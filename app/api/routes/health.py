from fastapi import APIRouter

from ...schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"], summary="Health check")
def healthcheck():
    return HealthResponse(status="ok")
