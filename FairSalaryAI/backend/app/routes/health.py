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
    import socket
    results = {}
    for port in [587, 465, 25]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        try:
            s.connect(("smtp.gmail.com", port))
            results[f"port_{port}"] = "CONNECTED"
            s.close()
        except Exception as e:
            results[f"port_{port}"] = f"FAILED: {type(e).__name__}: {e}"
    from app.services.email_service import send_email
    email_res = send_email("maheshburra2712@gmail.com", "Diagnostics Test", "Testing from Render")
    results["send_email_result"] = email_res
    return results