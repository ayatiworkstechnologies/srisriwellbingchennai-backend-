from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .api.routes.admin import router as admin_router
from .api.routes.health import router as health_router
from .api.routes.public import router as public_router
from .config import get_settings
from .database import engine
from .services.content import seed_admin_user, seed_default_content

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        seed_admin_user()
        seed_default_content()
        logger.info("Application startup completed successfully.")
    except Exception:
        logger.exception(
            "Application startup failed. Check DATABASE_URL and other environment variables."
        )
        raise
    yield


app = FastAPI(title=settings.project_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(public_router)
app.include_router(admin_router)
