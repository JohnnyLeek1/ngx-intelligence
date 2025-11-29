"""
Enhanced document processor with per-user Paperless client support.

This module extends the queue manager to support per-user Paperless credentials.
"""

from typing import Dict, Optional
from uuid import UUID

from app.core.logging import get_logger
from app.database.models import ApprovalStatus, ProcessingStatus
from app.database.session import sessionmanager
from app.repositories.approval import ApprovalRepository
from app.repositories.document import DocumentRepository
from app.repositories.queue import QueueRepository
from app.repositories.user import UserRepository
from app.services.paperless import PaperlessClient
from app.services.processing.pipeline import DocumentProcessor, ProcessingError

logger = get_logger(__name__)


async def process_single_document(
    queue_item,
    processor: DocumentProcessor,
    session,
) -> Dict:
    """
    Process a single document with per-user Paperless client.

    This function fetches the user's Paperless credentials, creates a client,
    processes the document through the AI pipeline, and applies the results.

    Args:
        queue_item: ProcessingQueue item
        processor: DocumentProcessor instance
        session: Database session

    Returns:
        Processing result dictionary
    """
    user_repo = UserRepository(session)
    doc_repo = DocumentRepository(session)
    approval_repo = ApprovalRepository(session)

    # Fetch user to get Paperless credentials
    user = await user_repo.get_by_id(queue_item.user_id)
    if not user:
        logger.error(f"User {queue_item.user_id} not found for queue item {queue_item.id}")
        return {
            "success": False,
            "error": f"User {queue_item.user_id} not found",
            "document_id": queue_item.paperless_document_id,
        }

    # Create per-user Paperless client
    paperless_client = PaperlessClient(
        base_url=user.paperless_url,
        auth_token=user.paperless_token,
    )

    # Temporarily set the paperless client on the processor
    original_client = processor.paperless_client
    processor.paperless_client = paperless_client

    try:
        # Process through pipeline
        result = await processor.process_document(
            document_id=queue_item.paperless_document_id,
            user_id=queue_item.user_id,
            max_retries=3,  # We can get this from config if needed
        )

        # Determine status based on approval mode
        from app.config import get_settings
        settings = get_settings()

        approval_mode = result.get("approval_mode")
        if approval_mode is None:
            approval_mode = settings.approval_workflow.enabled

        if approval_mode:
            status = ProcessingStatus.PENDING_APPROVAL
        else:
            status = ProcessingStatus.SUCCESS

        # Save to processed_documents table
        await doc_repo.mark_as_processed(
            paperless_id=queue_item.paperless_document_id,
            user_id=queue_item.user_id,
            status=status,
            suggested_data=result["suggested_data"],
            confidence_score=result["confidence_score"],
            processing_time_ms=result["processing_time_ms"],
        )

        # If approval mode, add to approval queue
        if approval_mode:
            logger.info(
                f"Approval mode enabled - adding document {queue_item.paperless_document_id} "
                "to approval queue"
            )

            # Get the processed document to link approval
            processed_doc = await doc_repo.get_by_paperless_id(
                queue_item.paperless_document_id,
                queue_item.user_id,
            )

            if processed_doc:
                # Create approval queue entry
                from app.database.models import ApprovalQueue
                approval_item = ApprovalQueue(
                    document_id=processed_doc.id,
                    user_id=queue_item.user_id,
                    suggestions=result["suggested_data"],
                    status=ApprovalStatus.PENDING,
                )
                session.add(approval_item)

                # Apply approval-pending tag in paperless
                try:
                    pending_tag = settings.approval_workflow.pending_tag
                    # Get existing tags
                    doc_data = await paperless_client.get_document(
                        queue_item.paperless_document_id
                    )
                    existing_tags = doc_data.get("tags", [])

                    # Find or create approval-pending tag
                    all_tags = await paperless_client.get_tags()
                    pending_tag_id = None
                    for tag in all_tags:
                        if tag.get("name") == pending_tag:
                            pending_tag_id = tag.get("id")
                            break

                    # Create tag if it doesn't exist
                    if pending_tag_id is None:
                        logger.info(f"Creating approval-pending tag '{pending_tag}'")
                        created_tag = await paperless_client.create_tag(
                            name=pending_tag,
                            color="#ff9800",  # Orange for pending
                        )
                        pending_tag_id = created_tag.get("id")

                    if pending_tag_id and pending_tag_id not in existing_tags:
                        existing_tags.append(pending_tag_id)
                        await paperless_client.update_document(
                            queue_item.paperless_document_id,
                            {"tags": existing_tags}
                        )
                        logger.info(
                            f"Applied approval-pending tag to document "
                            f"{queue_item.paperless_document_id}"
                        )

                except Exception as e:
                    logger.warning(
                        f"Failed to apply approval-pending tag: {e}",
                        exc_info=True
                    )

        else:
            # Directly apply changes to paperless
            logger.info(
                f"Applying AI suggestions directly to document "
                f"{queue_item.paperless_document_id}"
            )
            await apply_suggestions_to_paperless(
                paperless_client=paperless_client,
                document_id=queue_item.paperless_document_id,
                suggestions=result["suggested_data"],
            )

        logger.info(
            f"Successfully processed document {queue_item.paperless_document_id} "
            f"(confidence: {result['confidence_score']:.2f})"
        )

        return {"success": True, **result}

    except ProcessingError as e:
        logger.error(
            f"Processing error for document {queue_item.paperless_document_id}: {e.message}"
        )
        return {
            "success": False,
            "error": e.message,
            "document_id": queue_item.paperless_document_id,
        }

    except Exception as e:
        logger.error(
            f"Unexpected error processing document {queue_item.paperless_document_id}: {e}",
            exc_info=True,
        )
        return {
            "success": False,
            "error": str(e),
            "document_id": queue_item.paperless_document_id,
        }

    finally:
        # Restore original client and close per-user client
        processor.paperless_client = original_client
        await paperless_client.close()


async def apply_suggestions_to_paperless(
    paperless_client: PaperlessClient,
    document_id: int,
    suggestions: Dict,
) -> None:
    """
    Apply AI suggestions directly to Paperless document.

    Handles creation of new correspondents, document types, and tags if they
    don't exist (based on configuration).

    Args:
        paperless_client: Paperless API client
        document_id: Paperless document ID
        suggestions: Suggested metadata from AI processing
    """
    from app.config import get_settings
    settings = get_settings()

    try:
        update_data = {}

        # Apply title
        if suggestions.get("title"):
            update_data["title"] = suggestions["title"]

        # Apply correspondent (create if needed and allowed)
        if suggestions.get("correspondent_id"):
            update_data["correspondent"] = suggestions["correspondent_id"]
        elif suggestions.get("correspondent") and settings.auto_creation.correspondents:
            # Need to create new correspondent
            logger.info(f"Creating new correspondent: {suggestions['correspondent']}")
            try:
                correspondent_data = await paperless_client.create_correspondent(
                    name=suggestions["correspondent"]
                )
                update_data["correspondent"] = correspondent_data.get("id")
                logger.info(
                    f"Created correspondent '{suggestions['correspondent']}' "
                    f"(ID: {correspondent_data.get('id')})"
                )
            except Exception as e:
                logger.warning(f"Failed to create correspondent: {e}")

        # Apply document type (create if needed and allowed)
        if suggestions.get("document_type_id"):
            update_data["document_type"] = suggestions["document_type_id"]
        elif suggestions.get("document_type") and settings.auto_creation.document_types:
            # Need to create new document type
            logger.info(f"Creating new document type: {suggestions['document_type']}")
            try:
                doc_type_data = await paperless_client.create_document_type(
                    name=suggestions["document_type"]
                )
                update_data["document_type"] = doc_type_data.get("id")
                logger.info(
                    f"Created document type '{suggestions['document_type']}' "
                    f"(ID: {doc_type_data.get('id')})"
                )
            except Exception as e:
                logger.warning(f"Failed to create document type: {e}")

        # Apply tags (create if needed and allowed)
        tag_ids = suggestions.get("tag_ids", [])
        new_tags = suggestions.get("tags", [])

        # Create any new tags if auto-creation is enabled
        if new_tags and settings.auto_creation.tags:
            for tag_name in new_tags:
                # Skip if we already have the ID
                if tag_name in [t for t in suggestions.get("tags", []) if isinstance(t, str)]:
                    # Check if this tag needs to be created
                    all_tags = await paperless_client.get_tags()
                    existing = next((t for t in all_tags if t.get("name") == tag_name), None)

                    if not existing:
                        logger.info(f"Creating new tag: {tag_name}")
                        try:
                            tag_data = await paperless_client.create_tag(name=tag_name)
                            tag_ids.append(tag_data.get("id"))
                            logger.info(f"Created tag '{tag_name}' (ID: {tag_data.get('id')})")
                        except Exception as e:
                            logger.warning(f"Failed to create tag '{tag_name}': {e}")
                    else:
                        tag_ids.append(existing.get("id"))

        if tag_ids:
            # Get existing tags on document to merge
            doc_data = await paperless_client.get_document(document_id)
            existing_tag_ids = doc_data.get("tags", [])

            # Merge with existing tags (avoid duplicates)
            merged_tags = list(set(existing_tag_ids + tag_ids))
            update_data["tags"] = merged_tags

        # Apply document date
        if suggestions.get("document_date"):
            update_data["created"] = suggestions["document_date"]

        # Apply processing tag if enabled
        if settings.tagging.processing_tag.enabled:
            processing_tag_name = settings.tagging.processing_tag.name

            # Find or create processing tag
            all_tags = await paperless_client.get_tags()
            processing_tag = next(
                (t for t in all_tags if t.get("name") == processing_tag_name),
                None
            )

            if not processing_tag:
                logger.info(f"Creating processing tag '{processing_tag_name}'")
                processing_tag = await paperless_client.create_tag(
                    name=processing_tag_name,
                    color="#4caf50",  # Green for processed
                )

            # Add to tags if not already present
            if "tags" in update_data:
                if processing_tag.get("id") not in update_data["tags"]:
                    update_data["tags"].append(processing_tag.get("id"))
            else:
                doc_data = await paperless_client.get_document(document_id)
                existing_tags = doc_data.get("tags", [])
                if processing_tag.get("id") not in existing_tags:
                    existing_tags.append(processing_tag.get("id"))
                    update_data["tags"] = existing_tags

        # Apply updates to Paperless
        if update_data:
            await paperless_client.update_document(document_id, update_data)
            logger.info(
                f"Applied {len(update_data)} metadata updates to document {document_id}: "
                f"{list(update_data.keys())}"
            )
        else:
            logger.debug(f"No updates to apply for document {document_id}")

    except Exception as e:
        logger.error(f"Failed to apply suggestions to Paperless: {e}", exc_info=True)
        raise
