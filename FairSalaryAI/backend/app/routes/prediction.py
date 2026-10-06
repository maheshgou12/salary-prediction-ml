# FairSalary AI - Prediction Routes
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Prediction
from app.schemas import (
    CandidateInput, PredictionResponse, PredictionHistoryItem, PredictionDetail
)
from app.dependencies import get_current_user
from app.services.prediction_service import prediction_service

router = APIRouter(prefix="/predict", tags=["Predictions"])


@router.post("", response_model=PredictionResponse)
async def predict_salary(
    candidate: CandidateInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Predict salary for a candidate profile."""
    try:
        candidate_data = candidate.model_dump()

        # Make prediction
        predicted, min_sal, max_sal, confidence = prediction_service.predict(candidate_data)

        # Get similar profiles
        similar = prediction_service.find_similar_profiles(candidate_data)

        # Get SHAP explanation
        explanation = prediction_service.get_explanation(candidate_data)

        # Get model info
        model_info = prediction_service.get_model_info()

        # Save prediction to database
        prediction_record = Prediction(
            user_id=current_user.id,
            input_data=candidate_data,
            predicted_salary=int(round(predicted)),
            min_salary=int(round(min_sal)),
            max_salary=int(round(max_sal)),
            confidence=confidence,
            similar_profiles=similar,
            explanation=explanation,
            model_version=model_info.get("version", "1.0.0")
        )

        db.add(prediction_record)
        db.commit()
        db.refresh(prediction_record)

        # Format explanation for response
        formatted_explanation = [
            {"feature": e["feature"], "contribution": e["contribution"], "direction": e["direction"]}
            for e in explanation
        ]

        return PredictionResponse(
            predicted_salary=int(round(predicted)),
            minimum_salary=int(round(min_sal)),
            maximum_salary=int(round(max_sal)),
            confidence=confidence,
            similar_profiles=similar,
            explanation=formatted_explanation,
            model_version=model_info.get("version", "1.0.0"),
            fairness_disclaimer=(
                "This prediction was made without using protected attributes "
                "(gender, age). The model was audited for demographic parity "
                "across protected groups. Fairness analysis did not identify "
                "a significant disparity under the selected metrics. "
                "This tool provides recommendations, not binding decisions."
            ),
            prediction_id=prediction_record.id
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("", response_model=List[PredictionHistoryItem])
async def get_prediction_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 20
):
    """Get user's prediction history."""
    offset = (page - 1) * page_size

    predictions = db.query(Prediction).filter(
        Prediction.user_id == current_user.id
    ).order_by(Prediction.created_at.desc()).offset(offset).limit(page_size).all()

    return predictions


@router.get("/{prediction_id}", response_model=PredictionDetail)
async def get_prediction_detail(
    prediction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed prediction by ID."""
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == current_user.id
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )

    return prediction