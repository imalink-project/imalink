"""
Main FastAPI application for ImaLink Fase 1
"""
import os
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from database.connection import init_database
from api.images import router as images_router
from api.import_api import router as import_router

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

# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main gallery page"""
    static_dir = Path(__file__).parent / "static"
    index_file = static_dir / "index.html"
    
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(), status_code=200)
    else:
        return HTMLResponse(
            content="""
            <html>
                <head><title>ImaLink Fase 1</title></head>
                <body>
                    <h1>ImaLink Fase 1</h1>
                    <p>Welcome to ImaLink! The frontend is not yet available.</p>
                    <p>API documentation: <a href="/docs">/docs</a></p>
                </body>
            </html>
            """,
            status_code=200
        )


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "message": "ImaLink Fase 1 is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)