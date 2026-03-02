from fastapi import APIRouter

from app.api.entries import router as entries_router
from app.api.pipeline import router as pipeline_router
from app.api.tags import router as tags_router
from app.api.profile import router as profile_router
from app.api.config import router as config_router
from app.api.stats import router as stats_router

api_router = APIRouter()
api_router.include_router(entries_router, prefix="/entries", tags=["entries"])
api_router.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])
api_router.include_router(tags_router, prefix="/tags", tags=["tags"])
api_router.include_router(profile_router, prefix="/profile", tags=["profile"])
api_router.include_router(config_router, prefix="/config", tags=["config"])
api_router.include_router(stats_router, prefix="/stats", tags=["stats"])
