"""
Pydantic schemas for API request/response validation.
"""

from app.schemas.approval import (
    ApprovalActionRequest,
    ApprovalQueueResponse,
    ApprovalStatsResponse,
    ApprovalWithDocumentResponse,
    BatchApprovalRequest,
)
from app.schemas.common import (
    ErrorResponse,
    HealthCheckResponse,
    MessageResponse,
    PaginatedResponse,
    PaginationParams,
    UTCBaseModel,
)
from app.schemas.config import (
    AIModelResponse,
    AIModelsListResponse,
    AITestRequest,
    AITestResponse,
    ConfigResponse,
    ConfigUpdateRequest,
    ConfigValidationRequest,
    ConfigValidationResponse,
    PromptResponse,
    PromptUpdateRequest,
)
from app.schemas.metrics import (
    DailyMetricsComparisonResponse,
    DailyMetricsResponse,
    MetricsRangeRequest,
    MetricsRangeResponse,
)
from app.schemas.document import (
    DocumentFilterRequest,
    DocumentReprocessRequest,
    DocumentStatsResponse,
    ProcessedDocumentDetail,
    ProcessedDocumentResponse,
    ProcessingResult,
    RecentDocumentsResponse,
)
from app.schemas.queue import (
    QueueAddRequest,
    QueueClearRequest,
    QueueItemResponse,
    QueueStatsResponse,
    QueueStatusResponse,
)
from app.schemas.user import (
    LoginRequest,
    PaperlessCredentialsUpdate,
    PaperlessValidationRequest,
    PaperlessValidationResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserCreate,
    UserPasswordChange,
    UserResponse,
    UserUpdate,
    UserWithStats,
)

__all__ = [
    # Common
    "UTCBaseModel",
    "HealthCheckResponse",
    "MessageResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "PaginationParams",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserWithStats",
    "UserPasswordChange",
    "PaperlessCredentialsUpdate",
    "LoginRequest",
    "TokenResponse",
    "TokenRefreshRequest",
    "PaperlessValidationRequest",
    "PaperlessValidationResponse",
    # Document
    "ProcessedDocumentResponse",
    "ProcessedDocumentDetail",
    "DocumentStatsResponse",
    "DocumentFilterRequest",
    "DocumentReprocessRequest",
    "ProcessingResult",
    "RecentDocumentsResponse",
    # Queue
    "QueueItemResponse",
    "QueueStatsResponse",
    "QueueStatusResponse",
    "QueueAddRequest",
    "QueueClearRequest",
    # Approval
    "ApprovalQueueResponse",
    "ApprovalWithDocumentResponse",
    "ApprovalStatsResponse",
    "ApprovalActionRequest",
    "BatchApprovalRequest",
    # Config
    "ConfigResponse",
    "ConfigUpdateRequest",
    "ConfigValidationRequest",
    "ConfigValidationResponse",
    "AIModelResponse",
    "AIModelsListResponse",
    "AITestRequest",
    "AITestResponse",
    "PromptResponse",
    "PromptUpdateRequest",
    # Metrics
    "DailyMetricsResponse",
    "DailyMetricsComparisonResponse",
    "MetricsRangeRequest",
    "MetricsRangeResponse",
]
