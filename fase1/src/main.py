"""
Main FastAPI application for ImaLink Fase 1
"""
import os
from pathlib import Path
from fastapi import FastAPI, Depends, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from config import config
from database.connection import init_database
from api.images import router as images_router
from api.import_api import router as import_router
from api.authors import router as authors_router
from api.selections import router as selections_router

# Ensure directories exist
config.ensure_directories()

# Initialize database
init_database()

# Create FastAPI app
app = FastAPI(
    title="ImaLink Fase 1",
    description="Simple image gallery and management system",
    version="0.1.0"
)

# Include API routers
app.include_router(images_router, prefix="/api/images", tags=["images"])
app.include_router(import_router, prefix="/api/import", tags=["import"])
app.include_router(authors_router, prefix="/api/authors", tags=["authors"])
app.include_router(selections_router, prefix="/api/selections", tags=["selections"])

# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Middleware to add no-cache headers to static files in development
@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Add no-cache headers for static files in development
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    
    return response


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard page"""
    return serve_static_file("index.html")


@app.get("/gallery", response_class=HTMLResponse)
async def gallery():
    """Serve the gallery page"""
    return serve_static_file("gallery.html")


@app.get("/import", response_class=HTMLResponse)
async def import_page():
    """Serve the import management page"""
    return serve_static_file("import.html")


@app.get("/authors", response_class=HTMLResponse)
async def authors_page():
    """Serve the authors management page"""
    return serve_static_file("authors.html")


@app.get("/selections", response_class=HTMLResponse)
async def selections_page():
    """Serve the selections management page"""
    return serve_static_file("selections.html")


def serve_static_file(filename: str):
    """Helper function to serve static HTML files"""
    static_dir = Path(__file__).parent / "static"
    file_path = static_dir / filename
    
    if file_path.exists():
        content = file_path.read_text(encoding="utf-8")
        return HTMLResponse(content=content, status_code=200)
    else:
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Side ikke funnet - ImaLink</title></head>
                <body>
                    <h1>404 - Side ikke funnet</h1>
                    <p>Filen {filename} ble ikke funnet.</p>
                    <p><a href="/">← Tilbake til hovedsiden</a></p>
                </body>
            </html>
            """,
            status_code=404
        )


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "message": "ImaLink Fase 1 is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)