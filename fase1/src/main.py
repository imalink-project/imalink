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
from core.config import config
from database.connection import init_database
from api.v1.images import router as images_router
from api.v1.import_sessions import router as import_sessions_router
from api.v1.authors import router as authors_router
from api.v1.debug import router as debug_router
from api.v1.photos import router as photos_router
from core.exceptions import APIException

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

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers with v1 prefix for versioning
app.include_router(images_router, prefix="/api/v1/images", tags=["images"])
app.include_router(import_sessions_router, prefix="/api/v1/import_sessions", tags=["import_sessions"])
app.include_router(authors_router, prefix="/api/v1/authors", tags=["authors"])
app.include_router(debug_router, prefix="/api/v1/debug", tags=["debug"])
app.include_router(photos_router, prefix="/api/v1/photos", tags=["photos"])

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