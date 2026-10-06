"""FairSalary AI - ML Package"""
from .data_loader import load_raw_data, load_processed_data, save_processed_data, get_data_info
from .preprocessing import (
    create_preprocessing_pipeline,
    create_full_pipeline,
    get_feature_names_after_preprocessing,
    prepare_features,
    prepare_target,
    save_preprocessor,
    load_preprocessor,
    split_features_target,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    ALL_FEATURES,
    PROTECTED_ATTRIBUTES,
    TARGET,
)
from .feature_engineering import engineer_all_features, get_feature_groups
from .train import run_training, load_data as load_train_data
from .evaluate import run_evaluation, evaluate_model, load_model as load_eval_model
from .fairness import run_fairness_audit, load_model as load_fairness_model
from .explain import run_shap_analysis, load_model as load_explain_model
from .uncertainty import run_conformal_prediction, ConformalPredictor
from .drift import run_drift_detection, calculate_drift_metrics
from .predict import run_prediction, predict_salary, predict_batch, load_conformal_quantile

__all__ = [
    # Data loading
    'load_raw_data',
    'load_processed_data',
    'save_processed_data',
    'get_data_info',
    # Preprocessing
    'create_preprocessing_pipeline',
    'create_full_pipeline',
    'get_feature_names_after_preprocessing',
    'prepare_features',
    'prepare_target',
    'save_preprocessor',
    'load_preprocessor',
    'split_features_target',
    # Feature engineering
    'engineer_all_features',
    'get_feature_groups',
    # Training
    'run_training',
    'load_train_data',
    # Evaluation
    'run_evaluation',
    'evaluate_model',
    'load_eval_model',
    # Fairness
    'run_fairness_audit',
    'load_fairness_model',
    # Explainability
    'run_shap_analysis',
    'load_explain_model',
    # Uncertainty
    'run_conformal_prediction',
    'ConformalPredictor',
    # Drift
    'run_drift_detection',
    'calculate_drift_metrics',
    # Prediction
    'run_prediction',
    'predict_salary',
    'predict_batch',
    'load_conformal_quantile',
    # Constants
    'NUMERICAL_FEATURES',
    'CATEGORICAL_FEATURES',
    'ALL_FEATURES',
    'PROTECTED_ATTRIBUTES',
    'TARGET',
]