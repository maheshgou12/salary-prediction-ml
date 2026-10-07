# FairSalary AI - Pydantic Schemas
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ==========================================
# Authentication Schemas
# ==========================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    sub: str  # user_id (JWT spec requires string)
    email: str
    role: str
    exp: int
    type: str = "access"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ==========================================
# Prediction Schemas
# ==========================================

class CandidateInput(BaseModel):
    """Input features for salary prediction."""
    experience_years: float = Field(..., ge=0, le=50, description="Years of professional experience")
    education: str = Field(..., description="Education level")
    job_role: str = Field(..., min_length=1, max_length=100, description="Job title/role")
    location: str = Field(..., min_length=1, max_length=100, description="Work location")
    skills: List[str] = Field(..., min_length=1, max_length=50, description="Technical skills")
    industry: str = Field(..., min_length=1, max_length=100, description="Industry sector")
    company_size: str = Field(..., description="Company size category")
    employment_type: str = Field(default="Full-time", description="Employment type")
    previous_salary: Optional[float] = Field(default=None, ge=0, description="Existing/expected prior salary (USD)")
    interview_score: Optional[float] = Field(default=None, ge=0, le=10, description="Interview performance score (0-10)")

    # Valid values (documentation)
    EDUCATION_OPTIONS: ClassVar[List[str]] = [
        "High School", "Associate Degree", "Bachelor's Degree",
        "Master's Degree", "PhD"
    ]
    COMPANY_SIZE_OPTIONS: ClassVar[List[str]] = [
        "Startup (1-50)", "Small (51-200)", "Medium (201-1000)", "Large (1000+)"
    ]
    EMPLOYMENT_TYPE_OPTIONS: ClassVar[List[str]] = [
        "Full-time", "Part-time", "Contract", "Internship", "Freelance"
    ]


class SimilarProfiles(BaseModel):
    count: int
    median_salary: int
    percentile_25: int
    percentile_75: int


class ExplanationFeature(BaseModel):
    feature: str
    contribution: int
    direction: str  # "positive" or "negative"


class PredictionResponse(BaseModel):
    predicted_salary: int
    minimum_salary: int
    maximum_salary: int
    confidence: float = Field(..., ge=0, le=1)
    similar_profiles: SimilarProfiles
    explanation: List[ExplanationFeature]
    model_version: str
    fairness_disclaimer: str
    prediction_id: int


class PredictionCreate(BaseModel):
    input_data: Dict[str, Any]
    predicted_salary: int
    min_salary: int
    max_salary: int
    confidence: float
    similar_profiles: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None
    model_version: str


class PredictionHistoryItem(BaseModel):
    id: int
    input_data: Dict[str, Any]
    predicted_salary: int
    minimum_salary: int
    maximum_salary: int
    confidence: float
    model_version: str
    created_at: datetime

    class Config:
        from_attributes = True


class PredictionDetail(PredictionHistoryItem):
    similar_profiles: Optional[Any] = None
    explanation: Optional[Any] = None


# ==========================================
# Fairness Schemas
# ==========================================

class GroupMetrics(BaseModel):
    group: str
    count: int
    mean_predicted: float
    mean_actual: Optional[float] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    prediction_difference: Optional[float] = None


class FairnessMetrics(BaseModel):
    demographic_parity_difference: Optional[float] = None
    mean_prediction_difference: Optional[float] = None
    mae_by_group: Dict[str, float] = {}
    rmse_by_group: Dict[str, float] = {}
    groups: List[GroupMetrics] = []


class FairnessReport(BaseModel):
    overall_status: str  # "PASS" | "REVIEW" | "WARNING"
    protected_attribute: str
    metrics: FairnessMetrics
    recommendations: List[str] = []
    generated_at: datetime


class FairnessDashboard(BaseModel):
    overall_status: str
    model_version: str
    protected_attributes: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    generated_at: Optional[datetime] = None


# ==========================================
# Model Schemas
# ==========================================

class ModelMetrics(BaseModel):
    mae: float
    rmse: float
    r2: float
    cv_mae: Optional[float] = None
    cv_std: Optional[float] = None


class ModelInfo(BaseModel):
    version: str
    model_type: str
    metrics: ModelMetrics
    fairness_metrics: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Health & System Schemas
# ==========================================

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    model_loaded: bool
    timestamp: datetime


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
