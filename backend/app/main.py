from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, bills, subscriptions, dashboard
from app.core.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background jobs on boot, clean up on shutdown."""
    start_scheduler()
    yield
    stop_scheduler()


# CORS origins: comma-separated list in CORS_ORIGINS env var, defaulting to localhost dev.
_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app = FastAPI(
    title="BillWise API",
    version="1.0.0",
    description=(
        "BillWise — personal bill & subscription tracker with AI-powered extraction, "
        "email reminders, and spending analytics. "
        "All routes (except /auth/* and /health) require a Bearer JWT."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(bills.router)
app.include_router(subscriptions.router)
app.include_router(dashboard.router)


@app.get("/health", tags=["meta"])
def health():
    """Liveness probe — returns 200 OK when the app is running."""
    return {"status": "ok", "version": "1.0.0"}
