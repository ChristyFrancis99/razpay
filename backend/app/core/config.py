"""
Central configuration for the Risk Intelligence Platform backend.
All values are overridable via environment variables (see .env.example).
"""
import os
from pathlib import Path
from functools import lru_cache


BASE_DIR = Path(__file__).resolve().parents[2]  # backend/


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    # --- Paths -----------------------------------------------------------
    DATA_DIR: str = os.getenv("DATA_DIR", str(BASE_DIR / "data"))
    MODEL_DIR: str = os.getenv("MODEL_DIR", str(BASE_DIR / "models"))
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", str(BASE_DIR / "reports"))

    TRANSACTION_TRAIN_FILE: str = os.getenv("TRANSACTION_TRAIN_FILE", "train_transaction.csv")
    IDENTITY_TRAIN_FILE: str = os.getenv("IDENTITY_TRAIN_FILE", "train_identity.csv")
    TRANSACTION_TEST_FILE: str = os.getenv("TRANSACTION_TEST_FILE", "test_transaction.csv")
    IDENTITY_TEST_FILE: str = os.getenv("IDENTITY_TEST_FILE", "test_identity.csv")

    # --- Database ----------------------------------------------------------
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'risk_platform.db'}")

    # --- Model artifacts ---------------------------------------------------
    MODEL_FILE: str = os.getenv("MODEL_FILE", "fraud_model.pkl")
    PREPROCESSOR_FILE: str = os.getenv("PREPROCESSOR_FILE", "preprocessor.pkl")
    SELECTED_FEATURES_FILE: str = os.getenv("SELECTED_FEATURES_FILE", "selected_features.json")
    METADATA_FILE: str = os.getenv("METADATA_FILE", "model_metadata.json")

    # --- Risk scoring thresholds (0-100 scale) ------------------------------
    RISK_LOW_MAX: int = int(os.getenv("RISK_LOW_MAX", 30))
    RISK_MEDIUM_MAX: int = int(os.getenv("RISK_MEDIUM_MAX", 60))
    RISK_HIGH_MAX: int = int(os.getenv("RISK_HIGH_MAX", 80))
    # anything above RISK_HIGH_MAX => CRITICAL

    # --- Decision engine mapping --------------------------------------------
    # risk_level -> decision. Configurable without code changes.
    DECISION_MAP: dict = {
        "LOW": "ALLOW",
        "MEDIUM": "REVIEW",
        "HIGH": "REVIEW",
        "CRITICAL": "HOLD",
    }

    # --- Training ------------------------------------------------------------
    RANDOM_STATE: int = int(os.getenv("RANDOM_STATE", 42))
    TEST_SIZE: float = float(os.getenv("TEST_SIZE", 0.15))
    VAL_SIZE: float = float(os.getenv("VAL_SIZE", 0.15))
    N_SELECTED_FEATURES: int = int(os.getenv("N_SELECTED_FEATURES", 40))

    # --- Synthetic data fallback ---------------------------------------------
    # If the real IEEE-CIS files are not present under DATA_DIR, the loader
    # can optionally generate a small synthetic dataset with the same schema
    # so the pipeline is runnable end-to-end for development/demo purposes.
    ALLOW_SYNTHETIC_FALLBACK: bool = _get_bool("ALLOW_SYNTHETIC_FALLBACK", True)
    SYNTHETIC_ROWS: int = int(os.getenv("SYNTHETIC_ROWS", 20000))

    # --- LLM (optional) for the Copilot --------------------------------------
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "")  # "anthropic" | "openai" | ""
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")

    # --- CORS ------------------------------------------------------------
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    # --- Audit -----------------------------------------------------------
    DEFAULT_ACTOR: str = os.getenv("DEFAULT_ACTOR", "system")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
