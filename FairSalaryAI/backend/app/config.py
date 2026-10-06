# FairSalary AI - Configuration Management
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_project_root() -> Path:
    """Get the FairSalaryAI project root directory."""
    # config.py is at: FairSalaryAI/backend/app/config.py
    # We need to go up 3 levels: app -> backend -> FairSalaryAI
    current = Path(__file__).resolve()
    # Go up: config.py -> app -> backend -> FairSalaryAI
    for _ in range(3):
        current = current.parent
    return current


PROJECT_ROOT = get_project_root()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "FairSalary AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://fairuser:fairpass@localhost:5432/fairsalary",
        description="PostgreSQL connection string"
    )
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Security
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-in-production-min-32-chars",
        description="JWT signing secret"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Model
    MODEL_PATH: str = str(PROJECT_ROOT / "ml" / "models" / "best_model.joblib")
    MODEL_METADATA_PATH: str = str(PROJECT_ROOT / "ml" / "models" / "metadata.json")
    MODEL_VERSION: str = "1.0.0"
    MODEL_METADATA_PATH: str = "ml/models/metadata.json"
    MODEL_VERSION: str = "1.0.0"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Feature Flags
    ENABLE_FAIRNESS_ANALYSIS: bool = True
    ENABLE_SHAP_EXPLANATIONS: bool = True
    ENABLE_SIMILAR_PROFILES: bool = True
    ENABLE_SALARY_RANGE: bool = True

    # External Services (Optional)
    SENTRY_DSN: Optional[str] = None
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()