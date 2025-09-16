"""Main FastAPI application for E4P."""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse
import os
from pathlib import Path

from app.config import settings
from app.routes import encrypt, decrypt, download

# Create FastAPI app
app = FastAPI(
    title="Encryption 4 People (E4P)",
    description="Secure file encryption web application",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Include routers
app.include_router(encrypt.router)
app.include_router(decrypt.router)
app.include_router(download.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page with encryption form."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "max_file_size": settings.max_file_size_mb,
        "supported_algorithms": ["AES-256-GCM", "XCHACHA20-POLY1305"]
    })


@app.get("/decrypt", response_class=HTMLResponse)
async def decrypt_page(request: Request):
    """Decryption page."""
    return templates.TemplateResponse("decrypt.html", {
        "request": request,
        "max_file_size": settings.max_file_size_mb
    })


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "max_file_size_mb": settings.max_file_size_mb,
        "max_concurrency": settings.max_concurrency
    }


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    # Ensure temp directory exists
    os.makedirs(settings.temp_dir, exist_ok=True)
    print(f"E4P application started on {settings.app_host}:{settings.app_port}")
    print(f"Temp directory: {settings.temp_dir}")
    print(f"Max file size: {settings.max_file_size_mb}MB")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    # Cleanup resources
    from app.services.tasks import TaskManager
    from app.services.storage import StorageManager
    
    # Create instances for cleanup
    task_manager = TaskManager()
    storage_manager = StorageManager()
    
    await task_manager.shutdown()
    await storage_manager.shutdown()
    print("E4P application shutdown complete")


if __name__ == "__main__":
    import uvicorn
    
    print(f"🌐 Starting E4P server on {settings.app_host}:{settings.app_port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )
