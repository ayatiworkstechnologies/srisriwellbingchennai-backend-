from fastapi import APIRouter

from .routes.admin import router as admin_router
from .routes.health import router as health_router
from .routes.public import router as public_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(public_router)
api_router.include_router(admin_router)
