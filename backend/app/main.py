"""Risk Intelligence Platform — FastAPI entrypoint."""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.config import settings
from app.core.security import decode_access_token
from app.database.database import SessionLocal, init_db
from app.api import routes_auth, routes_transactions, routes_merchants, routes_risk, routes_copilot, routes_analytics, routes_audit, routes_cases

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# These endpoints must be reachable before a bearer token exists. /demo is
# intentionally public only in development; the route itself enforces that.
PUBLIC_PATHS = {
    "/api/health",
    "/api/health/ready",
    "/api/auth/login",
    "/api/auth/demo",
    "/openapi.json",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized. Model dir: %s", settings.MODEL_DIR)
    yield


app = FastAPI(
    title="Risk Intelligence Platform API",
    description="Explainable Fraud Agent, Merchant Risk Investigator, Transaction Copilot, and investigation case management.",
    version="2.1.2",
    lifespan=lifespan,
)

if settings.ENVIRONMENT == "development":
    cors_kwargs = {
        "allow_origins": [o.strip() for o in settings.CORS_ORIGINS if o.strip()],
        "allow_origin_regex": r"https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?$",
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
else:
    cors_kwargs = {
        "allow_origins": [o.strip() for o in settings.CORS_ORIGINS if o.strip()],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
app.add_middleware(CORSMiddleware, **cors_kwargs)


@app.middleware("http")
async def authentication_middleware(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS or not request.url.path.startswith("/api/"):
        return await call_next(request)
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Authentication required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        request.state.user = decode_access_token(authorization[7:].strip())
    except HTTPException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await call_next(request)


@app.get("/api/health", tags=["health"])
def health():
    from app.ml.predict import get_model_bundle
    model = get_model_bundle()
    database_ok = False
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        database_ok = True
    finally:
        db.close()
    return {
        "status": "ok" if database_ok else "degraded",
        "database": "ok" if database_ok else "error",
        "model_loaded": model.is_ready,
        "model_name": model.metadata.get("model_name") if model.is_ready else None,
        "data_source": model.metadata.get("data_source") if model.is_ready else None,
    }


@app.get("/api/health/ready", tags=["health"])
def readiness():
    from app.ml.predict import get_model_bundle
    model = get_model_bundle()
    if not model.is_ready:
        raise HTTPException(status_code=503, detail="Model is not ready. Train/load the model before serving predictions.")
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    finally:
        db.close()
    return {
        "status": "ready",
        "model_name": model.metadata.get("model_name"),
        "data_source": model.metadata.get("data_source"),
    }


app.include_router(routes_auth.router)
app.include_router(routes_transactions.router)
app.include_router(routes_merchants.router)
app.include_router(routes_risk.router)
app.include_router(routes_copilot.router)
app.include_router(routes_analytics.router)
app.include_router(routes_audit.router)
app.include_router(routes_cases.router)
