"""
Risk Intelligence Platform — FastAPI entrypoint.

Run locally:
    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.database import init_db
from app.api import (
    routes_transactions, routes_merchants, routes_risk,
    routes_copilot, routes_analytics, routes_audit,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Risk Intelligence Platform API",
    description="Explainable Fraud Agent, Merchant Risk Investigator, and Real-time Transaction Copilot.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Database initialized. Model dir: %s", settings.MODEL_DIR)


@app.get("/api/health", tags=["health"])
def health():
    from app.ml.predict import get_model_bundle
    bundle = get_model_bundle()
    return {
        "status": "ok",
        "model_loaded": bundle.is_ready,
        "model_name": bundle.metadata.get("model_name") if bundle.is_ready else None,
        "data_source": bundle.metadata.get("data_source") if bundle.is_ready else None,
    }


app.include_router(routes_transactions.router)
app.include_router(routes_merchants.router)
app.include_router(routes_risk.router)
app.include_router(routes_copilot.router)
app.include_router(routes_analytics.router)
app.include_router(routes_audit.router)
