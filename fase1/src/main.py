"""
Main FastAPI application for ImaLink Fase 1 - Pure API Backend
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from core.config import config
from database.connection import init_database
from api.v1.images import router as images_router
from api.v1.imports import router as imports_router
from api.v1.authors import router as authors_router
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

# Include API routers with v1 prefix for versioning
app.include_router(images_router, prefix="/api/v1/images", tags=["images"])
print("🔥 MAIN.PY: Loading imports router...")
app.include_router(imports_router, prefix="/api/v1/imports", tags=["imports"])
print("🔥 MAIN.PY: Imports router loaded!")
app.include_router(authors_router, prefix="/api/v1/authors", tags=["authors"])



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