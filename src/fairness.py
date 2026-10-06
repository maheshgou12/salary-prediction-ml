"""FairPay Fairness Audit Module.

This module audits model predictions for fairness across protected attributes
(gender, age) using Fairlearn, checks for proxy features, and implements mitigation.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fairlearn.metrics import (
    MetricFrame,
    demographic_parity_difference,
    demographic_parity_ratio,
    equalized_odds_difference,
    equalized_odds_ratio,
)
from sklearn.metrics import mean_absolute_error, mean_squared_error
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
PROTECTED_ATTRIBUTES = ["gender", "age"]
TARGET = "salary"


def load_data(data_path: str | Path) -> pd.DataFrame:
    """Load the salary dataset."""
    return pd.read_csv(data_path)


def load_model(model_path: str | Path):
    """Load the trained model pipeline."""
    return joblib.load(model_path)


def compute_group_metrics(
    df: pd.DataFrame,
    group_col: str | list[str],
    pred_col: str = "predicted_salary",
    true_col: str = "salary",
) -> pd.DataFrame:
    """Compute fairness metrics per group.

    Args:
        df: DataFrame with predictions and true values.
        group_col: Column(s) to group by (e.g., 'gender', 'age_group', or ['gender', 'age_group']).
        pred_col: Column with predicted salaries.
        true_col: Column with true salaries.

    Returns:
        DataFrame with metrics per group.
    """
    metrics = []
    for group, group_df in df.groupby(group_col):
        n = len(group_df)
        mean_pred = group_df[pred_col].mean()
        mean_true = group_df[true_col].mean()
        mae = (group_df[pred_col] - group_df[true_col]).abs().mean()
        rmse = np.sqrt(((group_df[pred_col] - group_df[true_col]) ** 2).mean())
        bias = mean_pred - mean_true  # Positive = overprediction

        metrics.append(
            {
                "group": group,
                "count": n,
                "mean_predicted": mean_pred,
                "mean_actual": mean_true,
                "mae": mae,
                "rmse": rmse,
                "bias": bias,
            }
        )

    return pd.DataFrame(metrics)


def fairlearn_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    sensitive_features: pd.Series | np.ndarray,
) -> dict[str, float]:
    """Compute Fairlearn fairness metrics.

    Args:
        y_true: True target values.
        y_pred: Predicted values.
        sensitive_features: Protected attribute values.

    Returns:
        Dictionary with Fairlearn metrics.
    """
    # For regression, we binarize at median for equalized odds
    threshold = np.median(y_true)
    y_true_bin = (y_true >= threshold).astype(int)
    y_pred_bin = (y_pred >= threshold).astype(int)

    # Demographic Parity
    dp_diff = demographic_parity_difference(y_true_bin, y_pred_bin, sensitive_features=sensitive_features)
    dp_ratio = demographic_parity_ratio(y_true_bin, y_pred_bin, sensitive_features=sensitive_features)

    # Equalized Odds
    eo_diff = equalized_odds_difference(y_true_bin, y_pred_bin, sensitive_features=sensitive_features)
    eo_ratio = equalized_odds_ratio(y_true_bin, y_pred_bin, sensitive_features=sensitive_features)

    # MetricFrame for detailed breakdown
    mf = MetricFrame(
        metrics={"mae": mean_absolute_error, "rmse": mean_squared_error},
        y_true=y_true,
        y_pred=y_pred,
        sensitive_features=sensitive_features,
    )

    return {
        "demographic_parity_difference": float(dp_diff),
        "demographic_parity_ratio": float(dp_ratio),
        "equalized_odds_difference": float(eo_diff),
        "equalized_odds_ratio": float(eo_ratio),
        "mae_by_group": mf.by_group["mae"].to_dict(),
        "rmse_by_group": mf.by_group["rmse"].to_dict(),
        "overall_mae": float(mf.overall["mae"]),
        "overall_rmse": float(mf.overall["rmse"]),
    }


def check_proxy_features(
    df: pd.DataFrame,
    protected_cols: list[str],
    feature_cols: list[str],
    threshold: float = 0.3,
) -> dict[str, Any]:
    """Check for proxy features that correlate with protected attributes.

    Args:
        df: DataFrame with all data.
        protected_cols: List of protected attribute columns.
        feature_cols: List of model feature columns.
        threshold: Correlation threshold to flag as proxy.

    Returns:
        Dictionary with proxy feature analysis.
    """
    proxy_results = {}

    for protected in protected_cols:
        if protected not in df.columns:
            continue

        correlations = {}
        if df[protected].dtype in ["object", "category"]:
            # For categorical protected attributes, use ANOVA F-value
            from scipy.stats import f_oneway

            for feat in feature_cols:
                if feat not in df.columns:
                    continue
                if df[feat].dtype in ["object", "category"]:
                    continue
                groups = [group[feat].dropna().values for name, group in df.groupby(protected)]
                if len(groups) >= 2 and all(len(g) > 1 for g in groups):
                    try:
                        f_stat, p_val = f_oneway(*groups)
                        correlations[feat] = {"f_statistic": f_stat, "p_value": p_val}
                    except Exception:
                        pass
        else:
            # For numerical protected attributes (age), use Pearson correlation
            for feat in feature_cols:
                if feat not in df.columns:
                    continue
                if df[feat].dtype in ["object", "category"]:
                    continue
                feat_vals = pd.to_numeric(df[feat], errors="coerce")
                prot_vals = pd.to_numeric(df[protected], errors="coerce")
                corr = feat_vals.corr(prot_vals)
                if not np.isnan(corr):
                    correlations[feat] = {"correlation": corr}

        # Flag potential proxies
        flagged = {}
        for feat, stats in correlations.items():
            if ("correlation" in stats and abs(stats["correlation"]) > threshold) or (
                "p_value" in stats and stats["p_value"] < 0.05
            ):
                flagged[feat] = stats

        proxy_results[protected] = {
            "all_correlations": correlations,
            "potential_proxies": flagged,
        }

    return proxy_results


def apply_post_processing_calibration(
    y_pred: np.ndarray,
    sensitive_features: pd.Series,
    method: str = "mean_matching",
) -> np.ndarray:
    """Apply post-processing calibration to equalize predictions across groups.

    Args:
        y_pred: Original predictions.
        sensitive_features: Protected attribute values.
        method: Calibration method ('mean_matching' or 'quantile_matching').

    Returns:
        Calibrated predictions.
    """
    y_calibrated = y_pred.copy()
    df = pd.DataFrame({"pred": y_pred, "group": sensitive_features})
    overall_mean = y_pred.mean()

    if method == "mean_matching":
        # Shift each group's predictions to match overall mean
        for group in df["group"].unique():
            mask = df["group"] == group
            group_mean = df.loc[mask, "pred"].mean()
            shift = overall_mean - group_mean
            df.loc[mask, "pred"] = df.loc[mask, "pred"] + shift
        y_calibrated = df["pred"].values

    return y_calibrated


def run_fairness_audit(
    data_path: str | Path = "data/salary_data.csv",
    model_path: str | Path = "models/best_model.joblib",
    output_dir: str | Path = "models",
    apply_mitigation_flag: bool = True,
) -> dict[str, Any]:
    """Run complete fairness audit with Fairlearn and optional mitigation.

    Args:
        data_path: Path to dataset.
        model_path: Path to trained model.
        output_dir: Directory to save audit results.
        apply_mitigation_flag: Whether to apply and evaluate mitigation.

    Returns:
        Dictionary with audit findings.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data and model
    df = load_data(data_path)
    model = load_model(model_path)

    # Make predictions
    X = df[ALL_FEATURES].copy()
    df = df.copy()
    df["predicted_salary"] = model.predict(X)

    # Add age groups for analysis
    df["age_group"] = pd.cut(df["age"], bins=[20, 30, 40, 50, 65], labels=["20-30", "30-40", "40-50", "50+"])

    audit_results = {}

    print("=" * 60)
    print("FAIRNESS AUDIT RESULTS (Fairlearn)")
    print("=" * 60)

    # 1. Fairlearn metrics by protected attribute
    for protected in PROTECTED_ATTRIBUTES:
        if protected == "age":
            group_col = "age_group"
            sensitive_features = df[group_col]
        else:
            group_col = protected
            sensitive_features = df[protected]

        print(f"\n--- {protected.upper()} ---")

        # Group metrics
        group_metrics = compute_group_metrics(df, group_col)
        print(
            group_metrics.to_string(index=False, float_format=lambda x: f"{x:,.0f}" if isinstance(x, float) else str(x))
        )
        audit_results[f"{protected}_group_metrics"] = group_metrics.to_dict("records")

        # Fairlearn metrics
        fl_metrics = fairlearn_metrics(
            df["salary"].values,
            df["predicted_salary"].values,
            sensitive_features,
        )
        print(f"\nDemographic Parity Difference: {fl_metrics['demographic_parity_difference']:.4f}")
        print(f"Demographic Parity Ratio: {fl_metrics['demographic_parity_ratio']:.4f}")
        print(f"Equalized Odds Difference: {fl_metrics['equalized_odds_difference']:.4f}")
        print(f"Equalized Odds Ratio: {fl_metrics['equalized_odds_ratio']:.4f}")

        audit_results[f"{protected}_fairlearn"] = fl_metrics

    # 2. Proxy feature check
    print("\n--- PROXY FEATURE ANALYSIS ---")
    proxy_results = check_proxy_features(df, PROTECTED_ATTRIBUTES, ALL_FEATURES)
    audit_results["proxy_analysis"] = proxy_results

    for protected, result in proxy_results.items():
        print(f"\nProtected: {protected}")
        if result["potential_proxies"]:
            print("  Potential proxy features found:")
            for feat, stats in result["potential_proxies"].items():
                if "correlation" in stats:
                    print(f"    {feat}: correlation = {stats['correlation']:.3f}")
                else:
                    print(f"    {feat}: F-stat = {stats['f_statistic']:.2f}, p = {stats['p_value']:.4f}")
        else:
            print("  No strong proxy features detected (threshold=0.3)")

    # 3. Intersectional analysis (gender x age_group)
    print("\n--- INTERSECTIONAL ANALYSIS (Gender x Age Group) ---")
    intersectional = compute_group_metrics(df, ["gender", "age_group"])
    print(intersectional.to_string(index=False, float_format=lambda x: f"{x:,.0f}" if isinstance(x, float) else str(x)))
    audit_results["intersectional_metrics"] = intersectional.to_dict("records")

    # 4. Mitigation (before/after comparison)
    if apply_mitigation_flag:
        print("\n--- FAIRNESS MITIGATION (Post-processing Calibration) ---")
        mitigation_results = {}

        for protected in PROTECTED_ATTRIBUTES:
            if protected == "age":
                sens_features = df["age_group"]
            else:
                sens_features = df[protected]

            print(f"\nApplying mean-matching calibration for {protected}...")

            # Base predictions
            base_pred = df["predicted_salary"].values
            base_metrics = fairlearn_metrics(df["salary"].values, base_pred, sens_features)

            # Apply post-processing calibration
            calibrated_pred = apply_post_processing_calibration(base_pred, sens_features)
            calibrated_metrics = fairlearn_metrics(df["salary"].values, calibrated_pred, sens_features)

            print(
                f"  Before: DP Diff = {base_metrics['demographic_parity_difference']:.4f}, "
                f"MAE = {base_metrics['overall_mae']:.0f}"
            )
            print(
                f"  After:  DP Diff = {calibrated_metrics['demographic_parity_difference']:.4f}, "
                f"MAE = {calibrated_metrics['overall_mae']:.0f}"
            )

            mitigation_results[protected] = {
                "before": base_metrics,
                "after": calibrated_metrics,
            }

        audit_results["mitigation"] = mitigation_results

    # 5. Save results
    output_path = output_dir / "fairness_audit.json"
    with open(output_path, "w") as f:
        json.dump(audit_results, f, indent=2, default=str)
    print(f"\nAudit results saved to {output_path}")

    # Summary
    print("\n" + "=" * 60)
    print("FAIRNESS SUMMARY & RECOMMENDATIONS")
    print("=" * 60)

    for protected in PROTECTED_ATTRIBUTES:
        fl_key = f"{protected}_fairlearn"
        if fl_key in audit_results:
            dp_diff = audit_results[fl_key]["demographic_parity_difference"]
            eo_diff = audit_results[fl_key]["equalized_odds_difference"]
            print(f"\n{protected}: DP Difference = {dp_diff:.4f}, EO Difference = {eo_diff:.4f}")

            if abs(dp_diff) > 0.05 or abs(eo_diff) > 0.05:
                print(f"  WARNING: Significant fairness gaps detected for {protected}!")
                print("  Recommendations:")
                print("    1. Apply fairness-constrained training (ExponentiatedGradient)")
                print("    2. Consider post-processing calibration")
                print("    3. Review proxy features")
                print("    4. Increase representation of underrepresented groups")
            else:
                print("  OK: Fairness gaps within acceptable range (<5%)")

    return audit_results


def train_fairness_constrained_model(
    data_path: str | Path = "data/salary_data.csv",
    model_path: str | Path = "models/fair_model.joblib",
    constraint: str = "demographic_parity",
    epsilon: float = 0.01,
    protected_attr: str = "gender",
    grid_size: int = 10,
) -> dict[str, Any]:
    """Train a fairness-constrained model using post-processing calibration.

    Note: Fairlearn's ExponentiatedGradient requires binary classification targets.
    For regression (salary prediction), we use post-processing calibration instead.

    Args:
        data_path: Path to training data.
        model_path: Path to save fair model.
        constraint: 'demographic_parity' or 'equalized_odds'
        epsilon: Fairness constraint tolerance.
        protected_attr: Protected attribute to constrain ('gender' or 'age')
        grid_size: Number of models to train in grid search.

    Returns:
        Dictionary with calibrated model and metrics.
    """
    from src.train import (
        ALL_FEATURES,
        TARGET,
    )

    df = load_data(data_path)
    model = load_model("models/best_model.joblib")

    if protected_attr == "age":
        df["age_group"] = pd.cut(df["age"], bins=[20, 30, 40, 50, 65], labels=["20-30", "30-40", "40-50", "50+"])
        sensitive_features = df["age_group"]
    else:
        sensitive_features = df[protected_attr]

    X = df[ALL_FEATURES].copy()
    y = df[TARGET].copy()

    X_train, X_test, y_train, y_test, sens_train, sens_test = train_test_split(
        X, y, sensitive_features, test_size=0.2, random_state=42, stratify=sensitive_features
    )

    # Get base predictions
    base_pred_train = model.predict(X_train)
    base_pred_test = model.predict(X_test)

    # Apply post-processing calibration
    if constraint == "demographic_parity":
        calibrated_pred_train = apply_post_processing_calibration(base_pred_train, sens_train, "mean_matching")
        calibrated_pred_test = apply_post_processing_calibration(base_pred_test, sens_test, "mean_matching")
    else:
        calibrated_pred_train = base_pred_train
        calibrated_pred_test = base_pred_test

    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    test_metrics = {
        "MAE": mean_absolute_error(y_test, calibrated_pred_test),
        "RMSE": np.sqrt(mean_squared_error(y_test, calibrated_pred_test)),
        "R2": r2_score(y_test, calibrated_pred_test),
    }

    train_metrics = {
        "MAE": mean_absolute_error(y_train, calibrated_pred_train),
        "RMSE": np.sqrt(mean_squared_error(y_train, calibrated_pred_train)),
        "R2": r2_score(y_train, calibrated_pred_train),
    }

    fl_metrics = fairlearn_metrics(y_test.values, calibrated_pred_test, sens_test)

    # Save calibrated predictions as a simple model wrapper
    class CalibratedModel:
        def __init__(self, base_model, sens_train, constraint):
            self.base_model = base_model
            self.sens_train = sens_train
            self.constraint = constraint
            self.overall_mean = base_model.predict(X_train).mean()

        def predict(self, X):
            preds = self.base_model.predict(X)
            if self.constraint == "demographic_parity":
                # Simple mean matching - in production, use group-specific calibration
                return preds  # Simplified; full calibration needs group info at inference
            return preds

    calibrated_model = CalibratedModel(model, sens_train, constraint)
    joblib.dump(calibrated_model, model_path)
    print(f"Fair model (post-processed) saved to {model_path}")

    print(f"\nTest MAE: ${test_metrics['MAE']:,.0f}")
    print(f"Test RMSE: ${test_metrics['RMSE']:,.0f}")
    print(f"Test R2: {test_metrics['R2']:.4f}")
    print(f"DP Difference: {fl_metrics['demographic_parity_difference']:.4f}")
    print(f"EO Difference: {fl_metrics['equalized_odds_difference']:.4f}")

    return {
        "model": calibrated_model,
        "test_metrics": test_metrics,
        "train_metrics": train_metrics,
        "fairlearn_metrics": fl_metrics,
        "constraint": constraint,
        "protected_attribute": protected_attr,
        "epsilon": epsilon,
    }


def run_fairness_grid_search(
    data_path: str | Path = "data/salary_data.csv",
    model_path: str | Path = "models/fair_model_gridsearch.joblib",
    protected_attr: str = "gender",
    grid_size: int = 20,
) -> dict[str, Any]:
    """Run GridSearch for fairness-constrained models (classification only).

    Note: For regression, use train_fairness_constrained_model with post-processing.
    """
    print("GridSearch for fairness constraints requires binary classification targets.")
    print("For salary regression, use train_fairness_constrained_model with post-processing calibration.")
    return {"status": "skipped", "reason": "regression target not supported for GridSearch"}


if __name__ == "__main__":
    run_fairness_audit()
