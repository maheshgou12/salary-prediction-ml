# FairSalary AI - Health Check Routes
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import HealthResponse
from app.config import settings
from app.services.prediction_service import prediction_service

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    # Check database connection
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    # Check model loaded
    model_loaded = prediction_service.model is not None

    return HealthResponse(
        status="healthy" if db_status == "connected" and model_loaded else "degraded",
        version=settings.APP_VERSION,
        database=db_status,
        model_loaded=model_loaded,
        timestamp=__import__("datetime").datetime.utcnow()
    )


@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    model_loaded = prediction_service.model is not None
    if not model_loaded:
        return {"ready": False, "reason": "Model not loaded"}

    return {"ready": True}


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"alive": True}


@router.get("/smtp")
async def test_smtp_connection():
    results = {}
    results["resend_key_configured"] = bool(settings.RESEND_API_KEY)
    if settings.RESEND_API_KEY:
        import httpx
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {settings.RESEND_API_KEY.strip()}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": "onboarding@resend.dev",
                        "to": ["maheshburra2712@gmail.com"],
                        "subject": "FairSalary AI - Diagnostic Test",
                        "text": "Testing Resend email delivery from Render",
                    },
                )
            results["resend_status"] = r.status_code
            results["resend_response"] = r.text
        except Exception as e:
            results["resend_error"] = str(e)
    return results