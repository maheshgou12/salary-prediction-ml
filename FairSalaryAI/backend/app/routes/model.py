# FairSalary AI - Model Metrics Routes
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.services.prediction_service import prediction_service
from app.schemas import ModelInfo

router = APIRouter(prefix="/model", tags=["Model"])


@router.get("/metrics")
async def get_model_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get model performance metrics."""
    return prediction_service.get_model_info()


@router.get("/info", response_model=ModelInfo)
async def get_model_info_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed model information."""
    info = prediction_service.get_model_info()
    return {
        "version": info.get("version", "1.0.0"),
        "model_type": info.get("model_type", "Unknown"),
        "metrics": info.get("metrics", {}),
        "fairness_metrics": info.get("fairness_metrics"),
        "is_active": True,
        "created_at": __import__("datetime").datetime.utcnow()
    }