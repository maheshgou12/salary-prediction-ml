# FairSalary AI - Candidate Records Routes
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import CandidateProfile, CompanySize, EducationLevel, EmploymentType, User
from app.schemas import CandidateInput

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post("", status_code=201)
async def add_candidate_profile(
    candidate: CandidateInput,
    salary: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a real candidate record (with actual salary) to the database.

    New records immediately improve the similar-profiles statistics used by
    future predictions — no retraining needed.
    """
    try:
        record = CandidateProfile(
            experience_years=candidate.experience_years,
            education=EducationLevel(candidate.education),
            job_role=candidate.job_role,
            location=candidate.location,
            skills=candidate.skills,
            industry=candidate.industry,
            company_size=CompanySize(candidate.company_size),
            employment_type=EmploymentType(candidate.employment_type),
            salary=salary,
            source="real",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid field value: {e}")

    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "message": "Candidate record added"}


@router.get("/count")
async def candidate_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"count": db.query(CandidateProfile).count()}
