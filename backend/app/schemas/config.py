"""
Pydantic schemas for Configuration-related API operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import UTCBaseModel


# Request schemas
class ConfigUpdateRequest(BaseModel):
    """Schema for configuration updates."""

    section: str = Field(..., description="Configuration section to update")
    data: Dict[str, Any] = Field(..., description="Configuration data")


class ConfigValidationRequest(BaseModel):
    """Schema for configuration validation."""

    config_data: Dict[str, Any]


# Response schemas
class ConfigSectionResponse(BaseModel):
    """Schema for configuration section response."""

    section: str
    data: Dict[str, Any]
    is_default: bool = False


class ConfigResponse(BaseModel):
    """Schema for full configuration response."""

    app: Dict[str, Any]
    database: Dict[str, Any]
    ai: Dict[str, Any]
    processing: Dict[str, Any]
    tagging: Dict[str, Any]
    naming: Dict[str, Any]
    learning: Dict[str, Any]
    approval_workflow: Dict[str, Any]
    auto_creation: Dict[str, Any]
    notifications: Dict[str, Any]


class ConfigValidationResponse(BaseModel):
    """Schema for configuration validation response."""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# AI-specific schemas
class AIModelResponse(BaseModel):
    """Schema for AI model information."""

    name: str
    size: Optional[str] = None
    parameter_count: Optional[str] = None
    quantization: Optional[str] = None
    is_available: bool = True


class AIModelsListResponse(BaseModel):
    """Schema for available AI models list."""

    models: List[AIModelResponse]
    current_model: str


class PromptUpdateRequest(BaseModel):
    """Schema for prompt updates."""

    prompt_type: str = Field(..., description="Type of prompt (system, classification, etc.)")
    content: str = Field(..., min_length=1, max_length=10000)


class PromptResponse(UTCBaseModel):
    """Schema for prompt response."""

    prompt_type: str
    content: str
    version: int
    created_at: datetime
    is_active: bool


class AITestRequest(BaseModel):
    """Schema for testing AI with sample document."""

    document_content: str = Field(..., min_length=1)
    test_types: List[str] = Field(
        default=["classification", "tagging", "correspondent"],
        description="Types of tests to run"
    )


class AITestResponse(BaseModel):
    """Schema for AI test results."""

    test_type: str
    result: Dict[str, Any]
    confidence: Optional[float]
    processing_time_ms: int
    success: bool
    error: Optional[str] = None
