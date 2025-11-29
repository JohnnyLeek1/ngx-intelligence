"""
Paperless-NGX API client for document management integration.

This service handles all interactions with the Paperless-NGX REST API.
"""

from typing import Any, Dict, List, Optional

import httpx

from app.core.logging import get_logger


logger = get_logger(__name__)


class PaperlessAPIError(Exception):
    """Base exception for Paperless API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class PaperlessAuthError(PaperlessAPIError):
    """Exception raised for authentication/authorization errors."""

    pass


class PaperlessNotFoundError(PaperlessAPIError):
    """Exception raised when a resource is not found."""

    pass


class PaperlessRateLimitError(PaperlessAPIError):
    """Exception raised when rate limit is exceeded."""

    pass


class PaperlessClient:
    """
    Client for interacting with Paperless-NGX API.

    Provides methods for fetching documents, updating metadata,
    and managing document types, tags, and correspondents.

    Example:
        async with PaperlessClient(base_url, token) as client:
            doc = await client.get_document(123)
            documents = await client.list_documents(page=1, page_size=50)
    """

    def __init__(self, base_url: str, auth_token: str, timeout: int = 30):
        """
        Initialize Paperless client.

        Args:
            base_url: Paperless-NGX base URL (e.g., http://localhost:8000)
            auth_token: Authentication token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Token {self.auth_token}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10,
                ),
            )
        return self._client

    async def __aenter__(self) -> "PaperlessClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle HTTP response and raise appropriate exceptions.

        Args:
            response: HTTP response object

        Returns:
            JSON response data

        Raises:
            PaperlessAuthError: On 401/403 status codes
            PaperlessNotFoundError: On 404 status code
            PaperlessRateLimitError: On 429 status code
            PaperlessAPIError: On other error status codes
        """
        if response.status_code == 401:
            logger.error("Authentication failed - invalid token")
            raise PaperlessAuthError(
                "Authentication failed - invalid or expired token",
                status_code=401,
            )
        elif response.status_code == 403:
            logger.error("Authorization failed - insufficient permissions")
            raise PaperlessAuthError(
                "Authorization failed - insufficient permissions",
                status_code=403,
            )
        elif response.status_code == 404:
            logger.warning(f"Resource not found: {response.url}")
            raise PaperlessNotFoundError(
                f"Resource not found: {response.url}",
                status_code=404,
            )
        elif response.status_code == 429:
            logger.warning("Rate limit exceeded")
            raise PaperlessRateLimitError(
                "Rate limit exceeded - please retry later",
                status_code=429,
            )
        elif response.status_code >= 400:
            error_detail = response.text
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", error_data)
            except Exception:
                pass
            logger.error(
                f"API error {response.status_code}: {error_detail}"
            )
            raise PaperlessAPIError(
                f"API error: {error_detail}",
                status_code=response.status_code,
            )

        try:
            return response.json()
        except Exception as e:
            logger.error(f"Failed to parse response JSON: {e}")
            raise PaperlessAPIError(f"Invalid JSON response: {str(e)}")

    async def health_check(self) -> bool:
        """
        Check if Paperless API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            logger.debug("Performing health check on Paperless API")
            client = await self._get_client()
            response = await client.get("/api/", follow_redirects=True)
            # Accept 200 (OK) or 3xx (redirect) as healthy
            is_healthy = response.status_code in (200, 301, 302)
            logger.debug(f"Health check result: {is_healthy} (status: {response.status_code})")
            return is_healthy
        except httpx.TimeoutException as e:
            logger.error(f"Paperless health check timed out: {e}")
            return False
        except httpx.NetworkError as e:
            logger.error(f"Paperless health check network error: {e}")
            return False
        except Exception as e:
            logger.error(f"Paperless health check failed: {e}")
            return False

    async def validate_credentials(
        self,
        username: Optional[str] = None,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate authentication credentials.

        Args:
            username: Optional username to validate (for display purposes)
            token: Optional token to validate (overrides instance token)

        Returns:
            API root information if valid

        Raises:
            PaperlessAuthError: If credentials are invalid
            PaperlessAPIError: On other API errors
        """
        try:
            logger.debug(f"Validating credentials for user: {username or 'current'}")
            client = await self._get_client()

            # Override token if provided
            headers = {}
            if token:
                headers["Authorization"] = f"Token {token}"

            # Use /api/ endpoint which requires authentication
            response = await client.get("/api/", headers=headers or None)

            if response.status_code == 200:
                data = response.json()
                logger.debug("Credentials validated successfully")
                return data
            elif response.status_code in (401, 403):
                raise PaperlessAuthError(
                    "Invalid credentials - authentication failed",
                    status_code=response.status_code,
                )
            else:
                raise PaperlessAPIError(
                    f"Unexpected status code: {response.status_code}",
                    status_code=response.status_code,
                )
        except PaperlessAuthError:
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Credential validation timed out: {e}")
            raise PaperlessAPIError(f"Connection timeout: {str(e)}")
        except httpx.NetworkError as e:
            logger.error(f"Credential validation network error: {e}")
            raise PaperlessAPIError(f"Network error: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"Credential validation HTTP error: {e}")
            raise PaperlessAPIError(f"HTTP error: {str(e)}")

    async def get_document(self, document_id: int) -> Dict[str, Any]:
        """
        Get document metadata and content.

        Args:
            document_id: Paperless document ID

        Returns:
            Document data including:
                - id: Document ID
                - title: Document title
                - content: OCR extracted text content
                - created: Creation timestamp
                - modified: Last modification timestamp
                - correspondent: Correspondent ID
                - document_type: Document type ID
                - tags: List of tag IDs
                - archive_serial_number: ASN if set
                - original_file_name: Original filename
                - archived_file_name: Archive filename

        Raises:
            PaperlessNotFoundError: If document not found
            PaperlessAPIError: On other API errors
        """
        try:
            logger.debug(f"Fetching document {document_id} from Paperless")
            client = await self._get_client()
            response = await client.get(f"/api/documents/{document_id}/")
            data = await self._handle_response(response)
            logger.debug(f"Successfully fetched document {document_id}")
            return data
        except (PaperlessNotFoundError, PaperlessAuthError, PaperlessRateLimitError):
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching document {document_id}: {e}")
            raise PaperlessAPIError(f"Request timeout: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching document {document_id}: {e}")
            raise PaperlessAPIError(f"HTTP error: {str(e)}")

    async def list_documents(
        self,
        page: int = 1,
        page_size: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get list of documents with pagination and filtering.

        Args:
            page: Page number (1-indexed)
            page_size: Number of results per page (max 100)
            filters: Optional filters:
                - ordering: Field to order by (prefix with - for desc)
                - correspondent__id: Filter by correspondent ID
                - document_type__id: Filter by document type ID
                - tags__id__in: Filter by tag IDs (comma-separated)
                - created__date__gt: Filter by creation date (YYYY-MM-DD)
                - title_content: Search in title and content

        Returns:
            Dictionary with:
                - count: Total number of documents
                - next: URL to next page (if any)
                - previous: URL to previous page (if any)
                - results: List of document objects

        Raises:
            PaperlessAPIError: On API errors
        """
        try:
            logger.debug(f"Listing documents - page {page}, size {page_size}")
            client = await self._get_client()

            # Build query parameters
            params: Dict[str, Any] = {
                "page": page,
                "page_size": min(page_size, 100),
            }

            if filters:
                params.update(filters)

            response = await client.get("/api/documents/", params=params)
            data = await self._handle_response(response)
            logger.debug(
                f"Successfully listed documents - total: {data.get('count', 0)}"
            )
            return data
        except (PaperlessAuthError, PaperlessRateLimitError):
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout listing documents: {e}")
            raise PaperlessAPIError(f"Request timeout: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error listing documents: {e}")
            raise PaperlessAPIError(f"HTTP error: {str(e)}")

    async def update_document(
        self,
        document_id: int,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update document metadata.

        Args:
            document_id: Paperless document ID
            data: Document metadata to update. Common fields:
                - title: Document title
                - correspondent: Correspondent ID
                - document_type: Document type ID
                - tags: List of tag IDs
                - archive_serial_number: ASN
                - created: Creation date (YYYY-MM-DD)

        Returns:
            Updated document data

        Raises:
            PaperlessNotFoundError: If document not found
            PaperlessAPIError: If update fails
        """
        try:
            logger.info(
                f"Updating document {document_id} with data: {list(data.keys())}"
            )
            client = await self._get_client()
            response = await client.patch(
                f"/api/documents/{document_id}/",
                json=data,
            )
            result = await self._handle_response(response)
            logger.info(f"Successfully updated document {document_id}")
            return result
        except (PaperlessNotFoundError, PaperlessAuthError, PaperlessRateLimitError):
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout updating document {document_id}: {e}")
            raise PaperlessAPIError(f"Request timeout: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error updating document {document_id}: {e}")
            raise PaperlessAPIError(f"HTTP error: {str(e)}")

    async def get_document_types(self) -> List[Dict[str, Any]]:
        """
        Get all document types.

        Returns:
            List of document types with fields:
                - id: Document type ID
                - name: Document type name
                - slug: URL-safe slug
                - match: Matching pattern
                - matching_algorithm: Algorithm (1=any, 2=all, 3=literal, 4=regex)
                - is_insensitive: Case insensitive matching
                - document_count: Number of documents with this type

        Raises:
            PaperlessAPIError: On API errors
        """
        try:
            logger.debug("Fetching document types from Paperless")
            client = await self._get_client()
            response = await client.get("/api/document_types/")
            data = await self._handle_response(response)
            # API returns paginated response, extract results
            results = data.get("results", [])
            logger.debug(f"Successfully fetched {len(results)} document types")
            return results
        except (PaperlessAuthError, PaperlessRateLimitError):
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching document types: {e}")
            raise PaperlessAPIError(f"Request timeout: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching document types: {e}")
            raise PaperlessAPIError(f"HTTP error: {str(e)}")

    async def create_document_type(
        self,
        name: str,
        match: str = "",
        matching_algorithm: int = 1,
    ) -> Dict[str, Any]:
        """
        Create a new document type.

        Args:
            name: Document type name
            match: Matching pattern (optional)
            matching_algorithm: Matching algorithm:
                - 1: Any word
                - 2: All words
                - 3: Exact match
                - 4: Regular expression
                - 5: Fuzzy match
                - 6: Auto (default)

        Returns:
            Created document type data

        Raises:
            PaperlessAPIError: If creation fails
        """
        try:
            logger.info(f"Creating document type '{name}' in Paperless")
            client = await self._get_client()
            payload = {
                "name": name,
                "match": match,
                "matching_algorithm": matching_algorithm,
                "is_insensitive": True,
            }
            response = await client.post("/api/document_types/", json=payload)
            data = await self._handle_response(response)
            logger.info(f"Successfully created document type '{name}' (ID: {data.get('id')})")
            return data
        except (PaperlessAuthError, PaperlessRateLimitError):
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout creating document type: {e}")
            raise PaperlessAPIError(f"Request timeout: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating document type: {e}")
            raise PaperlessAPIError(f"HTTP error: {str(e)}")

    async def get_tags(self) -> List[Dict[str, Any]]:
        """
        Get all tags.

        Returns:
            List of tags with fields:
                - id: Tag ID
                - name: Tag name
                - slug: URL-safe slug
                - color: Tag color (hex code)
                - match: Matching pattern
                - matching_algorithm: Algorithm (same as document types)
                - is_insensitive: Case insensitive matching
                - is_inbox_tag: Whether this is an inbox tag
                - document_count: Number of documents with this tag

        Raises:
            PaperlessAPIError: On API errors
        """
        try:
            logger.debug("Fetching tags from Paperless")
            client = await self._get_client()
            response = await client.get("/api/tags/")
            data = await self._handle_response(response)
            # API returns paginated response, extract results
            results = data.get("results", [])
            logger.debug(f"Successfully fetched {len(results)} tags")
            return results
        except (PaperlessAuthError, PaperlessRateLimitError):
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching tags: {e}")
            raise PaperlessAPIError(f"Request timeout: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching tags: {e}")
            raise PaperlessAPIError(f"HTTP error: {str(e)}")

    async def create_tag(
        self,
        name: str,
        color: str = "#a6cee3",
        is_inbox_tag: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new tag.

        Args:
            name: Tag name
            color: Tag color in hex format (default: light blue)
            is_inbox_tag: Whether this is an inbox tag

        Returns:
            Created tag data

        Raises:
            PaperlessAPIError: If creation fails
        """
        try:
            logger.info(f"Creating tag '{name}' in Paperless")
            client = await self._get_client()
            payload = {
                "name": name,
                "color": color,
                "is_inbox_tag": is_inbox_tag,
                "match": "",
                "matching_algorithm": 1,
                "is_insensitive": True,
            }
            response = await client.post("/api/tags/", json=payload)
            data = await self._handle_response(response)
            logger.info(f"Successfully created tag '{name}' (ID: {data.get('id')})")
            return data
        except (PaperlessAuthError, PaperlessRateLimitError):
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout creating tag: {e}")
            raise PaperlessAPIError(f"Request timeout: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating tag: {e}")
            raise PaperlessAPIError(f"HTTP error: {str(e)}")

    async def get_correspondents(self) -> List[Dict[str, Any]]:
        """
        Get all correspondents.

        Returns:
            List of correspondents with fields:
                - id: Correspondent ID
                - name: Correspondent name
                - slug: URL-safe slug
                - match: Matching pattern
                - matching_algorithm: Algorithm (same as document types)
                - is_insensitive: Case insensitive matching
                - document_count: Number of documents with this correspondent

        Raises:
            PaperlessAPIError: On API errors
        """
        try:
            logger.debug("Fetching correspondents from Paperless")
            client = await self._get_client()
            response = await client.get("/api/correspondents/")
            data = await self._handle_response(response)
            # API returns paginated response, extract results
            results = data.get("results", [])
            logger.debug(f"Successfully fetched {len(results)} correspondents")
            return results
        except (PaperlessAuthError, PaperlessRateLimitError):
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching correspondents: {e}")
            raise PaperlessAPIError(f"Request timeout: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching correspondents: {e}")
            raise PaperlessAPIError(f"HTTP error: {str(e)}")

    async def create_correspondent(
        self,
        name: str,
        match: str = "",
        matching_algorithm: int = 1,
    ) -> Dict[str, Any]:
        """
        Create a new correspondent.

        Args:
            name: Correspondent name
            match: Matching pattern (optional)
            matching_algorithm: Matching algorithm:
                - 1: Any word
                - 2: All words
                - 3: Exact match
                - 4: Regular expression
                - 5: Fuzzy match
                - 6: Auto (default)

        Returns:
            Created correspondent data

        Raises:
            PaperlessAPIError: If creation fails
        """
        try:
            logger.info(f"Creating correspondent '{name}' in Paperless")
            client = await self._get_client()
            payload = {
                "name": name,
                "match": match,
                "matching_algorithm": matching_algorithm,
                "is_insensitive": True,
            }
            response = await client.post("/api/correspondents/", json=payload)
            data = await self._handle_response(response)
            logger.info(
                f"Successfully created correspondent '{name}' (ID: {data.get('id')})"
            )
            return data
        except (PaperlessAuthError, PaperlessRateLimitError):
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout creating correspondent: {e}")
            raise PaperlessAPIError(f"Request timeout: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating correspondent: {e}")
            raise PaperlessAPIError(f"HTTP error: {str(e)}")


async def get_paperless_client(
    base_url: str,
    auth_token: str,
) -> PaperlessClient:
    """
    Get a Paperless client instance.

    Args:
        base_url: Paperless-NGX base URL
        auth_token: Authentication token

    Returns:
        PaperlessClient instance
    """
    return PaperlessClient(base_url, auth_token)
