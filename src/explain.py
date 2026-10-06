"""FairPay SHAP Explainability Module.

This module provides global and local explanations for salary predictions using SHAP.
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

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

ALL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES


def load_model(model_path: str | Path):
    """Load the trained model pipeline."""
    return joblib.load(model_path)


def load_data(data_path: str | Path, sample_size: int = 500) -> pd.DataFrame:
    """Load data and return a sample for SHAP analysis."""
    df = pd.read_csv(data_path)
    return df.sample(n=min(sample_size, len(df)), random_state=42)


def get_feature_names_after_preprocessing(preprocessor, categorical_features: list[str]) -> list[str]:
    """Get feature names after one-hot encoding."""
    # Get numerical feature names (unchanged)
    num_features = NUMERICAL_FEATURES

    # Get categorical feature names after one-hot encoding
    cat_encoder = preprocessor.named_transformers_['cat'].named_steps['encoder']
    cat_feature_names = cat_encoder.get_feature_names_out(categorical_features).tolist()

    return num_features + cat_feature_names


def create_shap_explainer(model, X_sample: pd.DataFrame) -> shap.Explainer:
    """Create a SHAP explainer for the model.

    Args:
        model: Trained pipeline or ensemble.
        X_sample: Sample of training data for background distribution.

    Returns:
        SHAP Explainer object.
    """
    # Handle both Pipeline (single model) and StackingRegressor/VotingRegressor (ensembles)
    if hasattr(model, 'named_steps'):
        # Pipeline model
        preprocessor = model.named_steps['preprocessor']
        regressor = model.named_steps['model']
    elif hasattr(model, 'estimators_'):
        # StackingRegressor / VotingRegressor - use first estimator's preprocessor
        first_estimator = model.estimators_[0]
        if hasattr(first_estimator, 'named_steps'):
            preprocessor = first_estimator.named_steps['preprocessor']
        else:
            raise ValueError("Cannot extract preprocessor from ensemble")
        regressor = model  # Use the full ensemble for predictions
    else:
        raise ValueError(f"Unsupported model type: {type(model)}")

    # Transform sample data
    X_transformed = preprocessor.transform(X_sample)

    # Get feature names
    feature_names = get_feature_names_after_preprocessing(preprocessor, CATEGORICAL_FEATURES)

    # Create explainer - use model-agnostic for ensembles, specific for single models
    if hasattr(regressor, 'tree_'):
        # Tree-based model
        explainer = shap.TreeExplainer(regressor, X_transformed, feature_names=feature_names)
    elif hasattr(regressor, 'estimators_'):
        # Ensemble (Stacking/Voting) - use model-agnostic KernelExplainer with raw data
        # Use a smaller background sample for speed
        X_background = X_sample.sample(n=min(50, len(X_sample)), random_state=42)
        
        def model_predict_raw(X_raw):
            # X_raw comes from KernelExplainer as numpy array with original feature columns
            if not isinstance(X_raw, pd.DataFrame):
                X_raw = pd.DataFrame(X_raw, columns=ALL_FEATURES)
            return model.predict(X_raw)
        
        explainer = shap.KernelExplainer(model_predict_raw, X_background, feature_names=ALL_FEATURES)
    else:
        # Linear model - use LinearExplainer
        explainer = shap.LinearExplainer(regressor, X_transformed, feature_names=feature_names)

    return explainer


def compute_shap_values(explainer: shap.Explainer, X: pd.DataFrame, model) -> tuple:
    """Compute SHAP values for a dataset.

    Args:
        explainer: SHAP explainer.
        X: Input features.
        model: Trained pipeline or ensemble.

    Returns:
        Tuple of (shap_values, X_transformed, feature_names).
    """
    # Handle both Pipeline and ensemble
    if hasattr(model, 'named_steps'):
        preprocessor = model.named_steps['preprocessor']
    elif hasattr(model, 'estimators_'):
        first_estimator = model.estimators_[0]
        preprocessor = first_estimator.named_steps['preprocessor']
    else:
        raise ValueError(f"Unsupported model type: {type(model)}")

    X_transformed = preprocessor.transform(X)
    expanded_feature_names = get_feature_names_after_preprocessing(preprocessor, CATEGORICAL_FEATURES)

    # For KernelExplainer, we need to pass raw data (ALL_FEATURES)
    # For TreeExplainer and LinearExplainer, we pass transformed data
    if isinstance(explainer, shap.explainers._kernel.KernelExplainer):
        shap_values = explainer.shap_values(X)
        feature_names = ALL_FEATURES
    else:
        shap_values = explainer.shap_values(X_transformed)
        feature_names = expanded_feature_names

    # Handle different SHAP output formats
    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    return shap_values, X_transformed, feature_names


def plot_global_importance(
    shap_values: np.ndarray,
    feature_names: list[str],
    output_path: str | Path | None = None,
) -> plt.Figure:
    """Create global feature importance plot (mean |SHAP|).

    Args:
        shap_values: SHAP values array.
        feature_names: List of feature names.
        output_path: Optional path to save figure.

    Returns:
        Matplotlib figure.
    """
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'mean_abs_shap': mean_abs_shap,
    }).sort_values('mean_abs_shap', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 8))
    bars = ax.barh(range(len(importance_df)), importance_df['mean_abs_shap'], color='steelblue', edgecolor='black')
    ax.set_yticks(range(len(importance_df)))
    ax.set_yticklabels(importance_df['feature'])
    ax.set_xlabel('Mean |SHAP Value| (Impact on Salary Prediction)')
    ax.set_title('Global Feature Importance (SHAP)')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Add value labels
    for i, (_, row) in enumerate(importance_df.iterrows()):
        ax.text(row['mean_abs_shap'] + 0.01 * max(importance_df['mean_abs_shap']),
                i, f'{row["mean_abs_shap"]:,.0f}', va='center', fontsize=9)

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches='tight')

    return fig


def plot_shap_summary(
    shap_values: np.ndarray,
    X_data: np.ndarray,
    feature_names: list[str],
    output_path: str | Path | None = None,
) -> plt.Figure:
    """Create SHAP summary plot (beeswarm).

    Args:
        shap_values: SHAP values array.
        X_data: Feature matrix (raw or transformed depending on explainer).
        feature_names: List of feature names.
        output_path: Optional path to save figure.

    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    # Newer SHAP API doesn't support ax parameter for summary_plot
    shap.summary_plot(shap_values, X_data, feature_names=feature_names,
                      plot_type='dot', show=False)
    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches='tight')

    return fig


def get_local_explanation(
    explainer: shap.Explainer,
    X_single: pd.DataFrame,
    model,
    top_k: int = 10,
) -> dict[str, Any]:
    """Get SHAP explanation for a single prediction.

    Args:
        explainer: SHAP explainer.
        X_single: Single row DataFrame with features.
        model: Trained pipeline or ensemble.
        top_k: Number of top features to return.

    Returns:
        Dictionary with explanation details.
    """
    # Handle both Pipeline and ensemble
    if hasattr(model, 'named_steps'):
        preprocessor = model.named_steps['preprocessor']
    elif hasattr(model, 'estimators_'):
        first_estimator = model.estimators_[0]
        preprocessor = first_estimator.named_steps['preprocessor']
    else:
        raise ValueError(f"Unsupported model type: {type(model)}")

    X_transformed = preprocessor.transform(X_single)
    expanded_feature_names = get_feature_names_after_preprocessing(preprocessor, CATEGORICAL_FEATURES)

    # For KernelExplainer, use raw data
    if isinstance(explainer, shap.explainers._kernel.KernelExplainer):
        shap_values = explainer.shap_values(X_single)
        feature_names = ALL_FEATURES
        feature_values = X_single.iloc[0].values
    else:
        shap_values = explainer.shap_values(X_transformed)
        feature_names = expanded_feature_names
        feature_values = X_transformed[0]
    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    # For single sample, shap_values shape is (1, n_features)
    if shap_values.ndim > 1:
        shap_values = shap_values[0]

    # Create explanation dataframe
    exp_df = pd.DataFrame({
        'feature': feature_names,
        'shap_value': shap_values,
        'feature_value': feature_values,
    })
    exp_df['abs_shap'] = exp_df['shap_value'].abs()
    exp_df = exp_df.sort_values('abs_shap', ascending=False).head(top_k)

    # Get base value (expected value)
    base_value = explainer.expected_value
    if isinstance(base_value, np.ndarray):
        base_value = base_value[0] if len(base_value) > 0 else 0

    prediction = model.predict(X_single)[0]

    return {
        'base_value': float(base_value),
        'prediction': float(prediction),
        'top_features': exp_df[['feature', 'shap_value', 'feature_value']].to_dict('records'),
        'all_features': pd.DataFrame({
            'feature': feature_names,
            'shap_value': shap_values,
            'feature_value': feature_values,
        }).to_dict('records'),
    }


def run_shap_analysis(
    data_path: str | Path = 'data/salary_data.csv',
    model_path: str | Path = 'models/best_model.joblib',
    output_dir: str | Path = 'models',
    sample_size: int = 200,
) -> dict[str, Any]:
    """Run complete SHAP analysis.

    Args:
        data_path: Path to dataset.
        model_path: Path to trained model.
        output_dir: Directory to save plots.
        sample_size: Sample size for SHAP computation.

    Returns:
        Dictionary with analysis results.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load model and data
    model = load_model(model_path)
    df_sample = load_data(data_path, sample_size)

    X_sample = df_sample[ALL_FEATURES].copy()

    print("Creating SHAP explainer...")
    explainer = create_shap_explainer(model, X_sample)

    print("Computing SHAP values...")
    shap_values, X_transformed, feature_names = compute_shap_values(explainer, X_sample, model)

    print("Generating global importance plot...")
    fig1 = plot_global_importance(shap_values, feature_names,
                                   output_dir / 'shap_global_importance.png')
    plt.close(fig1)

    print("Generating SHAP summary plot...")
    fig2 = plot_shap_summary(shap_values, X_sample.values if isinstance(explainer, shap.explainers._kernel.KernelExplainer) else X_transformed, feature_names,
                              output_dir / 'shap_summary.png')
    plt.close(fig2)

    print("Generating local explanations for sample cases...")
    local_explanations = []
    for idx in range(min(5, len(X_sample))):
        X_single = X_sample.iloc[[idx]]
        exp = get_local_explanation(explainer, X_single, model)
        exp['sample_index'] = int(idx)
        exp['actual_salary'] = float(df_sample.iloc[idx]['salary'])
        local_explanations.append(exp)

    # Save results
    results = {
        'feature_names': feature_names,
        'global_importance': pd.DataFrame({
            'feature': feature_names,
            'mean_abs_shap': np.abs(shap_values).mean(axis=0),
        }).sort_values('mean_abs_shap', ascending=False).to_dict('records'),
        'local_explanations': local_explanations,
    }

    import json
    with open(output_dir / 'shap_analysis.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"SHAP analysis saved to {output_dir}")
    print(f"Global importance plot: {output_dir / 'shap_global_importance.png'}")
    print(f"Summary plot: {output_dir / 'shap_summary.png'}")

    return results


if __name__ == '__main__':
    run_shap_analysis()