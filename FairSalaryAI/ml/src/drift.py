"""FairSalary AI - Data Drift Detection"""
import json
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import ks_2samp, chi2_contingency

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


def load_data(data_path: str | Path) -> pd.DataFrame:
    """Load the salary dataset."""
    return pd.read_csv(data_path)


def load_model(model_path: str | Path):
    """Load the trained model pipeline."""
    return joblib.load(model_path)


def population_stability_index(
    expected: np.ndarray,
    actual: np.ndarray,
    bins: int = 10,
) -> float:
    """Calculate Population Stability Index (PSI) between two distributions.

    PSI < 0.1: No significant drift
    0.1 <= PSI < 0.25: Moderate drift
    PSI >= 0.25: Significant drift

    Args:
        expected: Reference distribution.
        actual: Current distribution.
        bins: Number of bins for histograms.

    Returns:
        PSI value.
    """
    def _hist_percents(arr, bins):
        hist, bin_edges = np.histogram(arr, bins=bins, density=False)
        percs = hist / len(arr)
        percs = np.where(percs == 0, 0.0001, percs)
        return percs, bin_edges

    expected_percs, bin_edges = _hist_percents(expected, bins)
    actual_percs, _ = _hist_percents(actual, bins)

    psi = np.sum((actual_percs - expected_percs) * np.log(actual_percs / expected_percs))
    return float(psi)


def psi_categorical(expected: pd.Series, actual: pd.Series) -> float:
    """Calculate PSI for categorical features using category proportions."""
    all_categories = set(expected.unique()) | set(actual.unique())

    expected_counts = expected.value_counts()
    actual_counts = actual.value_counts()

    expected_props = expected_counts / len(expected)
    actual_props = actual_counts / len(actual)

    expected_props = expected_props.reindex(all_categories).fillna(0.0001)
    actual_props = actual_props.reindex(all_categories).fillna(0.0001)

    psi = np.sum((actual_props - expected_props) * np.log(actual_props / expected_props))
    return float(psi)


def ks_test_drift(reference: np.ndarray, current: np.ndarray) -> Dict[str, float]:
    """Kolmogorov-Smirnov test for distribution drift."""
    statistic, p_value = ks_2samp(reference, current)
    return {
        'ks_statistic': float(statistic),
        'p_value': float(p_value),
        'drift_detected': p_value < 0.05,
    }


def chi2_test_drift(reference: pd.Series, current: pd.Series) -> Dict[str, float]:
    """Chi-square test for categorical drift."""
    contingency = pd.crosstab(reference, current)
    chi2, p_value, dof, expected = chi2_contingency(contingency)
    return {
        'chi2_statistic': float(chi2),
        'p_value': float(p_value),
        'dof': int(dof),
        'drift_detected': p_value < 0.05,
    }


def calculate_drift_metrics(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    features: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Calculate comprehensive drift metrics for all features.

    Args:
        reference_df: Reference (training) data.
        current_df: Current (production) data.
        features: List of features to check. If None, uses ALL_FEATURES.

    Returns:
        Dictionary with drift metrics.
    """
    if features is None:
        features = ALL_FEATURES

    results = {
        'numerical_features': {},
        'categorical_features': {},
        'overall_drift_score': 0.0,
        'drift_detected': False,
        'drifted_features': [],
    }

    numerical_drifts = []
    categorical_drifts = []

    for feature in features:
        if feature not in reference_df.columns or feature not in current_df.columns:
            continue

        ref_data = reference_df[feature].dropna()
        cur_data = current_df[feature].dropna()

        if len(ref_data) < 10 or len(cur_data) < 10:
            continue

        if feature in NUMERICAL_FEATURES:
            psi_val = population_stability_index(ref_data.values, cur_data.values)
            ks_result = ks_test_drift(ref_data.values, cur_data.values)

            drift_score = max(psi_val, ks_result['ks_statistic'])
            numerical_drifts.append(drift_score)

            results['numerical_features'][feature] = {
                'psi': psi_val,
                'ks_statistic': ks_result['ks_statistic'],
                'ks_p_value': ks_result['p_value'],
                'ks_drift_detected': ks_result['drift_detected'],
                'drift_level': (
                    'high' if psi_val >= 0.25 else
                    'moderate' if psi_val >= 0.1 else
                    'low'
                ),
            }

            if psi_val >= 0.1 or ks_result['drift_detected']:
                results['drifted_features'].append(feature)

        elif feature in CATEGORICAL_FEATURES:
            psi_val = psi_categorical(ref_data, cur_data)
            chi2_result = chi2_test_drift(ref_data, cur_data)

            categorical_drifts.append(psi_val)

            results['categorical_features'][feature] = {
                'psi': psi_val,
                'chi2_statistic': chi2_result['chi2_statistic'],
                'chi2_p_value': chi2_result['p_value'],
                'chi2_drift_detected': chi2_result['drift_detected'],
                'drift_level': (
                    'high' if psi_val >= 0.25 else
                    'moderate' if psi_val >= 0.1 else
                    'low'
                ),
            }

            if psi_val >= 0.1 or chi2_result['drift_detected']:
                results['drifted_features'].append(feature)

    all_drifts = numerical_drifts + categorical_drifts
    if all_drifts:
        results['overall_drift_score'] = float(np.mean(all_drifts))
        results['drift_detected'] = len(results['drifted_features']) > 0

    return results


def prediction_drift(
    reference_preds: np.ndarray,
    current_preds: np.ndarray,
) -> Dict[str, Any]:
    """Detect drift in model predictions."""
    psi_val = population_stability_index(reference_preds, current_preds)
    ks_result = ks_2samp(reference_preds, current_preds)

    return {
        'prediction_psi': psi_val,
        'prediction_ks_statistic': ks_result['ks_statistic'],
        'prediction_ks_p_value': ks_result['p_value'],
        'prediction_drift_detected': psi_val >= 0.1 or ks_result['drift_detected'],
        'reference_mean': float(np.mean(reference_preds)),
        'current_mean': float(np.mean(current_preds)),
        'reference_std': float(np.std(reference_preds)),
        'current_std': float(np.std(current_preds)),
        'mean_shift': float(np.mean(current_preds) - np.mean(reference_preds)),
    }


def run_drift_detection(
    reference_data_path: str | Path = 'ml/data/raw/salary_data.csv',
    current_data_path: Optional[str | Path] = None,
    model_path: str | Path = 'ml/models/best_model.joblib',
    output_dir: str | Path = 'ml/models',
    sample_size: int = 1000,
) -> Dict[str, Any]:
    """Run complete drift detection analysis."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    reference_df = load_data(reference_data_path)

    if current_data_path and Path(current_data_path).exists():
        current_df = load_data(current_data_path)
    else:
        # Use a sample from reference data as "current" for demo
        current_df = reference_df.sample(n=min(sample_size, len(reference_df)), random_state=123)

    model = load_model(model_path)

    ref_X = reference_df[ALL_FEATURES].copy()
    cur_X = current_df[ALL_FEATURES].copy()

    ref_preds = model.predict(ref_X)
    cur_preds = model.predict(cur_X)

    feature_drift = calculate_drift_metrics(reference_df, current_df)
    pred_drift = prediction_drift(ref_preds, cur_preds)

    results = {
        'feature_drift': feature_drift,
        'prediction_drift': pred_drift,
        'reference_size': len(reference_df),
        'current_size': len(current_df),
        'timestamp': pd.Timestamp.now().isoformat(),
    }

    output_path = Path(output_dir) / 'drift_report.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Drift detection completed. Report saved to {output_path}")
    print(f"Overall drift score: {feature_drift['overall_drift_score']:.4f}")
    print(f"Drift detected: {feature_drift['drift_detected']}")
    print(f"Drifted features: {feature_drift['drifted_features']}")
    print(f"Prediction drift: {pred_drift['prediction_drift_detected']}")

    return results


def load_data(data_path: str | Path) -> pd.DataFrame:
    """Load the salary dataset."""
    return pd.read_csv(data_path)


def load_model(model_path: str | Path):
    """Load the trained model pipeline."""
    return joblib.load(model_path)


if __name__ == '__main__':
    run_drift_detection()