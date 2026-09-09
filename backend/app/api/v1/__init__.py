from fastapi import APIRouter
from app.api.v1.alerts import router as alerts_router
from app.api.v1.benchmarks import router as benchmarks_router
from app.api.v1.analytics import router as analytics_router

from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.meta import router as meta_router
from app.api.v1.export import router as export_router
from app.api.v1.auth import router as auth_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.health import router as health_router
from app.api.v1.projects import router as projects_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(benchmarks_router, prefix="/benchmarks", tags=["Benchmarks"])


api_router.include_router(portfolio_router, prefix="/portfolio", tags=["Portfolio"])
api_router.include_router(meta_router, prefix="/meta", tags=["Metadata"])
api_router.include_router(export_router, prefix="/export", tags=["Export"])

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

api_router.include_router(ingest_router, prefix="/ingest", tags=["Ingestion"])
