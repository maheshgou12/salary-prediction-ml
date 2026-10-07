# FairSalary AI - Fairness Service
import warnings
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from app.config import settings, PROJECT_ROOT

warnings.filterwarnings("ignore")


class FairnessService:
    """Service for fairness analysis using Fairlearn."""

    def __init__(self):
        self.fairness_data = None
        self._load_fairness_data()

    def _load_fairness_data(self) -> None:
        """Load precomputed fairness analysis results."""
        import os
        import json

        fairness_path = str(PROJECT_ROOT / "ml" / "models" / "fairness_audit.json")
        if os.path.exists(fairness_path):
            with open(fairness_path, "r") as f:
                self.fairness_data = json.load(f)

    def get_fairness_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive fairness dashboard data."""
        if not self.fairness_data:
            return self._empty_dashboard()

        from datetime import datetime
        dashboard = {
            "overall_status": "PASS",
            "model_version": "1.0.0",
            "protected_attributes": [],
            "recommendations": [],
            "generated_at": datetime.utcnow().isoformat()
        }

        for attr in ["gender", "age"]:
            if f"{attr}_fairlearn" in self.fairness_data:
                attr_report = self._analyze_attribute(attr)
                dashboard["protected_attributes"].append(attr_report)

                if attr_report["status"] in ["REVIEW", "WARNING"]:
                    dashboard["overall_status"] = "REVIEW"
                    dashboard["recommendations"].extend(attr_report["recommendations"])

        return dashboard

    def _analyze_attribute(self, attribute: str) -> Dict[str, Any]:
        """Analyze fairness for a single protected attribute."""
        fl_key = f"{attribute}_fairlearn"
        group_key = f"{attribute}_group_metrics"

        fl_data = self.fairness_data.get(fl_key, {})
        group_data = self.fairness_data.get(group_key, [])

        dp_diff = fl_data.get("demographic_parity_difference", 0)
        mean_diff = fl_data.get("mean_prediction_difference", 0)
        mae_by_group = fl_data.get("mae_by_group", {})
        rmse_by_group = fl_data.get("rmse_by_group", {})

        # Determine status
        status = "PASS"
        if abs(dp_diff) > 0.1 or abs(mean_diff) > 50000:
            status = "WARNING"
        elif abs(dp_diff) > 0.05 or abs(mean_diff) > 20000:
            status = "REVIEW"

        # Group metrics
        groups = []
        for g in group_data:
            groups.append({
                "group": str(g.get("group", "Unknown")),
                "count": g.get("count", 0),
                "mean_predicted": g.get("mean_predicted", 0),
                "mean_actual": g.get("mean_actual"),
                "mae": g.get("mae"),
                "rmse": g.get("rmse"),
                "bias": g.get("bias", 0)
            })

        # Recommendations
        recommendations = []
        if status != "PASS":
            recommendations.append(
                f"Review {attribute} fairness: DP difference = {dp_diff:.3f}"
            )
            if abs(dp_diff) > 0.1:
                recommendations.append(
                    f"Consider post-processing calibration for {attribute}"
                )

        return {
            "attribute": attribute,
            "status": status,
            "demographic_parity_difference": dp_diff,
            "mean_prediction_difference": mean_diff,
            "mae_by_group": mae_by_group,
            "rmse_by_group": rmse_by_group,
            "groups": groups,
            "recommendations": recommendations
        }

    def get_group_metrics(self, attribute: str) -> List[Dict[str, Any]]:
        """Get detailed metrics for a specific protected attribute."""
        if not self.fairness_data:
            return []

        group_key = f"{attribute}_group_metrics"
        return self.fairness_data.get(group_key, [])

    def get_intersectional_analysis(self) -> List[Dict[str, Any]]:
        """Get intersectional fairness analysis (gender × age)."""
        if not self.fairness_data:
            return []

        return self.fairness_data.get("intersectional_metrics", [])

    def get_proxy_analysis(self) -> Dict[str, Any]:
        """Get proxy feature analysis results."""
        if not self.fairness_data:
            return {}

        return self.fairness_data.get("proxy_analysis", {})

    def _empty_dashboard(self) -> Dict[str, Any]:
        return {
            "overall_status": "UNKNOWN",
            "model_version": "1.0.0",
            "protected_attributes": [],
            "recommendations": [
                "Run fairness analysis to generate dashboard"
            ],
            "generated_at": None
        }


# Global instance
fairness_service = FairnessService()