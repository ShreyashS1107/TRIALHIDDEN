from fastapi import APIRouter
from app.api.v1.alerts import router as alerts_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.health import router as health_router
from app.api.v1.projects import router as projects_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])

