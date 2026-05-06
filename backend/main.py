"""
Barcode-Based Campus Entry/Exit System - FastAPI Backend
Run with: uvicorn main:app --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from database import engine, Base
import models  # noqa: F401

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified.")
    print("Barcode Campus System API running on http://localhost:8000")
    yield


app = FastAPI(
    title="Barcode Campus Entry/Exit System",
    description="Digitized student movement logging using barcode-based ID scanning",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routes (must be registered BEFORE static file mounts) ---
from routes.scanner import router as scanner_router
from routes.dashboard import router as dashboard_router
from routes.auth import router as auth_router
from routes.students import router as students_router

app.include_router(scanner_router)
app.include_router(dashboard_router)
app.include_router(auth_router)
app.include_router(students_router)


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Barcode Campus System", "version": "1.0.0"}


@app.get("/api/force-seed")
def force_seed():
    """Temporary endpoint to seed the database without terminal access."""
    import seed_data
    seed_data.seed()
    return {"status": "success", "message": "Database seeded with NIT Jalandhar students (including Ravishankar) and Guard credentials."}


# --- Serve Frontend index.html ---
@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# --- Static file sub-mounts (LAST) ---
if os.path.exists(os.path.join(FRONTEND_DIR, "css")):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
if os.path.exists(os.path.join(FRONTEND_DIR, "js")):
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
