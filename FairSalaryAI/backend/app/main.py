# FairSalary AI - Main FastAPI Application
# Live SHAP explanation pipeline verified
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import init_db, engine
from app.routes import auth, prediction, fairness, model, health, candidates


def _auto_seed_if_empty():
    """Automatically populate candidate profiles on clean databases (like Neon PostgreSQL)."""
    try:
        import csv
        import json
        from pathlib import Path
        from app.database import SessionLocal
        from app.models import CandidateProfile

        db = SessionLocal()
        try:
            if db.query(CandidateProfile).count() == 0:
                csv_path = Path(__file__).resolve().parents[2] / "ml" / "data" / "raw" / "salary_data.csv"
                if csv_path.exists():
                    print("Auto-seeding candidate profiles into database...")
                    with open(csv_path, mode="r", encoding="utf-8") as f:
                        rows = list(csv.DictReader(f))
                    edu_map = {
                        "High School": "High School",
                        "Bachelor": "Bachelor's Degree",
                        "Master": "Master's Degree",
                        "PhD": "PhD",
                        "Associate": "Associate Degree",
                    }
                    objs = []
                    for r in rows:
                        skills = json.dumps([f"skill{i}" for i in range(int(float(r.get("skills_count") or 0)))])
                        objs.append(CandidateProfile(
                            experience_years=float(r["years_experience"]),
                            education=edu_map.get(r["education_level"], r["education_level"]),
                            job_role=r["job_role"],
                            location=r["location"],
                            skills=skills,
                            industry="Technology",
                            company_size=r["company_size"],
                            employment_type="Full-time",
                            salary=int(float(r["salary"])),
                            gender=r["gender"],
                            age=int(float(r["age"])),
                            source="seed"
                        ))
                    db.bulk_save_objects(objs)
                    db.commit()
                    print(f"Auto-seeded {len(objs)} candidate profiles successfully.")
        finally:
            db.close()
    except Exception as e:
        print(f"Auto-seed check: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting FairSalary AI...")
    init_db()
    _auto_seed_if_empty()
    print("Database initialized")
    print(f"Model loaded: {settings.MODEL_PATH}")
    yield
    # Shutdown
    print("Shutting down FairSalary AI...")
    engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Fair Salary Recommendation and Bias Analysis Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": f"HTTP_{exc.status_code}"}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": str(exc.errors()),
            "error_code": "VALIDATION_ERROR"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        import traceback
        traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
    )


# Include routers
app.include_router(health.router)
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(prediction.router, prefix=settings.API_PREFIX)
app.include_router(fairness.router, prefix=settings.API_PREFIX)
app.include_router(model.router, prefix=settings.API_PREFIX)
app.include_router(candidates.router, prefix=settings.API_PREFIX)


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI-Powered Fair Salary Recommendation and Bias Analysis Platform",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )