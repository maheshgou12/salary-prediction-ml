"""FairPay FastAPI REST API.
Production-ready API with async endpoints, validation, and monitoring.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response

from src.train import ALL_FEATURES, NUMERICAL_FEATURES, CATEGORICAL_FEATURES
from src.database import (
    log_prediction,
    log_batch_prediction,
    log_model_metrics,
    log_audit,
    get_prediction_history,
    get_batch_history,
    get_model_metrics_history,
    get_audit_log,
    get_prediction_stats,
    init_database,
)
from src.uncertainty import ConformalPredictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_PATH = Path("models/best_model.joblib")
CONFORMAL_PATH = Path("models/conformal_summary.json")

model = None
conformal_predictor = None
model_version = "1.0.0"
model_metadata = {}

PREDICTION_COUNTER = Counter("fairpay_predictions_total", "Total predictions", ["endpoint", "status"])
PREDICTION_LATENCY = Histogram("fairpay_prediction_latency_seconds", "Prediction latency")
BATCH_SIZE_GAUGE = Gauge("fairpay_batch_size", "Current batch size")
ACTIVE_REQUESTS = Gauge("fairpay_active_requests", "Active requests")


class CandidateInput(BaseModel):
    years_experience: float = Field(ge=0, le=30, description="Years of professional experience")
    education_level: str = Field(description="Highest education level")
    skills_count: int = Field(ge=1, le=20, description="Number of relevant skills")
    job_role: str = Field(description="Target job role")
    previous_salary: int = Field(ge=30000, le=500000, description="Previous salary in USD")
    interview_score: float = Field(ge=1, le=10, description="Interview score (1-10)")
    location: str = Field(description="Job location")
    company_size: str = Field(description="Company size category")

    @field_validator("education_level")
    @classmethod
    def validate_education(cls, v):
        allowed = ["High School", "Bachelor", "Master", "PhD"]
        if v not in allowed:
            raise ValueError(f"education_level must be one of {allowed}")
        return v

    @field_validator("job_role")
    @classmethod
    def validate_role(cls, v):
        allowed = [
            "Software Engineer", "Data Scientist", "ML Engineer", "DevOps Engineer",
            "Frontend Developer", "Backend Developer", "Full Stack Developer",
            "Data Analyst", "Product Manager", "Engineering Manager"
        ]
        if v not in allowed:
            raise ValueError(f"job_role must be one of {allowed}")
        return v

    @field_validator("location")
    @classmethod
    def validate_location(cls, v):
        allowed = ["San Francisco", "New York", "Seattle", "Austin", "Boston", "Remote", "Chicago", "Los Angeles"]
        if v not in allowed:
            raise ValueError(f"location must be one of {allowed}")
        return v

    @field_validator("company_size")
    @classmethod
    def validate_company(cls, v):
        allowed = ["Startup (1-50)", "Small (51-200)", "Medium (201-1000)", "Large (1000+)"]
        if v not in allowed:
            raise ValueError(f"company_size must be one of {allowed}")
        return v


class BatchPredictionRequest(BaseModel):
    candidates: list[CandidateInput] = Field(min_length=1, max_length=1000)


class SalaryPrediction(BaseModel):
    predicted_salary: int
    lower_bound: int
    upper_bound: int
    confidence_level: float
    model_version: str
    prediction_id: str


class BatchPredictionResponse(BaseModel):
    predictions: list[SalaryPrediction]
    summary: dict[str, Any]
    batch_id: str


class HealthResponse(BaseModel):
    status: str
    model_version: str
    model_loaded: bool
    conformal_loaded: bool
    uptime_seconds: float


class ModelInfoResponse(BaseModel):
    model_version: str
    model_type: str
    features: list[str]
    numerical_features: list[str]
    categorical_features: list[str]
    performance: dict[str, float]
    fairness_metrics: dict[str, Any] | None


start_time = time.time()


def load_model_and_conformal():
    global model, conformal_predictor, model_metadata
    try:
        model = joblib.load(MODEL_PATH)
        if hasattr(model, 'named_steps'):
            model_type = type(model.named_steps['model']).__name__
        elif hasattr(model, 'estimators_'):
            model_type = f"StackingEnsemble({type(model.estimators_[0].named_steps['model']).__name__} + ...)"
        else:
            model_type = type(model).__name__
        logger.info(f"Model loaded: {model_type}")

        if CONFORMAL_PATH.exists():
            with open(CONFORMAL_PATH) as f:
                conformal_data = json.load(f)
            conformal_predictor = ConformalPredictor(model, alpha=conformal_data.get("alpha", 0.1))
            conformal_predictor.q_hat = conformal_data.get("q_hat")
            logger.info(f"Conformal predictor loaded: q_hat=${conformal_predictor.q_hat:,.0f}")

        training_summary_path = Path("models/training_summary.json")
        if training_summary_path.exists():
            with open(training_summary_path) as f:
                model_metadata = json.load(f)

        fairness_path = Path("models/fairness_audit.json")
        if fairness_path.exists():
            with open(fairness_path) as f:
                model_metadata["fairness"] = json.load(f)

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FairPay API...")
    init_database()
    load_model_and_conformal()
    logger.info("FairPay API ready")
    yield
    logger.info("Shutting down FairPay API...")


app = FastAPI(
    title="FairPay Salary Prediction API",
    description="Production-ready salary prediction with fairness auditing and explainability",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def track_requests(request: Request, call_next):
    ACTIVE_REQUESTS.inc()
    start = time.time()
    try:
        response = await call_next(request)
        return response
    finally:
        ACTIVE_REQUESTS.dec()
        latency = time.time() - start
        PREDICTION_LATENCY.observe(latency)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy" if model is not None else "degraded",
        model_version=model_version,
        model_loaded=model is not None,
        conformal_loaded=conformal_predictor is not None,
        uptime_seconds=time.time() - start_time,
    )


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")


@app.get("/model/info", response_model=ModelInfoResponse)
async def model_info():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if hasattr(model, 'named_steps'):
        regressor = model.named_steps["model"]
        model_type = type(regressor).__name__
    elif hasattr(model, 'estimators_'):
        regressor = model.estimators_[0].named_steps['model']
        model_type = f"StackingEnsemble({type(regressor).__name__} + ...)"
    else:
        model_type = type(model).__name__

    perf = model_metadata.get("test_metrics", {})

    fairness_data = model_metadata.get("fairness", {})
    fairness_summary = {}
    if fairness_data:
        for attr in ["gender", "age"]:
            key = f"{attr}_fairlearn"
            if key in fairness_data:
                fairness_summary[attr] = {
                    "demographic_parity_difference": fairness_data[key].get("demographic_parity_difference"),
                    "equalized_odds_difference": fairness_data[key].get("equalized_odds_difference"),
                }

    return ModelInfoResponse(
        model_version=model_version,
        model_type=model_type,
        features=ALL_FEATURES,
        numerical_features=ALL_FEATURES,
        categorical_features=CATEGORICAL_FEATURES,
        performance=perf,
        fairness_metrics=fairness_summary if fairness_summary else None,
    )


@app.post("/predict", response_model=SalaryPrediction)
async def predict_salary(candidate: CandidateInput, background_tasks: BackgroundTasks, request: Request):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    prediction_id = str(uuid.uuid4())[:8]
    input_data = candidate.model_dump()

    try:
        X = pd.DataFrame([input_data])[ALL_FEATURES]
        prediction = float(model.predict(X)[0])

        if conformal_predictor and conformal_predictor.q_hat:
            q_hat = conformal_predictor.q_hat
            lower = max(0, prediction - q_hat)
            upper = prediction + q_hat
            coverage = 0.90
        else:
            rmse = 22651
            margin = 1.96 * rmse
            lower = max(0, prediction - margin)
            upper = prediction + margin
            coverage = 0.95

        result = SalaryPrediction(
            predicted_salary=int(round(prediction)),
            lower_bound=int(round(lower)),
            upper_bound=int(round(upper)),
            confidence_level=coverage,
            model_version=model_version,
            prediction_id=prediction_id,
        )

        background_tasks.add_task(
            log_prediction,
            input_data,
            result.predicted_salary,
            result.lower_bound,
            result.upper_bound,
            model_version,
            request.client.host if request.client else None,
        )

        PREDICTION_COUNTER.labels(endpoint="predict", status="success").inc()
        return result

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        PREDICTION_COUNTER.labels(endpoint="predict", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(batch: BatchPredictionRequest, background_tasks: BackgroundTasks, request: Request):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    batch_id = str(uuid.uuid4())[:8]
    candidates_data = [c.model_dump() for c in batch.candidates]

    try:
        BATCH_SIZE_GAUGE.set(len(candidates_data))
        X = pd.DataFrame(candidates_data)[ALL_FEATURES]
        predictions = model.predict(X)

        if conformal_predictor and conformal_predictor.q_hat:
            q_hat = conformal_predictor.q_hat
            margin = q_hat
            coverage = 0.90
        else:
            margin = 1.96 * 22651
            coverage = 0.95

        results = []
        for i, pred in enumerate(predictions):
            pred_val = float(pred)
            lower = max(0, pred_val - margin)
            upper = pred_val + margin
            results.append(SalaryPrediction(
                predicted_salary=int(round(pred_val)),
                lower_bound=int(round(lower)),
                upper_bound=int(round(upper)),
                confidence_level=coverage,
                model_version=model_version,
                prediction_id=f"{batch_id}-{i}",
            ))

        summary = {
            "count": len(results),
            "mean_predicted": np.mean([r.predicted_salary for r in results]),
            "median_predicted": np.median([r.predicted_salary for r in results]),
            "min_predicted": min(r.predicted_salary for r in results),
            "max_predicted": max(r.predicted_salary for r in results),
        }

        background_tasks.add_task(
            log_batch_prediction,
            f"batch_{batch_id}.csv",
            len(candidates_data),
            summary["mean_predicted"],
            "completed",
            None,
        )

        PREDICTION_COUNTER.labels(endpoint="batch", status="success").inc()
        return BatchPredictionResponse(
            predictions=results,
            summary=summary,
            batch_id=batch_id,
        )

    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        PREDICTION_COUNTER.labels(endpoint="batch", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/predictions")
async def prediction_history(limit: int = 100):
    df = get_prediction_history(limit)
    return df.to_dict("records")


@app.get("/history/batches")
async def batch_history(limit: int = 50):
    df = get_batch_history(limit)
    return df.to_dict("records")


@app.get("/history/model-metrics")
async def model_metrics_history(limit: int = 50):
    df = get_model_metrics_history(limit)
    return df.to_dict("records")


@app.get("/history/audit")
async def audit_history(limit: int = 200):
    df = get_audit_log(limit)
    return df.to_dict("records")


@app.get("/stats")
async def prediction_stats():
    return get_prediction_stats()


@app.post("/model/retrain")
async def trigger_retrain(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_retrain)
    return {"status": "retraining started", "message": "Model retraining triggered in background"}


async def run_retrain():
    import subprocess
    try:
        logger.info("Starting model retraining...")
        result = subprocess.run(
            ["python", "src/train.py"],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0:
            load_model_and_conformal()
            logger.info("Retraining completed successfully")
            log_audit("model_retrain", details={"status": "success"})
        else:
            logger.error(f"Retraining failed: {result.stderr}")
            log_audit("model_retrain", details={"status": "failed", "error": result.stderr})
    except Exception as e:
        logger.error(f"Retraining error: {e}")
        log_audit("model_retrain", details={"status": "error", "error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)