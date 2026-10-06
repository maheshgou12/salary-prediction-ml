# FairSalary AI - Prediction Service
import os
import json
import warnings
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from app.config import settings

warnings.filterwarnings("ignore")


class PredictionService:
    """Service for making salary predictions using the trained model."""

    def __init__(self):
        self.model = None
        self.model_metadata = {}
        self._load_model()

    def _load_model(self) -> None:
        """Load the trained model pipeline and metadata."""
        model_path = settings.MODEL_PATH
        metadata_path = settings.MODEL_METADATA_PATH

        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
        else:
            raise FileNotFoundError(f"Model not found at {model_path}")

        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                self.model_metadata = json.load(f)
        else:
            self.model_metadata = {
                "version": settings.MODEL_VERSION,
                "model_type": "Unknown",
                "metrics": {}
            }

    def predict(
        self,
        candidate_data: Dict[str, Any]
    ) -> Tuple[float, float, float, float]:
        """
        Make a salary prediction with confidence interval.

        Returns:
            Tuple of (predicted_salary, min_salary, max_salary, confidence)
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        # Prepare input data
        X = self._prepare_input(candidate_data)

        # Make prediction
        predicted_salary = float(self.model.predict(X)[0])

        # Calculate prediction interval using conformal prediction or RMSE
        min_salary, max_salary, confidence = self._calculate_interval(predicted_salary)

        return predicted_salary, min_salary, max_salary, confidence

    def _prepare_input(self, candidate_data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare input data for the model."""
        # Convert to DataFrame with correct column order
        # The model's preprocessor expects specific columns
        df = pd.DataFrame([candidate_data])

        # Ensure all required columns are present
        required_columns = [
            "experience_years", "education", "job_role", "location",
            "skills", "industry", "company_size", "employment_type"
        ]

        for col in required_columns:
            if col not in df.columns:
                df[col] = ""

        # Handle skills - convert list to count or keep as-is depending on model
        if "skills" in df.columns:
            if isinstance(df["skills"].iloc[0], list):
                df["skills_count"] = df["skills"].apply(len)
            else:
                df["skills_count"] = 1

        return df

    def _calculate_interval(
        self, predicted_salary: float
    ) -> Tuple[float, float, float]:
        """Calculate prediction interval."""
        # Try to load conformal prediction quantile
        conformal_path = "ml/models/conformal_summary.json"
        if os.path.exists(conformal_path):
            with open(conformal_path, "r") as f:
                conformal = json.load(f)
            q_hat = conformal.get("q_hat", 22333)
            alpha = conformal.get("alpha", 0.1)
            confidence = 1 - alpha
        else:
            # Fallback: use RMSE-based interval
            q_hat = 22333  # Default from training
            confidence = 0.90

        min_salary = max(0, predicted_salary - q_hat)
        max_salary = predicted_salary + q_hat

        return min_salary, max_salary, confidence

    def get_explanation(
        self, candidate_data: Dict[str, Any], top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate SHAP-based explanation for a prediction."""
        if not settings.ENABLE_SHAP_EXPLANATIONS:
            return []

        try:
            import shap

            X = self._prepare_input(candidate_data)

            # Get preprocessor and model from pipeline
            if hasattr(self.model, "named_steps"):
                preprocessor = self.model.named_steps["preprocessor"]
                regressor = self.model.named_steps["model"]
            else:
                return []

            X_transformed = preprocessor.transform(X)

            # Get feature names after encoding
            cat_encoder = preprocessor.named_transformers_["cat"].named_steps["encoder"]
            cat_features = cat_encoder.get_feature_names_out(
                preprocessor.transformers_[1][2]
            ).tolist()
            num_features = preprocessor.transformers_[0][2]
            feature_names = list(num_features) + cat_features

            # Create explainer
            if hasattr(regressor, "coef_"):
                explainer = shap.LinearExplainer(regressor, X_transformed)
            elif hasattr(regressor, "tree_"):
                explainer = shap.TreeExplainer(regressor, X_transformed)
            else:
                # Ensemble or other - use KernelExplainer with small background
                def predict_fn(X_raw):
                    return self.model.predict(X_raw)
                background = X_transformed[:min(10, len(X_transformed))]
                explainer = shap.KernelExplainer(predict_fn, background)

            shap_values = explainer.shap_values(X_transformed)
            if isinstance(shap_values, list):
                shap_values = shap_values[0]
            if shap_values.ndim > 1:
                shap_values = shap_values[0]

            # Create explanation dataframe
            exp_df = pd.DataFrame({
                "feature": feature_names,
                "shap_value": shap_values,
            })
            exp_df["abs_shap"] = exp_df["shap_value"].abs()
            exp_df = exp_df.sort_values("abs_shap", ascending=False).head(top_k)

            explanations = []
            for _, row in exp_df.iterrows():
                explanations.append({
                    "feature": row["feature"],
                    "contribution": int(round(row["shap_value"])),
                    "direction": "positive" if row["shap_value"] > 0 else "negative"
                })

            return explanations

        except Exception as e:
            # Return empty explanation if SHAP fails
            return []

    def find_similar_profiles(
        self, candidate_data: Dict[str, Any], n: int = 5
    ) -> Dict[str, Any]:
        """Find similar historical profiles and their salary statistics."""
        if not settings.ENABLE_SIMILAR_PROFILES:
            return {"count": 0, "median_salary": 0, "percentile_25": 0, "percentile_75": 0}

        try:
            from app.database import get_db_context
            from app.models import CandidateProfile

            with get_db_context() as db:
                # Build query for similar profiles
                query = db.query(CandidateProfile.salary)

                # Filter by job role (most important)
                query = query.filter(CandidateProfile.job_role == candidate_data["job_role"])

                # Filter by location if possible
                query = query.filter(CandidateProfile.location == candidate_data["location"])

                # Filter by experience range (±2 years)
                exp = candidate_data["experience_years"]
                query = query.filter(
                    CandidateProfile.experience_years.between(exp - 2, exp + 2)
                )

                # Filter by education
                query = query.filter(CandidateProfile.education == candidate_data["education"])

                salaries = [row[0] for row in query.all()]

                if len(salaries) < 5:
                    # Fallback: just job role
                    query = db.query(CandidateProfile.salary).filter(
                        CandidateProfile.job_role == candidate_data["job_role"]
                    )
                    salaries = [row[0] for row in query.all()]

                if not salaries:
                    return {"count": 0, "median_salary": 0, "percentile_25": 0, "percentile_75": 0}

                salaries = np.array(salaries)
                return {
                    "count": len(salaries),
                    "median_salary": int(np.median(salaries)),
                    "percentile_25": int(np.percentile(salaries, 25)),
                    "percentile_75": int(np.percentile(salaries, 75))
                }

        except Exception:
            return {"count": 0, "median_salary": 0, "percentile_25": 0, "percentile_75": 0}

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "version": self.model_metadata.get("version", settings.MODEL_VERSION),
            "model_type": self.model_metadata.get("model_type", "Unknown"),
            "metrics": self.model_metadata.get("metrics", {}),
            "fairness_metrics": self.model_metadata.get("fairness_metrics", {}),
            "features": self.model_metadata.get("features", [])
        }


# Global instance
prediction_service = PredictionService()