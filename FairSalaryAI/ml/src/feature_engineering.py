"""FairSalary AI - Feature Engineering"""
import warnings
from typing import List, Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


def create_skills_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create additional features from skills.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with additional skill features.
    """
    df = df.copy()

    # Skill count already exists, but we could add more features
    # For now, we keep skills_count as is

    return df


def create_experience_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create experience-related features.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with additional experience features.
    """
    df = df.copy()

    # Experience buckets
    df['exp_bucket'] = pd.cut(
        df['years_experience'],
        bins=[-1, 0, 2, 5, 10, 15, 30],
        labels=['0', '0-2', '2-5', '5-10', '10-15', '15+']
    )

    # Log experience (for diminishing returns)
    df['log_experience'] = np.log1p(df['years_experience'])

    return df


def create_education_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create education-related features.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with additional education features.
    """
    df = df.copy()

    # Education ordinal encoding
    edu_map = {
        'High School': 0,
        'Bachelor': 1,
        'Master': 2,
        'PhD': 3
    }
    df['education_ordinal'] = df['education_level'].map(edu_map)

    return df


def create_location_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create location-based features.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with additional location features.
    """
    df = df.copy()

    # High cost of living locations
    high_col_locations = ['San Francisco', 'New York', 'Seattle', 'Boston']
    df['high_col_location'] = df['location'].isin(high_col_locations).astype(int)

    return df


def create_company_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create company size features.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with additional company features.
    """
    df = df.copy()

    # Company size ordinal
    size_map = {
        'Startup (1-50)': 0,
        'Small (51-200)': 1,
        'Medium (201-1000)': 2,
        'Large (1000+)': 3
    }
    df['company_size_ordinal'] = df['company_size'].map(size_map)

    return df


def create_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create interaction features.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with interaction features.
    """
    df = df.copy()

    # Experience x Education interaction
    df['exp_x_edu'] = df['years_experience'] * df['education_ordinal']

    # Experience x Skills
    df['exp_x_skills'] = df['years_experience'] * df['skills_count']

    return df


def engineer_all_features(
    df: pd.DataFrame,
    include_interactions: bool = True
) -> pd.DataFrame:
    """Apply all feature engineering steps.

    Args:
        df: Input DataFrame.
        include_interactions: Whether to create interaction features.

    Returns:
        DataFrame with all engineered features.
    """
    df = df.copy()

    # Apply feature engineering steps
    df = create_skills_features(df)
    df = create_experience_features(df)
    df = create_education_features(df)
    df = create_location_features(df)
    df = create_company_features(df)

    if include_interactions:
        df = create_interaction_features(df)

    return df


def get_feature_groups() -> dict:
    """Get feature group definitions for model interpretation.

    Returns:
        Dictionary mapping group names to feature lists.
    """
    return {
        'numerical': [
            'years_experience',
            'skills_count',
            'previous_salary',
            'interview_score',
        ],
        'categorical': [
            'education_level',
            'job_role',
            'location',
            'company_size',
        ],
        'protected': [
            'gender',
            'age',
        ],
        'engineered': [
            'exp_bucket',
            'log_experience',
            'education_ordinal',
            'high_col_location',
            'company_size_ordinal',
            'exp_x_edu',
            'exp_x_skills',
        ],
        'target': ['salary'],
    }