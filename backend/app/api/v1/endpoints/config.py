"""
Configuration API endpoints (Admin only).

Handles configuration viewing and updates.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.session import get_db
from app.dependencies import get_current_admin_user
from app.services.config_service import ConfigService
from app.services.ai.ollama import OllamaProvider
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/config", tags=["Configuration"])


class ConfigUpdateRequest(BaseModel):
    """Request model for config updates."""
    section: str
    data: Dict[str, Any]


class AIModelInfo(BaseModel):
    """AI model information."""
    name: str
    size: str | None = None
    parameter_count: str | None = None
    quantization: str | None = None
    is_available: bool


class AIModelsResponse(BaseModel):
    """Response with available AI models."""
    models: List[AIModelInfo]
    current_model: str


@router.get("/")
async def get_configuration(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current configuration with database overrides (admin only)."""
    service = ConfigService(db)
    return await service.get_full_config()


@router.get("/{section}")
async def get_configuration_section(
    section: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get a specific configuration section (admin only)."""
    service = ConfigService(db)
    try:
        data = await service.get_section(section)
        return {"data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/")
async def update_configuration(
    request: ConfigUpdateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a configuration section (admin only)."""
    service = ConfigService(db)
    try:
        updated_data = await service.update_section(
            section=request.section,
            data=request.data,
            user_id=current_user.id
        )
        return {
            "message": f"Configuration section '{request.section}' updated successfully",
            "data": updated_data
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ai/models")
async def get_ai_models(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AIModelsResponse:
    """Get available AI models from Ollama (admin only)."""
    try:
        # Get current model from config
        service = ConfigService(db)
        ai_config = await service.get_section("ai")
        current_model = ai_config.get("model", "llama3.2:latest")

        # Get available models from Ollama
        ollama = OllamaProvider()
        models_list = await ollama.list_models()

        # Format models for response
        models = []
        for model_name in models_list:
            models.append(AIModelInfo(
                name=model_name,
                is_available=True
            ))

        # If current model not in list, add it as unavailable
        if current_model not in models_list:
            models.insert(0, AIModelInfo(
                name=current_model,
                is_available=False
            ))

        return AIModelsResponse(
            models=models,
            current_model=current_model
        )
    except Exception as e:
        logger.error(f"Failed to fetch AI models: {e}")
        # Return fallback response
        return AIModelsResponse(
            models=[
                AIModelInfo(name="llama3.2:latest", is_available=False),
                AIModelInfo(name="llama3.1:latest", is_available=False),
                AIModelInfo(name="mistral:latest", is_available=False),
            ],
            current_model=current_model
        )
