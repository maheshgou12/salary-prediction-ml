"""FairSalary AI - SHAP Explainability"""
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

ALL_FEATURES = [
    'years_experience', 'skills_count', 'previous_salary', 'interview_score',
    'education_level', 'job_role', 'location', 'company_size'
]


def load_model(model_path: str | Path):
    """Load the trained model pipeline."""
    return joblib.load(model_path)


def load_data(data_path: str | Path, sample_size: int = 500) -> pd.DataFrame:
    """Load data and return a sample for SHAP analysis."""
    df = pd.read_csv(data_path)
    return df.sample(n=min(sample_size, len(df)), random_state=42)


def get_feature_names_after_preprocessing(
    preprocessor, categorical_features: List[str]
) -> List[str]:
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
        model: Trained pipeline.
        X_sample: Sample of training data for background distribution.

    Returns:
        SHAP Explainer object.
    """
    # Extract preprocessor and model
    preprocessor = model.named_steps['preprocessor']
    regressor = model.named_steps['model']

    # Transform sample data
    X_transformed = preprocessor.transform(X_sample)

    # Get feature names
    feature_names = get_feature_names_after_preprocessing(preprocessor, CATEGORICAL_FEATURES)

    # Create explainer based on model type
    if hasattr(regressor, 'tree_') or hasattr(regressor, 'estimators_'):
        # Tree-based model
        explainer = shap.TreeExplainer(regressor, X_transformed, feature_names=feature_names)
    else:
        # Linear model - use LinearExplainer
        explainer = shap.LinearExplainer(regressor, X_transformed, feature_names=feature_names)

    return explainer


def compute_shap_values(
    explainer: shap.Explainer,
    X: pd.DataFrame,
    model,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Compute SHAP values for a dataset.

    Args:
        explainer: SHAP explainer.
        X: Input features.
        model: Trained pipeline.

    Returns:
        Tuple of (shap_values, X_transformed, feature_names).
    """
    preprocessor = model.named_steps['preprocessor']
    X_transformed = preprocessor.transform(X)
    feature_names = get_feature_names_after_preprocessing(preprocessor, CATEGORICAL_FEATURES)

    shap_values = explainer.shap_values(X_transformed)

    # Handle different SHAP output formats
    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    return shap_values, X_transformed, feature_names


def plot_global_importance(
    shap_values: np.ndarray,
    feature_names: List[str],
    output_path: Optional[str | Path] = None,
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
    X_transformed: np.ndarray,
    feature_names: List[str],
    output_path: Optional[str | Path] = None,
) -> plt.Figure:
    """Create SHAP summary plot (beeswarm).

    Args:
        shap_values: SHAP values array.
        X_transformed: Transformed feature matrix.
        feature_names: List of feature names.
        output_path: Optional path to save figure.

    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    # Newer SHAP API doesn't support ax parameter for summary_plot
    shap.summary_plot(shap_values, X_transformed, feature_names=feature_names,
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
) -> Dict[str, Any]:
    """Get SHAP explanation for a single prediction.

    Args:
        explainer: SHAP explainer.
        X_single: Single row DataFrame with features.
        model: Trained pipeline.
        top_k: Number of top features to return.

    Returns:
        Dictionary with explanation details.
    """
    preprocessor = model.named_steps['preprocessor']
    X_transformed = preprocessor.transform(X_single)
    feature_names = get_feature_names_after_preprocessing(preprocessor, CATEGORICAL_FEATURES)

    shap_values = explainer.shap_values(X_transformed)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    # For single sample, shap_values shape is (1, n_features)
    if shap_values.ndim > 1:
        shap_values = shap_values[0]

    # Create explanation dataframe
    exp_df = pd.DataFrame({
        'feature': feature_names,
        'shap_value': shap_values,
        'feature_value': X_transformed[0],
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
            'feature_value': X_transformed[0],
        }).to_dict('records'),
    }


def plot_local_waterfall(
    explanation: Dict[str, Any],
    output_path: Optional[str | Path] = None,
) -> plt.Figure:
    """Create waterfall-style local explanation plot.

    Args:
        explanation: Explanation dictionary from get_local_explanation.
        output_path: Optional path to save figure.

    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    base_value = explanation['base_value']
    prediction = explanation['prediction']
    top_features = explanation['top_features']

    # Summary metrics
    ax.text(0.02, 0.98, f'Base Value (Avg Salary): ${base_value:,.0f}',
            transform=ax.transAxes, fontsize=12, fontweight='bold', va='top')
    ax.text(0.02, 0.92, f'Prediction: ${prediction:,.0f}',
            transform=ax.transAxes, fontsize=12, fontweight='bold', va='top')
    ax.text(0.02, 0.86, f'Difference: ${prediction - base_value:+,.0f}',
            transform=ax.transAxes, fontsize=12, va='top',
            color='green' if prediction > base_value else 'red')

    # Feature contributions bar chart
    features_df = pd.DataFrame(top_features)
    features_df = features_df.sort_values('shap_value', ascending=True)

    colors = ['#ff6b6b' if v < 0 else '#4ecb71' for v in features_df['shap_value']]

    bars = ax.barh(range(len(features_df)), features_df['shap_value'],
                   color=colors, edgecolor='black')
    ax.set_yticks(range(len(features_df)))
    ax.set_yticklabels(features_df['feature'])
    ax.set_xlabel('SHAP Value (Impact on Salary)')
    ax.set_title('Feature Contributions to Prediction')
    ax.axvline(x=0, color='black', linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Add value labels
    for i, (_, row) in enumerate(features_df.iterrows()):
        offset = 500 if row['shap_value'] >= 0 else -500
        ax.text(row['shap_value'] + offset, i, f"${row['shap_value']:+,.0f}",
                va='center', ha='left' if row['shap_value'] >= 0 else 'right', fontsize=9)

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches='tight')

    return fig


def run_shap_analysis(
    data_path: str | Path = 'ml/data/raw/salary_data.csv',
    model_path: str | Path = 'ml/models/best_model.joblib',
    output_dir: str | Path = 'ml/models',
    sample_size: int = 500,
) -> Dict[str, Any]:
    """Run complete SHAP analysis."""
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
    fig2 = plot_shap_summary(shap_values, X_transformed, feature_names,
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

    with open(Path(output_dir) / 'shap_analysis.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"SHAP analysis saved to {output_dir}")
    print(f"Global importance plot: {output_dir / 'shap_global_importance.png'}")
    print(f"Summary plot: {output_dir / 'shap_summary.png'}")

    return results


def load_model(model_path: str | Path):
    """Load the trained model pipeline."""
    return joblib.load(model_path)


def load_data(data_path: str | Path, sample_size: int = 500) -> pd.DataFrame:
    """Load data and return a sample for SHAP analysis."""
    df = pd.read_csv(data_path)
    return df.sample(n=min(sample_size, len(df)), random_state=42)


if __name__ == '__main__':
    run_shap_analysis()