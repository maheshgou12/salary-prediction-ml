"""FairSalary AI - Preprocessing Pipeline"""
import warnings
from pathlib import Path
from typing import List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore")

# Feature definitions
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

# Protected attributes - NOT used as model features
PROTECTED_ATTRIBUTES = ['gender', 'age']

TARGET = 'salary'

ALL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES


def create_preprocessing_pipeline() -> ColumnTransformer:
    """Create the preprocessing pipeline for numerical and categorical features.

    Returns:
        Configured ColumnTransformer with imputation and encoding.
    """
    numerical_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
    ])

    preprocessor = ColumnTransformer([
        ('num', numerical_pipeline, NUMERICAL_FEATURES),
        ('cat', categorical_pipeline, CATEGORICAL_FEATURES),
    ], remainder='drop')

    return preprocessor


def create_full_pipeline(model) -> Pipeline:
    """Create full ML pipeline with preprocessing and model.

    Args:
        model: sklearn-compatible estimator.

    Returns:
        Complete Pipeline with preprocessing and model.
    """
    preprocessor = create_preprocessing_pipeline()
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', model),
    ])
    return pipeline


def get_feature_names_after_preprocessing(
    preprocessor: ColumnTransformer,
    categorical_features: List[str]
) -> List[str]:
    """Get feature names after one-hot encoding.

    Args:
        preprocessor: Fitted ColumnTransformer.
        categorical_features: List of categorical feature names.

    Returns:
        List of feature names after transformation.
    """
    # Numerical features (unchanged)
    num_features = NUMERICAL_FEATURES

    # Categorical features after one-hot encoding
    cat_encoder = preprocessor.named_transformers_['cat'].named_steps['encoder']
    cat_feature_names = cat_encoder.get_feature_names_out(categorical_features).tolist()

    return num_features + cat_feature_names


def prepare_features(
    df: pd.DataFrame,
    preprocessor: Optional[ColumnTransformer] = None,
    fit: bool = False
) -> Tuple[np.ndarray, ColumnTransformer]:
    """Prepare features for modeling.

    Args:
        df: Input DataFrame with raw features.
        preprocessor: Optional pre-fitted preprocessor.
        fit: Whether to fit the preprocessor.

    Returns:
        Tuple of (transformed features, fitted preprocessor).
    """
    if preprocessor is None:
        preprocessor = create_preprocessing_pipeline()

    X = df[ALL_FEATURES].copy()

    if fit:
        X_transformed = preprocessor.fit_transform(X)
    else:
        X_transformed = preprocessor.transform(X)

    return X_transformed, preprocessor


def prepare_target(df: pd.DataFrame) -> np.ndarray:
    """Extract target variable.

    Args:
        df: Input DataFrame.

    Returns:
        Target array.
    """
    return df[TARGET].values


def save_preprocessor(preprocessor: ColumnTransformer, path: str) -> None:
    """Save preprocessor to disk.

    Args:
        preprocessor: Fitted ColumnTransformer.
        path: Path to save.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, path)


def load_preprocessor(path: str) -> ColumnTransformer:
    """Load preprocessor from disk.

    Args:
        path: Path to load from.

    Returns:
        Fitted ColumnTransformer.
    """
    return joblib.load(path)


def split_features_target(
    df: pd.DataFrame,
    target_col: str = TARGET
) -> Tuple[pd.DataFrame, pd.Series]:
    """Split DataFrame into features and target.

    Args:
        df: Input DataFrame.
        target_col: Name of target column.

    Returns:
        Tuple of (features DataFrame, target Series).
    """
    X = df.drop(columns=[target_col])
    y = df[target_col]
    return X, y