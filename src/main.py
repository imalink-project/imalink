"""
Main FastAPI application for ImaLink Fase 1 - Pure API Backend
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from src.core.config import config
from src.database.connection import init_database
from src.api.v1.import_sessions import router as import_sessions_router
from src.api.v1.authors import router as authors_router
from src.api.v1.debug import router as debug_router
from src.api.v1.photos import router as photos_router
from src.api.v1.tags import router as tags_router
from src.api.v1.database_stats import router as database_stats_router
from src.api.v1.photo_searches import router as photo_searches_router
from src.api.v1.photo_collections import router as photo_collections_router
from src.api.photo_stacks import router as photo_stacks_router
from src.api.auth import router as auth_router
from src.api.users import router as users_router
from src.core.exceptions import APIException

# Ensure directories exist
config.ensure_directories()

# Initialize database
init_database()

# Create FastAPI app
app = FastAPI(
    title="ImaLink API",
    description="Pure API backend for image gallery and management system",
    version="0.1.0"
)

# Add CORS middleware for client access (desktop app, web viewers, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers with v1 prefix for versioning
app.include_router(auth_router, prefix="/api/v1")  # Authentication endpoints
app.include_router(users_router, prefix="/api/v1")  # User management endpoints
# NOTE: image-files endpoints removed - all operations now through /photos
app.include_router(import_sessions_router, prefix="/api/v1/import-sessions", tags=["import-sessions"])
app.include_router(authors_router, prefix="/api/v1/authors", tags=["authors"])
app.include_router(debug_router, prefix="/api/v1/debug", tags=["debug"])
app.include_router(photos_router, prefix="/api/v1/photos", tags=["photos"])
app.include_router(photo_searches_router, prefix="/api/v1/photo-searches", tags=["photo-searches"])
app.include_router(photo_collections_router, prefix="/api/v1")  # Photo collections endpoints
app.include_router(tags_router, prefix="/api/v1")  # Tag endpoints
app.include_router(photo_stacks_router, prefix="/api/v1")  # PhotoStack endpoints
app.include_router(database_stats_router, prefix="/api/v1")  # Database statistics (no auth required)

# Debug endpoint to list all routes
@app.get("/debug/routes")
async def list_routes():
    """Debug endpoint to show all available routes"""
    routes = []
    for route in app.routes:
        route_info = {
            "path": getattr(route, 'path', 'unknown'),
            "methods": list(getattr(route, 'methods', [])),
            "name": getattr(route, 'name', 'unnamed')
        }
        routes.append(route_info)
    return {"routes": routes}

# Global exception handler for API exceptions
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions with structured response"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )






@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "message": "ImaLink Fase 1 is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)