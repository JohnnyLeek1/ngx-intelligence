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
    modified_at: str | None = None
    is_available: bool


class AIModelsResponse(BaseModel):
    """Response with available AI models."""
    models: List[AIModelInfo]
    current_model: str


class OllamaTestRequest(BaseModel):
    """Request to test Ollama connectivity."""
    url: str


class OllamaTestResponse(BaseModel):
    """Response from Ollama connectivity test."""
    reachable: bool
    error: str | None = None
    models: List[str] | None = None


@router.get("")
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


@router.put("")
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


@router.post("/ai/test-connection")
async def test_ollama_connection(
    request: OllamaTestRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> OllamaTestResponse:
    """Test connectivity to an Ollama instance (admin only)."""
    service = ConfigService(db)
    result = await service.test_ollama_connection(request.url)

    return OllamaTestResponse(
        reachable=result["reachable"],
        error=result["error"],
        models=result["models"]
    )


@router.get("/ai/models")
async def get_ai_models(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AIModelsResponse:
    """
    Get available AI models from Ollama (admin only).

    Returns a list of installed models from the Ollama instance with their
    availability status and metadata. If Ollama is unreachable, returns an
    error in the response.
    """
    service = ConfigService(db)
    ai_config = await service.get_section("ai")
    current_model = ai_config.get("model", "llama3.2:latest")

    # Get OllamaProvider with database-configured URL
    from app.services.ai.ollama import get_ollama_provider_from_config, OllamaConnectionError

    try:
        ollama = await get_ollama_provider_from_config(db)

        try:
            # Fetch detailed model information
            models_data = await ollama.list_models_detailed()

            # Format models for response
            models = []
            model_names = []

            for model_info in models_data:
                model_name = model_info.get("name", "")
                if not model_name:
                    continue

                model_names.append(model_name)

                # Format size for display (convert bytes to human-readable)
                size_bytes = model_info.get("size", 0)
                if size_bytes:
                    # Convert to GB with 2 decimal places
                    size_gb = size_bytes / (1024 ** 3)
                    size_str = f"{size_gb:.2f} GB"
                else:
                    size_str = None

                models.append(AIModelInfo(
                    name=model_name,
                    size=size_str,
                    modified_at=model_info.get("modified_at"),
                    is_available=True
                ))

            # If current model not in list, add it as unavailable
            if current_model not in model_names:
                models.insert(0, AIModelInfo(
                    name=current_model,
                    is_available=False
                ))

            logger.info(f"Successfully fetched {len(models)} models from Ollama")

            return AIModelsResponse(
                models=models,
                current_model=current_model
            )

        finally:
            await ollama.close()

    except OllamaConnectionError as e:
        logger.error(f"Cannot connect to Ollama: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Cannot connect to Ollama",
                "message": str(e),
                "configured_url": ai_config.get("ollama_url", "Not configured"),
                "suggestion": "Ensure Ollama is running and the URL is correct in configuration"
            }
        )
    except Exception as e:
        logger.error(f"Failed to fetch AI models: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to fetch models",
                "message": str(e),
                "type": type(e).__name__
            }
        )
