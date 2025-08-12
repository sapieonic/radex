from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.config import settings
from app.database import engine
from app.models import Base
from app.api import auth, folders, documents, rag
from app.core.exceptions import (
    CredentialsException,
    PermissionDeniedException,
    NotFoundException,
    BadRequestException,
    ConflictException
)

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not create database tables: {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="RAG Solution with Role-Based Access Control",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(CredentialsException)
async def credentials_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(PermissionDeniedException)
async def permission_denied_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(BadRequestException)
async def bad_request_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(ConflictException)
async def conflict_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(folders.router, prefix="/api/v1/folders", tags=["folders"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])

# Root endpoints
@app.get("/")
def read_root():
    return {
        "message": "RAG RBAC System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "1.0.0"
    }

# Optional: Add startup event to validate configuration
@app.on_event("startup")
async def startup_event():
    print(f"Starting {settings.app_name}")
    print(f"Debug mode: {settings.debug}")
    
    # Validate critical settings
    if not settings.jwt_secret_key or settings.jwt_secret_key == "your-secret-key-change-this":
        print("WARNING: JWT secret key is not properly configured!")
    
    if not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key":
        print("WARNING: OpenAI API key is not properly configured!")

@app.on_event("shutdown")
async def shutdown_event():
    print(f"Shutting down {settings.app_name}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )