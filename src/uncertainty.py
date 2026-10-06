"""FairPay Uncertainty Quantification Module.

This module implements conformal prediction for statistically rigorous
prediction intervals on salary predictions.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

# Feature configuration
NUMERICAL_FEATURES = [
    "years_experience",
    "skills_count",
    "previous_salary",
    "interview_score",
]

CATEGORICAL_FEATURES = [
    "education_level",
    "job_role",
    "location",
    "company_size",
]

ALL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
TARGET = "salary"


def load_data(data_path: str | Path) -> pd.DataFrame:
    """Load the salary dataset."""
    return pd.read_csv(data_path)


def load_model(model_path: str | Path):
    """Load the trained model pipeline."""
    return joblib.load(model_path)


class ConformalPredictor:
    """Conformal Prediction for regression using split conformal method.

    Provides distribution-free prediction intervals with finite-sample
    coverage guarantees.
    """

    def __init__(self, model: Any, alpha: float = 0.1):
        """Initialize conformal predictor.

        Args:
            model: Fitted sklearn pipeline with predict method.
            alpha: Miscoverage level (1 - alpha = coverage level).
                   alpha=0.1 gives 90% coverage, alpha=0.05 gives 95% coverage.
        """
        self.model = model
        self.alpha = alpha
        self.calibration_scores: np.ndarray | None = None
        self.q_hat: float | None = None

    def calibrate(self, X_cal: pd.DataFrame, y_cal: pd.Series) -> float:
        """Calibrate conformal predictor on calibration set.

        Args:
            X_cal: Calibration features.
            y_cal: Calibration targets.

        Returns:
            The conformal quantile (q_hat).
        """
        y_pred_cal = self.model.predict(X_cal)
        residuals = np.abs(y_cal.values - y_pred_cal)
        self.calibration_scores = residuals

        # Compute conformal quantile (1 - alpha)(1 + 1/n) quantile
        n = len(residuals)
        q_level = np.ceil((n + 1) * (1 - self.alpha)) / n
        self.q_hat = np.quantile(residuals, q_level, method="higher")

        return float(self.q_hat)

    def predict_interval(self, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predict with conformal prediction intervals.

        Args:
            X: Features to predict on.

        Returns:
            Tuple of (predictions, lower_bounds, upper_bounds).
        """
        if self.q_hat is None:
            raise ValueError("Must call calibrate() before predict_interval()")

        y_pred = self.model.predict(X)
        lower = y_pred - self.q_hat
        upper = y_pred + self.q_hat

        return y_pred, lower, upper

    def evaluate_coverage(self, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, float]:
        """Evaluate actual coverage on test set.

        Args:
            X_test: Test features.
            y_test: Test targets.

        Returns:
            Dictionary with coverage metrics.
        """
        y_pred, lower, upper = self.predict_interval(X_test)
        coverage = np.mean((y_test.values >= lower) & (y_test.values <= upper))
        avg_width = np.mean(upper - lower)

        return {
            "nominal_coverage": 1 - self.alpha,
            "actual_coverage": float(coverage),
            "coverage_gap": float(coverage - (1 - self.alpha)),
            "avg_interval_width": float(avg_width),
            "q_hat": float(self.q_hat or 0.0),
        }


def run_conformal_prediction(
    data_path: str | Path = "data/salary_data.csv",
    model_path: str | Path = "models/best_model.joblib",
    output_dir: str | Path = "models",
    alpha: float = 0.1,
    cal_size: float = 0.2,
) -> dict[str, Any]:
    """Run conformal prediction calibration and evaluation.

    Args:
        data_path: Path to dataset.
        model_path: Path to trained model.
        output_dir: Directory to save results.
        alpha: Miscoverage level (default 0.1 for 90% coverage).
        cal_size: Fraction of data to use for calibration.

    Returns:
        Dictionary with calibration and evaluation results.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data and model
    df = load_data(data_path)
    model = load_model(model_path)

    # Split data: train (already used), calibration, test
    X = df[ALL_FEATURES].copy()
    y = df[TARGET].copy()

    # Use a separate calibration set (not used in training)
    # First split off test set
    X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    # Then split temp into train and calibration
    X_train, X_cal, y_train, y_cal = train_test_split(X_temp, y_temp, test_size=cal_size / 0.8, random_state=42)

    print(f"Data splits: Train={len(X_train)}, Calibration={len(X_cal)}, Test={len(X_test)}")

    # Create and calibrate conformal predictor
    conformal = ConformalPredictor(model, alpha=alpha)
    q_hat = conformal.calibrate(X_cal, y_cal)

    print(f"\nConformal Quantile (q_hat): ${q_hat:,.0f}")
    print(f"Nominal Coverage: {1 - alpha:.0%}")

    # Evaluate on test set
    test_results = conformal.evaluate_coverage(X_test, y_test)
    print(f"Actual Coverage: {test_results['actual_coverage']:.1%}")
    print(f"Coverage Gap: {test_results['coverage_gap']:.3f}")
    print(f"Avg Interval Width: ${test_results['avg_interval_width']:,.0f}")

    # Evaluate on calibration set (should be close to nominal)
    cal_results = conformal.evaluate_coverage(X_cal, y_cal)
    print(f"\nCalibration Set Coverage: {cal_results['actual_coverage']:.1%}")

    # Generate predictions with intervals for test set
    y_pred, lower, upper = conformal.predict_interval(X_test)
    test_df = X_test.copy()
    test_df["actual_salary"] = y_test.values
    test_df["predicted_salary"] = y_pred
    test_df["lower_bound"] = lower
    test_df["upper_bound"] = upper
    test_df["interval_width"] = upper - lower
    test_df["covered"] = (test_df["actual_salary"] >= lower) & (test_df["actual_salary"] <= upper)

    # Save detailed results
    test_df.to_csv(output_dir / "conformal_predictions.csv", index=False)

    # Save summary
    summary = {
        "alpha": alpha,
        "nominal_coverage": 1 - alpha,
        "q_hat": float(q_hat),
        "calibration_size": len(X_cal),
        "test_size": len(X_test),
        "calibration_coverage": cal_results["actual_coverage"],
        "test_coverage": test_results["actual_coverage"],
        "test_coverage_gap": test_results["coverage_gap"],
        "avg_interval_width": test_results["avg_interval_width"],
    }

    import json

    with open(output_dir / "conformal_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults saved to {output_dir}")
    print("  - conformal_summary.json")
    print("  - conformal_predictions.csv")

    return summary


if __name__ == "__main__":
    run_conformal_prediction()
