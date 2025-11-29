"""
Document processing pipeline for AI-powered metadata extraction.

Orchestrates the complete document processing workflow following the 5-step
specification: Correspondent → Type → Tags → Date → Title.
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.config import get_settings
from app.core.logging import get_logger
from app.services.ai.base import AIProviderError, BaseLLMProvider
from app.services.paperless import PaperlessAPIError, PaperlessClient

logger = get_logger(__name__)


class ProcessingError(Exception):
    """Exception raised for processing pipeline errors."""

    def __init__(self, message: str, document_id: Optional[int] = None, original_error: Optional[Exception] = None):
        self.message = message
        self.document_id = document_id
        self.original_error = original_error
        super().__init__(self.message)


class DocumentProcessor:
    """
    Document processing pipeline for AI-powered metadata extraction.

    Coordinates document fetching, AI analysis, and metadata updates
    following the specification's processing order:
    1. Correspondent Identification
    2. Document Type Classification
    3. Tagging
    4. Date Extraction
    5. Renaming (Title Generation)

    Example:
        >>> processor = DocumentProcessor(ai_provider, paperless_client)
        >>> result = await processor.process_document(
        ...     document_id=123,
        ...     user_id=user_uuid,
        ...     approval_mode=False
        ... )
        >>> print(result["suggested_data"])
    """

    def __init__(
        self,
        ai_provider: BaseLLMProvider,
        paperless_client: PaperlessClient,
    ):
        """
        Initialize processing pipeline.

        Args:
            ai_provider: AI/LLM provider instance
            paperless_client: Paperless API client
        """
        self.ai_provider = ai_provider
        self.paperless_client = paperless_client
        self.settings = get_settings()

    async def process_document(
        self,
        document_id: int,
        user_id: UUID,
        approval_mode: Optional[bool] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Process a single document through the complete pipeline.

        Args:
            document_id: Paperless document ID
            user_id: User UUID
            approval_mode: Override approval workflow setting (None = use config)
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            Processing results with:
                - success: bool
                - document_id: int
                - original_data: dict (original metadata)
                - suggested_data: dict (AI suggestions)
                - confidence_score: float (overall confidence)
                - processing_time_ms: int
                - steps: dict (individual step results)
                - error: str (if failed)

        Raises:
            ProcessingError: If processing fails after all retries
        """
        start_time = datetime.utcnow()
        logger.info(f"Processing document {document_id} for user {user_id}")

        # Use config approval mode if not overridden
        if approval_mode is None:
            approval_mode = self.settings.approval_workflow.enabled

        # Retry logic with exponential backoff
        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                result = await self._process_document_internal(
                    document_id=document_id,
                    user_id=user_id,
                    approval_mode=approval_mode,
                    start_time=start_time,
                )
                return result

            except AIProviderError as e:
                last_error = e
                logger.warning(
                    f"AI error processing document {document_id} "
                    f"(attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    backoff_seconds = 2 ** attempt
                    logger.info(f"Retrying in {backoff_seconds} seconds...")
                    await asyncio.sleep(backoff_seconds)

            except PaperlessAPIError as e:
                # Don't retry paperless errors (likely auth or not found)
                logger.error(f"Paperless API error processing document {document_id}: {e}")
                raise ProcessingError(
                    f"Paperless API error: {e.message}",
                    document_id=document_id,
                    original_error=e,
                )

            except Exception as e:
                last_error = e
                logger.error(
                    f"Unexpected error processing document {document_id} "
                    f"(attempt {attempt + 1}/{max_retries}): {e}",
                    exc_info=True,
                )
                if attempt < max_retries - 1:
                    backoff_seconds = 2 ** attempt
                    await asyncio.sleep(backoff_seconds)

        # All retries failed
        elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        error_msg = f"Failed after {max_retries} attempts: {last_error}"
        logger.error(f"Processing failed for document {document_id}: {error_msg}")

        raise ProcessingError(error_msg, document_id=document_id, original_error=last_error)

    async def _process_document_internal(
        self,
        document_id: int,
        user_id: UUID,
        approval_mode: bool,
        start_time: datetime,
    ) -> Dict[str, Any]:
        """Internal processing implementation."""

        # Step 0: Fetch document from Paperless
        logger.debug(f"Fetching document {document_id} from Paperless")
        document = await self.paperless_client.get_document(document_id)

        # Extract OCR content
        ocr_content = document.get("content", "").strip()
        if not ocr_content:
            raise ProcessingError(
                f"Document {document_id} has no OCR content",
                document_id=document_id,
            )

        # Store original metadata
        original_data = {
            "title": document.get("title"),
            "correspondent": document.get("correspondent"),
            "document_type": document.get("document_type"),
            "tags": document.get("tags", []),
            "created": document.get("created"),
        }

        # Fetch available entities for AI context
        logger.debug("Fetching available entities from Paperless")
        correspondents = await self.paperless_client.get_correspondents()
        document_types = await self.paperless_client.get_document_types()
        tags = await self.paperless_client.get_tags()

        # Track individual step results
        steps_results = {}

        # Step 1: Correspondent Identification
        logger.info(f"Step 1/5: Identifying correspondent for document {document_id}")
        correspondent_result = await self._identify_correspondent(
            content=ocr_content,
            existing_correspondents=correspondents,
        )
        steps_results["correspondent"] = correspondent_result

        # Step 2: Document Type Classification
        logger.info(f"Step 2/5: Classifying document type for document {document_id}")
        type_result = await self._classify_document_type(
            content=ocr_content,
            existing_types=document_types,
        )
        steps_results["document_type"] = type_result

        # Step 3: Tagging
        logger.info(f"Step 3/5: Suggesting tags for document {document_id}")
        tag_result = await self._suggest_tags(
            content=ocr_content,
            document_type=type_result.get("document_type"),
            existing_tags=tags,
        )
        steps_results["tags"] = tag_result

        # Step 4: Date Extraction
        logger.info(f"Step 4/5: Extracting date from document {document_id}")
        date_result = await self._extract_date(content=ocr_content)
        steps_results["date"] = date_result

        # Step 5: Title Generation
        logger.info(f"Step 5/5: Generating title for document {document_id}")
        title_result = await self._generate_title(
            content=ocr_content,
            document_type=type_result.get("document_type"),
            correspondent=correspondent_result.get("correspondent"),
        )
        steps_results["title"] = title_result

        # Calculate overall confidence score (average of all steps)
        confidences = [
            correspondent_result.get("confidence", 0),
            type_result.get("confidence", 0),
            tag_result.get("confidence", 0),
            date_result.get("confidence", 0),
            title_result.get("confidence", 0),
        ]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Build suggested metadata
        suggested_data = {
            "correspondent": correspondent_result.get("correspondent"),
            "correspondent_id": correspondent_result.get("correspondent_id"),
            "document_type": type_result.get("document_type"),
            "document_type_id": type_result.get("document_type_id"),
            "tags": tag_result.get("tags", []),
            "tag_ids": tag_result.get("tag_ids", []),
            "document_date": date_result.get("document_date"),
            "title": title_result.get("title"),
        }

        # Apply naming template to generate final filename
        template_vars = {
            "date": date_result.get("document_date", ""),
            "type": type_result.get("document_type", ""),
            "correspondent": correspondent_result.get("correspondent", ""),
            "title": title_result.get("title", ""),
            "original": document.get("original_file_name", ""),
        }
        suggested_data["filename"] = self._apply_naming_template(
            template=self.settings.naming.default_template,
            variables=template_vars,
        )

        # Calculate processing time
        elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        logger.info(
            f"Successfully processed document {document_id} in {elapsed_ms}ms "
            f"(confidence: {overall_confidence:.2f})"
        )

        return {
            "success": True,
            "document_id": document_id,
            "original_data": original_data,
            "suggested_data": suggested_data,
            "confidence_score": overall_confidence,
            "processing_time_ms": elapsed_ms,
            "steps": steps_results,
            "approval_mode": approval_mode,
        }

    async def _identify_correspondent(
        self,
        content: str,
        existing_correspondents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Identify document correspondent using AI.

        Args:
            content: OCR text content
            existing_correspondents: List of existing correspondents from Paperless

        Returns:
            {
                "correspondent": str,
                "correspondent_id": int or None,
                "confidence": float,
                "is_new": bool
            }
        """
        logger.debug("Identifying correspondent with AI")

        # Build list of available correspondents
        correspondent_names = [c.get("name") for c in existing_correspondents if c.get("name")]

        # Construct AI prompt
        system_prompt = self.settings.prompts.system

        user_prompt = f"""Analyze this document and identify the correspondent (sender or recipient).

Available Correspondents:
{json.dumps(correspondent_names, indent=2) if correspondent_names else "None"}

Document Content (first 3000 chars):
{content[:3000]}

Return a JSON object with:
- correspondent: The identified correspondent name (choose from available list if match found, or suggest new name)
- confidence: Confidence score 0.0-1.0
- reasoning: Brief explanation of why this correspondent was chosen

IMPORTANT:
- If the document matches an existing correspondent, use that exact name
- If no match, suggest a new correspondent name based on the document
- Use the sender/recipient information from letterheads, invoices, bills, etc.
"""

        try:
            response_data = await self.ai_provider.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for more consistent results
            )

            correspondent_name = response_data.get("correspondent", "Unknown")
            confidence = float(response_data.get("confidence", 0.0))

            # Try to find matching correspondent ID
            correspondent_id = None
            is_new = True
            for c in existing_correspondents:
                if c.get("name", "").lower() == correspondent_name.lower():
                    correspondent_id = c.get("id")
                    correspondent_name = c.get("name")  # Use exact name from Paperless
                    is_new = False
                    break

            logger.debug(
                f"Identified correspondent: {correspondent_name} "
                f"(confidence: {confidence:.2f}, new: {is_new})"
            )

            return {
                "correspondent": correspondent_name,
                "correspondent_id": correspondent_id,
                "confidence": confidence,
                "is_new": is_new,
                "reasoning": response_data.get("reasoning", ""),
            }

        except Exception as e:
            logger.warning(f"Failed to identify correspondent: {e}")
            return {
                "correspondent": None,
                "correspondent_id": None,
                "confidence": 0.0,
                "is_new": False,
                "error": str(e),
            }

    async def _classify_document_type(
        self,
        content: str,
        existing_types: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Classify document type using AI.

        Args:
            content: OCR text content
            existing_types: List of existing document types from Paperless

        Returns:
            {
                "document_type": str,
                "document_type_id": int or None,
                "confidence": float,
                "is_new": bool
            }
        """
        logger.debug("Classifying document type with AI")

        # Build list of available types
        type_names = [t.get("name") for t in existing_types if t.get("name")]

        # Construct AI prompt
        system_prompt = self.settings.prompts.system

        user_prompt = f"""Analyze this document and classify its type.

Available Document Types:
{json.dumps(type_names, indent=2) if type_names else "None"}

Document Content (first 3000 chars):
{content[:3000]}

Return a JSON object with:
- document_type: The classified type (choose from available list if match found, or suggest new type)
- confidence: Confidence score 0.0-1.0
- reasoning: Brief explanation of the classification

Common document types include: Invoice, Receipt, Bill, Letter, Contract, Statement, Report, Form, etc.

IMPORTANT:
- If the document matches an existing type, use that exact name
- If no match, suggest an appropriate new type name
- Be specific but not too granular (e.g., "Invoice" not "Electric Company Invoice")
"""

        try:
            response_data = await self.ai_provider.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
            )

            type_name = response_data.get("document_type", "Document")
            confidence = float(response_data.get("confidence", 0.0))

            # Try to find matching document type ID
            document_type_id = None
            is_new = True
            for t in existing_types:
                if t.get("name", "").lower() == type_name.lower():
                    document_type_id = t.get("id")
                    type_name = t.get("name")  # Use exact name from Paperless
                    is_new = False
                    break

            logger.debug(
                f"Classified document type: {type_name} "
                f"(confidence: {confidence:.2f}, new: {is_new})"
            )

            return {
                "document_type": type_name,
                "document_type_id": document_type_id,
                "confidence": confidence,
                "is_new": is_new,
                "reasoning": response_data.get("reasoning", ""),
            }

        except Exception as e:
            logger.warning(f"Failed to classify document type: {e}")
            return {
                "document_type": None,
                "document_type_id": None,
                "confidence": 0.0,
                "is_new": False,
                "error": str(e),
            }

    async def _suggest_tags(
        self,
        content: str,
        document_type: Optional[str],
        existing_tags: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Suggest document tags using AI.

        Args:
            content: OCR text content
            document_type: Document type for context
            existing_tags: List of existing tags from Paperless

        Returns:
            {
                "tags": List[str],
                "tag_ids": List[int],
                "confidence": float,
                "new_tags": List[str]
            }
        """
        logger.debug("Suggesting tags with AI")

        # Get tag rules from config
        tag_rules = self.settings.tagging.rules

        # Build list of available tags (excluding excluded ones)
        excluded_tags = tag_rules.excluded_tags
        available_tags = [
            t.get("name") for t in existing_tags
            if t.get("name") and t.get("name") not in excluded_tags
        ]

        # Construct AI prompt
        system_prompt = self.settings.prompts.system

        user_prompt = f"""Analyze this document and suggest relevant tags.

Document Type: {document_type or "Unknown"}

Available Tags:
{json.dumps(available_tags, indent=2) if available_tags else "None"}

Tag Rules:
- Minimum tags: {tag_rules.min_tags}
- Maximum tags: {tag_rules.max_tags}
- Confidence threshold: {tag_rules.confidence_threshold}
- Excluded tags: {json.dumps(excluded_tags) if excluded_tags else "None"}

Document Content (first 3000 chars):
{content[:3000]}

Return a JSON object with:
- tags: Array of tag names (choose from available list or suggest new ones)
- confidences: Array of confidence scores (0.0-1.0) matching each tag
- reasoning: Brief explanation of tag selection

IMPORTANT:
- Suggest between {tag_rules.min_tags} and {tag_rules.max_tags} tags
- Prefer existing tags when applicable
- Only suggest tags with confidence >= {tag_rules.confidence_threshold}
- Tags should be descriptive and relevant to the document content
"""

        try:
            response_data = await self.ai_provider.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.5,
            )

            suggested_tags = response_data.get("tags", [])
            confidences = response_data.get("confidences", [])

            # Ensure we have confidence for each tag
            if len(confidences) < len(suggested_tags):
                confidences.extend([0.5] * (len(suggested_tags) - len(confidences)))

            # Filter by confidence threshold
            filtered_tags = []
            filtered_confidences = []
            for tag, conf in zip(suggested_tags, confidences):
                if conf >= tag_rules.confidence_threshold:
                    filtered_tags.append(tag)
                    filtered_confidences.append(conf)

            # Enforce min/max tags
            if len(filtered_tags) > tag_rules.max_tags:
                # Keep highest confidence tags
                sorted_pairs = sorted(
                    zip(filtered_tags, filtered_confidences),
                    key=lambda x: x[1],
                    reverse=True
                )
                filtered_tags = [t for t, _ in sorted_pairs[:tag_rules.max_tags]]
                filtered_confidences = [c for _, c in sorted_pairs[:tag_rules.max_tags]]

            # Match with existing tags and identify new ones
            matched_tag_ids = []
            matched_tag_names = []
            new_tags = []

            for tag_name in filtered_tags:
                matched = False
                for t in existing_tags:
                    if t.get("name", "").lower() == tag_name.lower():
                        matched_tag_ids.append(t.get("id"))
                        matched_tag_names.append(t.get("name"))
                        matched = True
                        break

                if not matched:
                    new_tags.append(tag_name)
                    matched_tag_names.append(tag_name)

            # Calculate average confidence
            avg_confidence = (
                sum(filtered_confidences) / len(filtered_confidences)
                if filtered_confidences else 0.0
            )

            logger.debug(
                f"Suggested {len(matched_tag_names)} tags "
                f"(confidence: {avg_confidence:.2f}, new: {len(new_tags)})"
            )

            return {
                "tags": matched_tag_names,
                "tag_ids": matched_tag_ids,
                "confidence": avg_confidence,
                "new_tags": new_tags,
                "reasoning": response_data.get("reasoning", ""),
            }

        except Exception as e:
            logger.warning(f"Failed to suggest tags: {e}")
            return {
                "tags": [],
                "tag_ids": [],
                "confidence": 0.0,
                "new_tags": [],
                "error": str(e),
            }

    async def _extract_date(
        self,
        content: str,
    ) -> Dict[str, Any]:
        """
        Extract most relevant date from document using AI.

        Args:
            content: OCR text content

        Returns:
            {
                "document_date": str (YYYY-MM-DD),
                "confidence": float,
                "date_type": str (e.g., "invoice_date", "letter_date")
            }
        """
        logger.debug("Extracting document date with AI")

        # Construct AI prompt
        system_prompt = self.settings.prompts.system

        user_prompt = f"""Analyze this document and extract the most relevant date.

Document Content (first 3000 chars):
{content[:3000]}

Date Priority:
1. Invoice date / Bill date (for invoices/bills)
2. Letter date / Document date (for correspondence)
3. Event date / Transaction date
4. Creation date (last resort)

Return a JSON object with:
- document_date: The date in YYYY-MM-DD format
- confidence: Confidence score 0.0-1.0
- date_type: Type of date (e.g., "invoice_date", "letter_date", "event_date")
- reasoning: Brief explanation of which date was chosen and why

IMPORTANT:
- Return date in YYYY-MM-DD format
- Choose the most semantically relevant date for this document type
- If multiple dates exist, prioritize based on the hierarchy above
"""

        try:
            response_data = await self.ai_provider.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.2,  # Very low temperature for date extraction
            )

            document_date = response_data.get("document_date")
            confidence = float(response_data.get("confidence", 0.0))
            date_type = response_data.get("date_type", "unknown")

            # Validate date format
            if document_date:
                try:
                    datetime.strptime(document_date, "%Y-%m-%d")
                except ValueError:
                    logger.warning(f"Invalid date format: {document_date}")
                    document_date = None
                    confidence = 0.0

            logger.debug(
                f"Extracted date: {document_date} "
                f"(confidence: {confidence:.2f}, type: {date_type})"
            )

            return {
                "document_date": document_date,
                "confidence": confidence,
                "date_type": date_type,
                "reasoning": response_data.get("reasoning", ""),
            }

        except Exception as e:
            logger.warning(f"Failed to extract date: {e}")
            return {
                "document_date": None,
                "confidence": 0.0,
                "date_type": "unknown",
                "error": str(e),
            }

    async def _generate_title(
        self,
        content: str,
        document_type: Optional[str] = None,
        correspondent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate descriptive title for document using AI.

        Args:
            content: OCR text content
            document_type: Document type for context
            correspondent: Correspondent for context

        Returns:
            {
                "title": str,
                "confidence": float
            }
        """
        logger.debug("Generating document title with AI")

        # Get max title length from config
        max_length = self.settings.naming.max_title_length

        # Construct AI prompt
        system_prompt = self.settings.prompts.system

        context_info = []
        if document_type:
            context_info.append(f"Document Type: {document_type}")
        if correspondent:
            context_info.append(f"Correspondent: {correspondent}")

        user_prompt = f"""Analyze this document and generate a concise, descriptive title.

{chr(10).join(context_info) if context_info else ""}

Document Content (first 3000 chars):
{content[:3000]}

Return a JSON object with:
- title: A concise, descriptive title (maximum {max_length} characters)
- confidence: Confidence score 0.0-1.0
- reasoning: Brief explanation of the title choice

Title Guidelines:
- Maximum {max_length} characters
- Be specific and descriptive
- Include key information (e.g., subject, purpose, period)
- Avoid generic titles like "Document" or "Letter"
- Do not include file extensions or special characters
- Examples: "Monthly Electric Bill January 2024", "Employment Contract - John Doe", "Tax Return 2023"

IMPORTANT: The title should be clear enough that someone can identify the document at a glance.
"""

        try:
            response_data = await self.ai_provider.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.5,
            )

            title = response_data.get("title", "Document")
            confidence = float(response_data.get("confidence", 0.0))

            # Enforce max length
            if len(title) > max_length:
                title = title[:max_length - 3] + "..."

            # Clean special characters if configured
            if self.settings.naming.clean_special_chars:
                title = self._clean_filename(title)

            logger.debug(f"Generated title: {title} (confidence: {confidence:.2f})")

            return {
                "title": title,
                "confidence": confidence,
                "reasoning": response_data.get("reasoning", ""),
            }

        except Exception as e:
            logger.warning(f"Failed to generate title: {e}")
            return {
                "title": "Document",
                "confidence": 0.0,
                "error": str(e),
            }

    def _apply_naming_template(
        self,
        template: str,
        variables: Dict[str, Any],
    ) -> str:
        """
        Apply naming template with extracted variables.

        Args:
            template: Naming template string (e.g., "{date}_{correspondent}_{type}_{title}")
            variables: Extracted variables (date, type, correspondent, title, original)

        Returns:
            Generated filename

        Example:
            >>> _apply_naming_template(
            ...     "{date}_{correspondent}_{title}",
            ...     {"date": "2024-01-15", "correspondent": "ACME Corp", "title": "Invoice"}
            ... )
            "2024-01-15_ACME_Corp_Invoice"
        """
        logger.debug(f"Applying naming template: {template}")

        # Clean and prepare variables
        cleaned_vars = {}
        for key, value in variables.items():
            if value:
                # Convert to string and clean
                str_value = str(value)
                if self.settings.naming.clean_special_chars:
                    str_value = self._clean_filename(str_value)
                cleaned_vars[key] = str_value
            else:
                cleaned_vars[key] = ""

        # Replace template variables
        result = template
        for key, value in cleaned_vars.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, value)

        # Clean up any remaining placeholders or multiple underscores
        result = re.sub(r"\{[^}]*\}", "", result)  # Remove unused placeholders
        result = re.sub(r"_+", "_", result)  # Replace multiple underscores
        result = result.strip("_")  # Remove leading/trailing underscores

        # Final cleanup
        if self.settings.naming.clean_special_chars:
            result = self._clean_filename(result)

        logger.debug(f"Generated filename: {result}")
        return result or "document"

    def _clean_filename(self, filename: str) -> str:
        """
        Clean filename for filesystem compatibility.

        Args:
            filename: Original filename

        Returns:
            Cleaned filename safe for filesystems

        Example:
            >>> _clean_filename("My File: Test / 2024")
            "My_File_Test_2024"
        """
        # Replace problematic characters with underscores
        cleaned = re.sub(r'[<>:"/\\|?*]', "_", filename)

        # Replace multiple spaces/underscores with single underscore
        cleaned = re.sub(r"[\s_]+", "_", cleaned)

        # Remove leading/trailing underscores and spaces
        cleaned = cleaned.strip("_ ")

        return cleaned

    def _calculate_confidence_score(self, ai_response: Dict[str, Any]) -> float:
        """
        Calculate confidence score from AI response.

        Args:
            ai_response: AI response dictionary

        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = ai_response.get("confidence", 0.0)

        try:
            confidence = float(confidence)
            # Clamp to valid range
            confidence = max(0.0, min(1.0, confidence))
        except (TypeError, ValueError):
            logger.warning(f"Invalid confidence value: {confidence}, using 0.0")
            confidence = 0.0

        return confidence
