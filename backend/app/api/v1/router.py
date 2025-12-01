"""
Main API v1 router aggregating all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, config, documents, metrics, queue


api_router = APIRouter(prefix="/v1")

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(queue.router)
api_router.include_router(config.router)
api_router.include_router(metrics.router)
