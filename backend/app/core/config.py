"""Central configuration for the Risk Intelligence Platform backend."""
import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
# FastAPI/uvicorn does not automatically load backend/.env. Load it before
# constructing Settings so local bootstrap credentials and CORS settings work.
load_dotenv(BASE_DIR / ".env", override=False)


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = _get_bool("DEBUG", ENVIRONMENT == "development")
    DATA_DIR: str = os.getenv("DATA_DIR", str(BASE_DIR / "data"))
    MODEL_DIR: str = os.getenv("MODEL_DIR", str(BASE_DIR / "models"))
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", str(BASE_DIR / "reports"))
    TRANSACTION_TRAIN_FILE: str = os.getenv("TRANSACTION_TRAIN_FILE", "train_transaction.csv")
    IDENTITY_TRAIN_FILE: str = os.getenv("IDENTITY_TRAIN_FILE", "train_identity.csv")
    TRANSACTION_TEST_FILE: str = os.getenv("TRANSACTION_TEST_FILE", "test_transaction.csv")
    IDENTITY_TEST_FILE: str = os.getenv("IDENTITY_TEST_FILE", "test_identity.csv")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'risk_platform.db'}")
    MODEL_FILE: str = os.getenv("MODEL_FILE", "fraud_model.pkl")
    PREPROCESSOR_FILE: str = os.getenv("PREPROCESSOR_FILE", "preprocessor.pkl")
    SELECTED_FEATURES_FILE: str = os.getenv("SELECTED_FEATURES_FILE", "selected_features.json")
    METADATA_FILE: str = os.getenv("METADATA_FILE", "model_metadata.json")
    RISK_LOW_MAX: int = int(os.getenv("RISK_LOW_MAX", 30))
    RISK_MEDIUM_MAX: int = int(os.getenv("RISK_MEDIUM_MAX", 60))
    RISK_HIGH_MAX: int = int(os.getenv("RISK_HIGH_MAX", 80))
    DECISION_MAP: dict = {"LOW": "ALLOW", "MEDIUM": "REVIEW", "HIGH": "REVIEW", "CRITICAL": "HOLD"}
    RANDOM_STATE: int = int(os.getenv("RANDOM_STATE", 42))
    TEST_SIZE: float = float(os.getenv("TEST_SIZE", 0.15))
    VAL_SIZE: float = float(os.getenv("VAL_SIZE", 0.15))
    N_SELECTED_FEATURES: int = int(os.getenv("N_SELECTED_FEATURES", 40))
    ALLOW_SYNTHETIC_FALLBACK: bool = _get_bool("ALLOW_SYNTHETIC_FALLBACK", True)
    SYNTHETIC_ROWS: int = int(os.getenv("SYNTHETIC_ROWS", 20000))
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000").split(",")
    DEFAULT_ACTOR: str = os.getenv("DEFAULT_ACTOR", "system")
    AUTH_SECRET_KEY: str = os.getenv("AUTH_SECRET_KEY", "")
    ACCESS_TOKEN_TTL_SECONDS: int = int(os.getenv("ACCESS_TOKEN_TTL_SECONDS", 3600))
    DEFAULT_ADMIN_USERNAME: str = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
