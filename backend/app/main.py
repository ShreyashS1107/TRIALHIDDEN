from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router

app = FastAPI(
    title="SIH26103 Backend",
    description="Backend API for the SIH26103 AI-powered infrastructure project monitoring platform.",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# Register safe, configurable CORS policy
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=False if "*" in settings.CORS_ORIGINS else True,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )

# Include v1 API router under prefix /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Welcome to SIH26103 Backend API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
