"""FairSalary AI - Model Evaluation"""
import json
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

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


def evaluate_model(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_pred_lower: Optional[np.ndarray] = None,
    y_pred_upper: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """Calculate comprehensive regression metrics.

    Args:
        y_true: True target values.
        y_pred: Predicted values.
        y_pred_lower: Optional lower bound of prediction interval.
        y_pred_upper: Optional upper bound of prediction interval.

    Returns:
        Dictionary with evaluation metrics.
    """
    metrics = {
        'MAE': mean_absolute_error(y_true, y_pred),
        'RMSE': np.sqrt(mean_squared_error(y_true, y_pred)),
        'R2': r2_score(y_true, y_pred),
        'MAPE': np.mean(np.abs((y_true - y_pred) / y_true)) * 100,
    }

    if y_pred_lower is not None and y_pred_upper is not None:
        coverage = np.mean((y_true >= y_pred_lower) & (y_true <= y_pred_upper))
        avg_width = np.mean(y_pred_upper - y_pred_lower)
        metrics['PI_Coverage'] = coverage
        metrics['PI_Width'] = avg_width

    return metrics


def evaluate_by_group(
    df: pd.DataFrame,
    group_col: str,
    pred_col: str = 'predicted_salary',
    true_col: str = 'salary',
) -> pd.DataFrame:
    """Evaluate model performance by group.

    Args:
        df: DataFrame with predictions and true values.
        group_col: Column to group by.
        pred_col: Column with predictions.
        true_col: Column with true values.

    Returns:
        DataFrame with metrics per group.
    """
    metrics = []
    for group, group_df in df.groupby(group_col):
        y_true = group_df[true_col].values
        y_pred = group_df[pred_col].values

        metrics.append({
            'group': group,
            'count': len(group_df),
            'MAE': mean_absolute_error(y_true, y_pred),
            'RMSE': np.sqrt(mean_squared_error(y_true, y_pred)),
            'R2': r2_score(y_true, y_pred),
            'mean_predicted': y_pred.mean(),
            'mean_actual': y_true.mean(),
            'bias': y_pred.mean() - y_true.mean(),
        })

    return pd.DataFrame(metrics)


def plot_predictions_vs_actual(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """Create predictions vs actual plot.

    Args:
        y_true: True target values.
        y_pred: Predicted values.
        output_path: Optional path to save figure.

    Returns:
        Matplotlib figure.
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Scatter plot
    axes[0].scatter(y_true, y_pred, alpha=0.5, s=10, color='steelblue')
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    axes[0].plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
    axes[0].set_xlabel('Actual Salary ($)')
    axes[0].set_ylabel('Predicted Salary ($)')
    axes[0].set_title('Predictions vs Actual')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Residuals
    residuals = y_pred - y_true
    axes[1].scatter(y_pred, residuals, alpha=0.5, s=10, color='coral')
    axes[1].axhline(y=0, color='r', linestyle='--', lw=2)
    axes[1].set_xlabel('Predicted Salary ($)')
    axes[1].set_ylabel('Residual ($)')
    axes[1].set_title('Residuals vs Predicted')
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')

    return fig


def plot_residuals_distribution(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """Plot residuals distribution.

    Args:
        y_true: True target values.
        y_pred: Predicted values.
        output_path: Optional path to save figure.

    Returns:
        Matplotlib figure.
    """
    residuals = y_pred - y_true

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Histogram
    axes[0].hist(residuals, bins=50, edgecolor='black', alpha=0.7, color='steelblue')
    axes[0].axvline(x=0, color='r', linestyle='--', lw=2)
    axes[0].set_xlabel('Residual ($)')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title('Residuals Distribution')
    axes[0].grid(True, alpha=0.3)

    # Q-Q plot
    from scipy import stats
    stats.probplot(residuals, dist="norm", plot=axes[1])
    axes[1].set_title('Q-Q Plot of Residuals')
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')

    return fig


def plot_feature_importance(
    feature_names: List[str],
    importances: np.ndarray,
    top_k: int = 20,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """Plot feature importance.

    Args:
        feature_names: List of feature names.
        importances: Array of importance values.
        top_k: Number of top features to show.
        output_path: Optional path to save figure.

    Returns:
        Matplotlib figure.
    """
    # Sort by importance
    idx = np.argsort(importances)[::-1][:top_k]
    top_features = [feature_names[i] for i in idx]
    top_importances = importances[idx]

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(top_features)))
    bars = ax.barh(range(len(top_features)), top_importances, color=colors, edgecolor='black')
    ax.set_yticks(range(len(top_features)))
    ax.set_yticklabels(top_features)
    ax.set_xlabel('Importance')
    ax.set_title(f'Top {top_k} Feature Importances')
    ax.invert_yaxis()

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, top_importances)):
        ax.text(val + 0.01 * max(top_importances), i, f'{val:.4f}',
                va='center', fontsize=9)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')

    return fig


def plot_error_by_group(
    df: pd.DataFrame,
    group_col: str,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """Plot error metrics by group.

    Args:
        df: DataFrame with predictions and group column.
        group_col: Column to group by.
        output_path: Optional path to save figure.

    Returns:
        Matplotlib figure.
    """
    metrics = []
    for group, group_df in df.groupby(group_col):
        y_true = group_df['salary'].values
        y_pred = group_df['predicted_salary'].values
        metrics.append({
            'group': group,
            'MAE': mean_absolute_error(y_true, y_pred),
            'RMSE': np.sqrt(mean_squared_error(y_true, y_pred)),
            'R2': r2_score(y_true, y_pred),
            'count': len(group_df),
        })

    metrics_df = pd.DataFrame(metrics)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for ax, metric, title in zip(axes, ['MAE', 'RMSE', 'R2'], ['MAE by Group', 'RMSE by Group', 'R² by Group']):
        bars = ax.bar(metrics_df['group'], metrics_df[metric], color='steelblue', edgecolor='black')
        ax.set_xlabel('Group')
        ax.set_ylabel(metric)
        ax.set_title(title)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)

        # Add value labels
        for bar, val in zip(bars, metrics_df[metric]):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01 * max(metrics_df[metric]),
                    f'{val:,.0f}' if metric != 'R2' else f'{val:.3f}',
                    ha='center', va='bottom', fontsize=8)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')

    return fig


def run_evaluation(
    data_path: str | Path = 'ml/data/raw/salary_data.csv',
    model_path: str | Path = 'ml/models/best_model.joblib',
    output_dir: str | Path = 'ml/models',
) -> Dict[str, Any]:
    """Run complete model evaluation."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data and model
    df = load_data(data_path)
    model = load_model(model_path)

    # Prepare features and target
    X = df[ALL_FEATURES].copy()
    y = df[TARGET].copy()

    # Predict
    y_pred = model.predict(X)

    # Calculate metrics
    metrics = evaluate_model(y.values, y_pred)

    # Add predictions to dataframe for group analysis
    df = df.copy()
    df['predicted_salary'] = model.predict(df[ALL_FEATURES])

    print("=" * 60)
    print("MODEL EVALUATION RESULTS")
    print("=" * 60)
    for metric, value in metrics.items():
        if metric == 'MAPE':
            print(f"  {metric}: {value:.2f}%")
        else:
            print(f"  {metric}: {value:,.2f}")

    # Evaluate by protected attributes
    print("\n--- Fairness Metrics ---")
    for attr in ['gender', 'age']:
        if attr in df.columns:
            group_metrics = evaluate_by_group(df, attr)
            print(f"\n{attr.upper()}:")
            for _, row in group_metrics.iterrows():
                print(f"  {row['group']}: MAE=${row['MAE']:,.0f}, R2={row['R2']:.4f}, Bias=${row['bias']:,.0f}")

    # Save metrics
    metrics_path = Path(output_dir) / 'evaluation_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"\nMetrics saved to {metrics_path}")

    # Generate plots
    print("\nGenerating plots...")
    plot_predictions_vs_actual(df['salary'].values, df['predicted_salary'].values,
                               output_dir / 'predictions_vs_actual.png')
    plot_residuals_distribution(df['salary'].values, df['predicted_salary'].values,
                                 output_dir / 'residuals_distribution.png')

    # Feature importance (if available)
    try:
        model_pipeline = model
        preprocessor = model_pipeline.named_steps['preprocessor']
        regressor = model_pipeline.named_steps['model']

        if hasattr(regressor, 'coef_'):
            # Linear model
            feature_names = ['years_experience', 'skills_count', 'previous_salary', 'interview_score']
            cat_encoder = preprocessor.named_transformers_['cat'].named_steps['encoder']
            cat_features = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
            feature_names = NUMERICAL_FEATURES + cat_features
            importances = np.abs(regressor.coef_)
            plot_feature_importance(feature_names, importances, output_dir / 'feature_importance.png')
        elif hasattr(regressor, 'feature_importances_'):
            # Tree-based model
            feature_names = ['years_experience', 'skills_count', 'previous_salary', 'interview_score']
            cat_encoder = preprocessor.named_transformers_['cat'].named_steps['encoder']
            cat_features = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
            feature_names = NUMERICAL_FEATURES + cat_features
            importances = regressor.feature_importances_
            plot_feature_importance(feature_names, importances, output_dir / 'feature_importance.png')
    except Exception as e:
        print(f"Could not generate feature importance plot: {e}")

    # Error by group plots
    if 'gender' in df.columns:
        plot_error_by_group(df, 'gender', output_dir / 'error_by_gender.png')
    if 'age' in df.columns:
        # Create age groups
        df['age_group'] = pd.cut(df['age'], bins=[20, 30, 40, 50, 65],
                                 labels=['20-30', '30-40', '40-50', '50+'])
        plot_error_by_group(df, 'age_group', output_dir / 'error_by_age.png')

    print(f"\nPlots saved to {output_dir}")

    return metrics


if __name__ == '__main__':
    run_evaluation()