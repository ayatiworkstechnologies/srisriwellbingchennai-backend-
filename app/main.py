from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes.admin import router as admin_router
from .api.routes.health import router as health_router
from .api.routes.public import router as public_router
from .config import get_settings
from .database import Base, engine
from .services.content import seed_admin_user, seed_default_content

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_admin_user()
    seed_default_content()
    yield


app = FastAPI(title=settings.project_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(public_router)
app.include_router(admin_router)
