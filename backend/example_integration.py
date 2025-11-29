#!/usr/bin/env python3
"""
Example: Complete Integration of Paperless Client with ngx-intelligence

This example demonstrates how the PaperlessClient integrates with:
- Configuration system
- Database models
- AI processing
- API endpoints
- Error handling
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from app.services.paperless import (
    PaperlessClient,
    PaperlessAPIError,
    PaperlessAuthError,
    PaperlessNotFoundError,
)
from app.config import get_settings
from app.core.logging import get_logger


logger = get_logger(__name__)


class DocumentProcessor:
    """
    Example service that processes documents from Paperless with AI.

    This demonstrates a complete workflow:
    1. Fetch documents from Paperless
    2. Process with AI (simulated)
    3. Update Paperless with suggestions
    4. Track processing in database (simulated)
    """

    def __init__(self, paperless_url: str, paperless_token: str):
        """Initialize processor with Paperless credentials."""
        self.paperless_url = paperless_url
        self.paperless_token = paperless_token
        self.settings = get_settings()

    async def process_inbox_documents(self) -> Dict[str, int]:
        """
        Process all documents in the Paperless inbox.

        Returns:
            Statistics: {processed, failed, skipped}
        """
        stats = {"processed": 0, "failed": 0, "skipped": 0}

        async with PaperlessClient(
            base_url=self.paperless_url,
            auth_token=self.paperless_token,
            timeout=self.settings.ai.ollama.timeout,
        ) as client:
            # Verify connectivity
            if not await client.health_check():
                logger.error("Paperless is not accessible")
                return stats

            # Get inbox tag
            tags = await client.get_tags()
            inbox_tag = next((t for t in tags if t.get("is_inbox_tag")), None)

            if not inbox_tag:
                logger.warning("No inbox tag found in Paperless")
                return stats

            logger.info(f"Processing documents with tag: {inbox_tag['name']}")

            # Fetch inbox documents
            result = await client.list_documents(
                page=1,
                page_size=100,
                filters={
                    "tags__id__in": str(inbox_tag["id"]),
                    "ordering": "-created",
                },
            )

            total_docs = len(result.get("results", []))
            logger.info(f"Found {total_docs} inbox documents to process")

            # Cache metadata to avoid repeated API calls
            metadata_cache = await self._build_metadata_cache(client)

            # Process each document
            for doc_summary in result.get("results", []):
                try:
                    await self._process_single_document(
                        client,
                        doc_summary["id"],
                        inbox_tag["id"],
                        metadata_cache,
                    )
                    stats["processed"] += 1

                except PaperlessNotFoundError:
                    logger.warning(
                        f"Document {doc_summary['id']} not found (deleted?)"
                    )
                    stats["skipped"] += 1

                except Exception as e:
                    logger.error(f"Error processing document {doc_summary['id']}: {e}")
                    stats["failed"] += 1

        logger.info(f"Processing complete: {stats}")
        return stats

    async def _build_metadata_cache(
        self, client: PaperlessClient
    ) -> Dict[str, Dict]:
        """Build lookup caches for types, tags, and correspondents."""
        logger.debug("Building metadata cache")

        doc_types = await client.get_document_types()
        tags = await client.get_tags()
        correspondents = await client.get_correspondents()

        return {
            "types": {dt["name"].lower(): dt for dt in doc_types},
            "tags": {t["name"].lower(): t for t in tags},
            "correspondents": {c["name"].lower(): c for c in correspondents},
        }

    async def _process_single_document(
        self,
        client: PaperlessClient,
        doc_id: int,
        inbox_tag_id: int,
        metadata_cache: Dict,
    ) -> None:
        """Process a single document with AI and update Paperless."""
        logger.info(f"Processing document {doc_id}")

        # Fetch full document with content
        doc = await client.get_document(doc_id)

        # Simulate AI processing
        ai_suggestions = await self._analyze_with_ai(doc)

        # Resolve or create entities
        updates = await self._prepare_updates(
            client,
            ai_suggestions,
            metadata_cache,
            doc["tags"],
            inbox_tag_id,
        )

        # Only update if we have suggestions
        if updates:
            await client.update_document(doc_id, updates)
            logger.info(
                f"Updated document {doc_id}: "
                f"type={updates.get('document_type')}, "
                f"correspondent={updates.get('correspondent')}, "
                f"tags={len(updates.get('tags', []))}"
            )
        else:
            logger.info(f"No updates needed for document {doc_id}")

    async def _analyze_with_ai(self, doc: Dict) -> Dict:
        """
        Analyze document with AI.

        In production, this would call the actual AI service.
        Here we simulate the analysis.
        """
        logger.debug(f"Analyzing document: {doc['title']}")

        # Simulate AI analysis delay
        await asyncio.sleep(0.1)

        # Simulate AI suggestions based on content
        content = doc.get("content", "").lower()

        suggestions = {
            "document_type": None,
            "correspondent": None,
            "tags": [],
            "title": None,
            "document_date": None,
        }

        # Simple heuristics (in production, this would be AI-generated)
        if "invoice" in content:
            suggestions["document_type"] = "Invoice"
            suggestions["tags"].append("financial")

        if "receipt" in content:
            suggestions["document_type"] = "Receipt"
            suggestions["tags"].append("expense")

        if "contract" in content:
            suggestions["document_type"] = "Contract"
            suggestions["tags"].append("legal")

        # Extract potential correspondent from content
        # (In production, use NER or similar)
        if "@" in content:
            suggestions["correspondent"] = "Email Correspondent"

        # Add urgency tag if needed
        if any(word in content for word in ["urgent", "asap", "immediate"]):
            suggestions["tags"].append("urgent")

        logger.debug(f"AI suggestions: {suggestions}")
        return suggestions

    async def _prepare_updates(
        self,
        client: PaperlessClient,
        suggestions: Dict,
        cache: Dict,
        current_tags: List[int],
        inbox_tag_id: int,
    ) -> Dict:
        """Prepare document updates, creating entities as needed."""
        updates = {}

        # Document Type
        if suggestions["document_type"]:
            type_name = suggestions["document_type"].lower()
            doc_type = cache["types"].get(type_name)

            if not doc_type:
                # Create new type
                logger.info(f"Creating new document type: {suggestions['document_type']}")
                doc_type = await client.create_document_type(
                    name=suggestions["document_type"]
                )
                cache["types"][type_name] = doc_type

            updates["document_type"] = doc_type["id"]

        # Correspondent
        if suggestions["correspondent"]:
            corr_name = suggestions["correspondent"].lower()
            correspondent = cache["correspondents"].get(corr_name)

            if not correspondent:
                # Create new correspondent
                logger.info(f"Creating new correspondent: {suggestions['correspondent']}")
                correspondent = await client.create_correspondent(
                    name=suggestions["correspondent"]
                )
                cache["correspondents"][corr_name] = correspondent

            updates["correspondent"] = correspondent["id"]

        # Tags
        tag_ids = set(current_tags)
        tag_ids.discard(inbox_tag_id)  # Remove inbox tag

        for tag_name in suggestions["tags"]:
            tag_name_lower = tag_name.lower()
            tag = cache["tags"].get(tag_name_lower)

            if not tag:
                # Create new tag with random color
                logger.info(f"Creating new tag: {tag_name}")
                tag = await client.create_tag(
                    name=tag_name,
                    color=self._get_tag_color(tag_name),
                )
                cache["tags"][tag_name_lower] = tag

            tag_ids.add(tag["id"])

        if tag_ids != set(current_tags):
            updates["tags"] = list(tag_ids)

        # Title (if AI generated better one)
        if suggestions["title"]:
            updates["title"] = suggestions["title"]

        # Document date
        if suggestions["document_date"]:
            updates["created"] = suggestions["document_date"]

        return updates

    def _get_tag_color(self, tag_name: str) -> str:
        """Get appropriate color for tag based on name."""
        color_map = {
            "urgent": "#ff0000",
            "important": "#ff9900",
            "financial": "#00cc00",
            "legal": "#0066cc",
            "expense": "#cc00cc",
            "tax": "#996600",
        }
        return color_map.get(tag_name.lower(), "#a6cee3")


class BatchDocumentFetcher:
    """
    Example service for batch-fetching documents with pagination.
    """

    def __init__(self, paperless_url: str, paperless_token: str):
        self.paperless_url = paperless_url
        self.paperless_token = paperless_token

    async def fetch_all_documents(
        self,
        filters: Optional[Dict] = None,
        batch_size: int = 100,
    ) -> List[Dict]:
        """
        Fetch all documents matching filters, handling pagination.

        Args:
            filters: Optional filters to apply
            batch_size: Number of documents per page

        Returns:
            List of all matching documents
        """
        all_documents = []

        async with PaperlessClient(
            self.paperless_url,
            self.paperless_token,
        ) as client:
            page = 1

            while True:
                logger.debug(f"Fetching page {page}")

                result = await client.list_documents(
                    page=page,
                    page_size=batch_size,
                    filters=filters,
                )

                documents = result.get("results", [])
                all_documents.extend(documents)

                logger.info(
                    f"Fetched page {page}: {len(documents)} docs "
                    f"(total: {len(all_documents)} / {result.get('count', 0)})"
                )

                # Check if there are more pages
                if not result.get("next"):
                    break

                page += 1

        return all_documents

    async def export_documents_by_type(
        self, document_type_name: str
    ) -> List[Dict]:
        """Export all documents of a specific type."""
        logger.info(f"Exporting documents of type: {document_type_name}")

        async with PaperlessClient(
            self.paperless_url,
            self.paperless_token,
        ) as client:
            # Find document type ID
            doc_types = await client.get_document_types()
            doc_type = next(
                (dt for dt in doc_types if dt["name"] == document_type_name),
                None,
            )

            if not doc_type:
                logger.warning(f"Document type not found: {document_type_name}")
                return []

            # Fetch all documents of this type
            return await self.fetch_all_documents(
                filters={"document_type__id": doc_type["id"]}
            )


async def example_usage():
    """Demonstrate various usage patterns."""
    # Configuration (in production, get from settings or user input)
    PAPERLESS_URL = "http://localhost:8000"
    PAPERLESS_TOKEN = "your-token-here"

    print("=" * 60)
    print("EXAMPLE 1: Process Inbox Documents")
    print("=" * 60)

    processor = DocumentProcessor(PAPERLESS_URL, PAPERLESS_TOKEN)

    try:
        stats = await processor.process_inbox_documents()
        print(f"\nResults:")
        print(f"  Processed: {stats['processed']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Skipped: {stats['skipped']}")
    except PaperlessAuthError:
        print("ERROR: Invalid Paperless credentials")
    except PaperlessAPIError as e:
        print(f"ERROR: Paperless API error: {e.message}")

    print("\n" + "=" * 60)
    print("EXAMPLE 2: Batch Export Documents")
    print("=" * 60)

    fetcher = BatchDocumentFetcher(PAPERLESS_URL, PAPERLESS_TOKEN)

    try:
        # Export all invoices
        invoices = await fetcher.export_documents_by_type("Invoice")
        print(f"\nExported {len(invoices)} invoices")

        # Fetch recent documents
        recent = await fetcher.fetch_all_documents(
            filters={"ordering": "-created"},
            batch_size=50,
        )
        print(f"Fetched {len(recent)} recent documents")
    except PaperlessAPIError as e:
        print(f"ERROR: {e.message}")

    print("\n" + "=" * 60)
    print("EXAMPLE 3: Simple Document Lookup")
    print("=" * 60)

    async with PaperlessClient(PAPERLESS_URL, PAPERLESS_TOKEN) as client:
        try:
            # Health check
            if await client.health_check():
                print("✓ Paperless is accessible")

            # Fetch a specific document
            doc = await client.get_document(123)
            print(f"\nDocument 123: {doc['title']}")

        except PaperlessNotFoundError:
            print("Document 123 not found")
        except PaperlessAuthError:
            print("Authentication failed")


if __name__ == "__main__":
    print("\nNOTE: Update PAPERLESS_URL and PAPERLESS_TOKEN before running\n")
    asyncio.run(example_usage())
