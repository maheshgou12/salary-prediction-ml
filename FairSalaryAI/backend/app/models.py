# FairSalary AI - SQLAlchemy Models
import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"
    INTERNSHIP = "Internship"
    FREELANCE = "Freelance"


class CompanySize(str, enum.Enum):
    STARTUP = "Startup (1-50)"
    SMALL = "Small (51-200)"
    MEDIUM = "Medium (201-1000)"
    LARGE = "Large (1000+)"


class EducationLevel(str, enum.Enum):
    HIGH_SCHOOL = "High School"
    ASSOCIATE = "Associate Degree"
    BACHELOR = "Bachelor's Degree"
    MASTER = "Master's Degree"
    PHD = "PhD"


class Gender(str, enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    NON_BINARY = "Non-binary"
    PREFER_NOT_TO_SAY = "Prefer not to say"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.USER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Input features (stored as JSONB for flexibility)
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Prediction results
    predicted_salary: Mapped[int] = mapped_column(Integer, nullable=False)
    min_salary: Mapped[int] = mapped_column(Integer, nullable=False)
    max_salary: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)

    # Supporting information
    similar_profiles: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    explanation: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Model info
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="predictions")

    __table_args__ = (
        Index("ix_predictions_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Prediction(id={self.id}, user_id={self.user_id}, salary={self.predicted_salary})>"


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Features used for prediction
    experience_years: Mapped[float] = mapped_column(nullable=False)
    education: Mapped[EducationLevel] = mapped_column(
        Enum(EducationLevel), nullable=False
    )
    job_role: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    skills: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    company_size: Mapped[CompanySize] = mapped_column(
        Enum(CompanySize), nullable=False
    )
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType), nullable=False
    )

    # Target variable
    salary: Mapped[int] = mapped_column(Integer, nullable=False)

    # Protected attributes (NOT used for prediction, only for fairness analysis)
    gender: Mapped[Optional[Gender]] = mapped_column(
        Enum(Gender), nullable=True, index=True
    )
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Metadata
    source: Mapped[str] = mapped_column(String(50), default="synthetic", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_candidate_role_location", "job_role", "location"),
        Index("ix_candidate_experience_education", "experience_years", "education"),
    )

    def __repr__(self) -> str:
        return f"<CandidateProfile(id={self.id}, role={self.job_role}, salary={self.salary})>"


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    version: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    model_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Performance metrics
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Fairness metrics
    fairness_metrics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Model artifacts path
    model_path: Mapped[str] = mapped_column(String(500), nullable=False)
    preprocessor_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ModelVersion(version={self.version}, type={self.model_type}, active={self.is_active})>"