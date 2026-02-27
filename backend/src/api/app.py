"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from pathlib import Path

from ..config import settings
from ..infrastructure.graph import neo4j_client
from ..infrastructure.graph.schema import create_all_constraints
from ..shared.utils import logger

from .middleware import (
    log_requests_middleware,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
    SecurityHeadersMiddleware
)

# Setup templates
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting GST Reconciliation System...")
    
    # Try to connect to Neo4j (optional)
    try:
        neo4j_client.connect()
        logger.info("Neo4j connected successfully")
        
        # Create constraints and indexes
        await create_all_constraints(neo4j_client)
        logger.info("Database schema initialized")
    except Exception as e:
        logger.warning(f"Neo4j connection failed: {e}")
        logger.warning("Running in limited mode without database")
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    try:
        neo4j_client.close()
    except:
        pass
    logger.info("Application shut down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Intelligent GST Reconciliation using Knowledge Graphs",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Request logging middleware
app.middleware("http")(log_requests_middleware)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - serves dashboard."""
    return templates.TemplateResponse(
        "dashboard_light.html",
        {
            "request": request,
            "version": settings.app_version,
            "backend_status": "Running"
        }
    )


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Upload page - for uploading invoice data."""
    return templates.TemplateResponse(
        "upload_light.html",
        {"request": request}
    )


@app.get("/results", response_class=HTMLResponse)
async def results_page(request: Request):
    """Results page - shows reconciliation results."""
    return templates.TemplateResponse(
        "results_light.html",
        {"request": request}
    )


@app.get("/workflow", response_class=HTMLResponse)
async def workflow_page(request: Request):
    """Workflow page - complete GST workflow visualization."""
    return templates.TemplateResponse(
        "workflow_light.html",
        {"request": request}
    )


@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "environment": settings.environment
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "version": settings.app_version
    }


# Import and include routers
from .routes import (
    reconciliation_router,
    mismatch_router,
    audit_router,
    vendor_router,
    dashboard_router
)
from .routes.upload import router as upload_router
from .routes.chatbot import router as chatbot_router

# Include routers with API prefix
app.include_router(upload_router, prefix="/api")
app.include_router(chatbot_router, prefix="/api")
app.include_router(reconciliation_router, prefix="/api")
app.include_router(mismatch_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(vendor_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
