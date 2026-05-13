from contextlib import asynccontextmanager
import logging
from time import sleep

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

from .api.metadata import API_DESCRIPTION, OPENAPI_TAGS
from .api.router import api_router
from .config import get_settings
from .database import engine
from .services.content import seed_admin_user, seed_default_content

settings = get_settings()
logger = logging.getLogger("srisriwellbeing.api")


def wait_for_database(max_attempts: int = 6, delay_seconds: int = 5) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == max_attempts:
                raise
            logger.warning(
                "Database connection unavailable on startup; retrying in %s seconds (%s/%s).",
                delay_seconds,
                attempt,
                max_attempts,
            )
            sleep(delay_seconds)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        wait_for_database()
        seed_admin_user()
        if settings.seed_default_content:
            seed_default_content()
        logger.info("Application startup completed successfully.")
    except Exception:
        logger.exception(
            "Application startup failed. Check DATABASE_URL and other environment variables."
        )
        raise
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(
    title=settings.project_name,
    description=API_DESCRIPTION,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_origin_regex=settings.frontend_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
