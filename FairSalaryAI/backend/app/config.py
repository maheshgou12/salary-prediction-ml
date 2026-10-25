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
        env_file=[
            ".env",
            str(PROJECT_ROOT / "backend" / ".env"),
            str(PROJECT_ROOT / ".env"),
        ],
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
        default=f"sqlite:///{PROJECT_ROOT.as_posix()}/backend/fairsalary.db",
        description="Database connection string"
    )
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    @property
    def resolved_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        if url.startswith("sqlite:///"):
            path_part = url[len("sqlite:///"):]
            if path_part.startswith("./"):
                path_part = path_part[2:]
            p = Path(path_part)
            if not p.is_absolute():
                full_path = (PROJECT_ROOT / "backend" / path_part).resolve()
                return f"sqlite:///{full_path.as_posix()}"
        return url

    # Security (1-year non-expiring tokens for smooth continuous usage)
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-in-production-min-32-chars",
        description="JWT signing secret"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 525600  # 365 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 365
    BCRYPT_ROUNDS: int = 12

    # CORS & Links
    FRONTEND_URL: str = "https://salary-prediction-ml-ivory.vercel.app"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://salary-prediction-ml-ivory.vercel.app",
    ]

    # Model
    MODEL_PATH: str = str(PROJECT_ROOT / "ml" / "models" / "best_model.joblib")
    MODEL_METADATA_PATH: str = str(PROJECT_ROOT / "ml" / "models" / "training_summary.json")
    MODEL_VERSION: str = "1.0.0"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Feature Flags
    ENABLE_FAIRNESS_ANALYSIS: bool = True
    ENABLE_SHAP_EXPLANATIONS: bool = True
    ENABLE_SIMILAR_PROFILES: bool = True
    ENABLE_SALARY_RANGE: bool = True

    # External Services
    SENTRY_DSN: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None
    BREVO_API_KEY: Optional[str] = None
    SMTP_HOST: Optional[str] = "smtp.gmail.com"
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = "maheshburra2712@gmail.com"
    SMTP_PASSWORD: Optional[str] = "igoj tols awne bfmx"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()