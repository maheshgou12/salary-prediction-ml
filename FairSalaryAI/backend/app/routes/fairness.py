# FairSalary AI - Fairness Routes
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.services.fairness_service import fairness_service
from app.schemas import FairnessDashboard

router = APIRouter(prefix="/fairness", tags=["Fairness"])


@router.get("", response_model=FairnessDashboard)
async def get_fairness_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive fairness dashboard."""
    return fairness_service.get_fairness_dashboard()


@router.get("/attribute/{attribute}")
async def get_attribute_fairness(
    attribute: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get fairness metrics for a specific protected attribute."""
    if attribute not in ["gender", "age"]:
        raise HTTPException(
            status_code=400,
            detail="Attribute must be 'gender' or 'age'"
        )

    return fairness_service.get_group_metrics(attribute)


@router.get("/intersectional")
async def get_intersectional_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get intersectional fairness analysis."""
    return fairness_service.get_intersectional_analysis()


@router.get("/proxy")
async def get_proxy_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get proxy feature analysis."""
    return fairness_service.get_proxy_analysis()