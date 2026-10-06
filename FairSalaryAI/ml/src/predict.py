"""FairSalary AI - Prediction Interface"""
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# Feature configuration
NUMERICAL_FEATURES = [
    'years_experience',
    'skills_count',
    'previous_salary',
    'interview_score',
]

CATEGORICAL_FEATURES = [
    'education_level',
    'job_role',
    'location',
    'company_size',
]

ALL_FEATURES = [
    'years_experience', 'skills_count', 'previous_salary', 'interview_score',
    'education_level', 'job_role', 'location', 'company_size'
]
TARGET = 'salary'


def load_model(model_path: str | Path):
    """Load the trained model pipeline."""
    return joblib.load(model_path)


def predict_salary(
    model,
    candidate_data: Dict[str, Any],
    conformal_q: Optional[float] = None,
) -> Tuple[float, float, float, float]:
    """Make salary prediction with optional conformal prediction interval.

    Args:
        model: Trained pipeline.
        candidate_data: Dictionary with candidate features.
        conformal_q: Optional conformal quantile for prediction intervals.

    Returns:
        Tuple of (predicted_salary, lower_bound, upper_bound, confidence).
    """
    X = pd.DataFrame([candidate_data])[ALL_FEATURES]
    prediction = float(model.predict(X)[0])

    if conformal_q is not None:
        # Use conformal prediction interval
        lower = max(0, prediction - conformal_q)
        upper = prediction + conformal_q
        confidence = 0.90  # Assuming alpha=0.1
    else:
        # Fallback: Use RMSE-based interval
        rmse = 22651  # Default from training
        margin = 1.96 * rmse
        lower = max(0, prediction - margin)
        upper = prediction + margin
        confidence = 0.95

    return prediction, lower, upper, confidence


def predict_batch(
    model,
    candidates: List[Dict[str, Any]],
    conformal_q: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Make batch salary predictions.

    Args:
        model: Trained pipeline.
        candidates: List of candidate feature dictionaries.
        conformal_q: Optional conformal quantile.

    Returns:
        List of prediction results.
    """
    X = pd.DataFrame(candidates)[ALL_FEATURES]
    predictions = model.predict(X)

    if conformal_q is not None:
        margin = conformal_q
        confidence = 0.90
    else:
        rmse = 22651
        margin = 1.96 * rmse
        confidence = 0.95

    results = []
    for i, pred in enumerate(predictions):
        pred_val = float(pred)
        lower = max(0, pred_val - margin)
        upper = pred_val + margin
        results.append({
            'predicted_salary': int(round(pred_val)),
            'minimum_salary': int(round(lower)),
            'maximum_salary': int(round(upper)),
            'confidence': confidence,
            'input_data': candidates[i],
        })

    return results


def load_conformal_quantile(path: str | Path) -> Optional[float]:
    """Load conformal quantile from summary file."""
    try:
        with open(path) as f:
            summary = json.load(f)
        return summary.get('q_hat')
    except Exception:
        return None


def run_prediction(
    candidate_data: Dict[str, Any],
    model_path: str | Path = 'ml/models/best_model.joblib',
    conformal_path: str | Path = 'ml/models/conformal_summary.json',
) -> Dict[str, Any]:
    """Run a single salary prediction."""
    model = load_model(model_path)
    conformal_q = load_conformal_quantile(conformal_path)

    predicted, lower, upper, confidence = predict_salary(model, candidate_data, conformal_q)

    result = {
        'predicted_salary': int(round(predicted)),
        'minimum_salary': int(round(lower)),
        'maximum_salary': int(round(upper)),
        'confidence': confidence,
        'model_version': '1.0.0',
        'fairness_disclaimer': (
            "This prediction was made without using protected attributes "
            "(gender, age). The model was audited for demographic parity "
            "across protected groups. Fairness analysis did not identify "
            "a significant disparity under the selected metrics. "
            "This tool provides recommendations, not binding decisions."
        ),
    }

    return result


def load_model(model_path: str | Path):
    """Load the trained model pipeline."""
    return joblib.load(model_path)


if __name__ == '__main__':
    # Example usage
    candidate = {
        'years_experience': 5.0,
        'education_level': "Bachelor's Degree",
        'skills_count': 5,
        'job_role': 'Software Engineer',
        'location': 'San Francisco',
        'company_size': 'Large (1000+)',
        'previous_salary': 120000,
        'interview_score': 7.5,
    }

    result = run_prediction(candidate)
    print(json.dumps(result, indent=2))