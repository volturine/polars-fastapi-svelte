from fastapi import APIRouter
from .service import get_health_status
from .schemas import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def check_health():
    return get_health_status()
