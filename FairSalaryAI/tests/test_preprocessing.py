"""Tests for FairPay preprocessing and prediction."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.src.train import (
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    ALL_FEATURES,
    PROTECTED_ATTRIBUTES,
    TARGET,
    create_preprocessing_pipeline,
    load_data,
    evaluate_model,
)


class TestDataLoading:
    """Tests for data loading."""

    def test_load_data_returns_dataframe(self):
        """Test that load_data returns a DataFrame."""
        df = load_data('data/salary_data.csv')
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_data_has_required_columns(self):
        """Test that data has all required columns."""
        df = load_data('data/salary_data.csv')
        expected_cols = ALL_FEATURES + PROTECTED_ATTRIBUTES + [TARGET]
        for col in expected_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_data_has_expected_size(self):
        """Test that data has at least 2000 rows."""
        df = load_data('data/salary_data.csv')
        assert len(df) >= 2000

    def test_no_missing_target(self):
        """Test that target column has no missing values."""
        df = load_data('data/salary_data.csv')
        assert df[TARGET].isnull().sum() == 0


class TestPreprocessing:
    """Tests for preprocessing pipeline."""

    def test_preprocessing_pipeline_creation(self):
        """Test that preprocessing pipeline can be created."""
        preprocessor = create_preprocessing_pipeline()
        assert preprocessor is not None

    def test_preprocessing_handles_missing_values(self):
        """Test that preprocessor handles missing values."""
        preprocessor = create_preprocessing_pipeline()

        # Create test data with missing values
        test_data = pd.DataFrame({
            'years_experience': [5.0, np.nan, 3.0],
            'skills_count': [5, 7, np.nan],
            'previous_salary': [100000, 120000, np.nan],
            'interview_score': [7.0, np.nan, 8.0],
            'education_level': ['Bachelor', 'Master', 'PhD'],
            'job_role': ['Software Engineer', 'Data Scientist', 'ML Engineer'],
            'location': ['San Francisco', 'Remote', 'New York'],
            'company_size': ['Large (1000+)', 'Startup (1-50)', 'Medium (201-1000)'],
        })

        # Should not raise
        transformed = preprocessor.fit_transform(test_data)
        assert transformed.shape[0] == 3
        assert not np.isnan(transformed).any()

    def test_preprocessing_handles_unknown_categories(self):
        """Test that preprocessor handles unknown categories gracefully."""
        preprocessor = create_preprocessing_pipeline()

        # Fit on training data
        train_data = load_data('data/salary_data.csv')[ALL_FEATURES]
        preprocessor.fit(train_data)

        # Transform with unknown category
        test_data = pd.DataFrame([{
            'years_experience': 5.0,
            'skills_count': 5,
            'previous_salary': 100000,
            'interview_score': 7.0,
            'education_level': 'Unknown Degree',  # Unknown category
            'job_role': 'Software Engineer',
            'location': 'San Francisco',
            'company_size': 'Large (1000+)',
        }])

        # Should not raise due to handle_unknown='ignore'
        transformed = preprocessor.transform(test_data)
        assert transformed.shape[0] == 1


class TestModelEvaluation:
    """Tests for model evaluation metrics."""

    def test_evaluate_model_returns_dict(self):
        """Test that evaluate_model returns a dictionary with expected keys."""
        y_true = np.array([100000, 120000, 140000, 160000])
        y_pred = np.array([105000, 118000, 142000, 158000])

        metrics = evaluate_model(y_true, y_pred)

        assert isinstance(metrics, dict)
        assert 'MAE' in metrics
        assert 'RMSE' in metrics
        assert 'R2' in metrics

    def test_evaluate_model_perfect_prediction(self):
        """Test metrics for perfect prediction."""
        y_true = np.array([100000, 120000, 140000])
        y_pred = np.array([100000, 120000, 140000])

        metrics = evaluate_model(y_true, y_pred)

        assert metrics['MAE'] == 0
        assert metrics['RMSE'] == 0
        assert metrics['R2'] == 1.0

    def test_evaluate_model_constant_prediction(self):
        """Test metrics for constant prediction."""
        y_true = np.array([100000, 120000, 140000])
        y_pred = np.array([120000, 120000, 120000])

        metrics = evaluate_model(y_true, y_pred)

        assert metrics['MAE'] > 0
        assert metrics['R2'] == 0.0  # Constant prediction has R2 = 0


class TestFeatureConfiguration:
    """Tests for feature configuration."""

    def test_numerical_features_defined(self):
        """Test that numerical features are defined."""
        assert len(NUMERICAL_FEATURES) == 4
        assert 'years_experience' in NUMERICAL_FEATURES
        assert 'skills_count' in NUMERICAL_FEATURES
        assert 'previous_salary' in NUMERICAL_FEATURES
        assert 'interview_score' in NUMERICAL_FEATURES

    def test_categorical_features_defined(self):
        """Test that categorical features are defined."""
        assert len(CATEGORICAL_FEATURES) == 4
        assert 'education_level' in CATEGORICAL_FEATURES
        assert 'job_role' in CATEGORICAL_FEATURES
        assert 'location' in CATEGORICAL_FEATURES
        assert 'company_size' in CATEGORICAL_FEATURES

    def test_protected_attributes_not_in_features(self):
        """Test that protected attributes are not in model features."""
        for protected in PROTECTED_ATTRIBUTES:
            assert protected not in ALL_FEATURES

    def test_all_features_combined(self):
        """Test that ALL_FEATURES contains all model features."""
        assert set(ALL_FEATURES) == set(NUMERICAL_FEATURES + CATEGORICAL_FEATURES)


class TestPrediction:
    """Tests for prediction functionality."""

    @pytest.fixture
    def model(self):
        """Load trained model."""
        import joblib
        return joblib.load('models/best_model.joblib')

    def test_model_predicts_single_sample(self, model):
        """Test that model can predict on a single sample."""
        input_data = pd.DataFrame([{
            'years_experience': 5.0,
            'skills_count': 5,
            'previous_salary': 120000,
            'interview_score': 7.0,
            'education_level': 'Bachelor',
            'job_role': 'Software Engineer',
            'location': 'San Francisco',
            'company_size': 'Large (1000+)',
        }])

        prediction = model.predict(input_data)
        assert len(prediction) == 1
        assert prediction[0] > 0
        assert prediction[0] < 1000000  # Sanity check

    def test_model_predicts_batch(self, model):
        """Test that model can predict on a batch."""
        input_data = pd.DataFrame([
            {
                'years_experience': 5.0,
                'skills_count': 5,
                'previous_salary': 120000,
                'interview_score': 7.0,
                'education_level': 'Bachelor',
                'job_role': 'Software Engineer',
                'location': 'San Francisco',
                'company_size': 'Large (1000+)',
            },
            {
                'years_experience': 3.0,
                'skills_count': 4,
                'previous_salary': 90000,
                'interview_score': 6.5,
                'education_level': 'Master',
                'job_role': 'Data Scientist',
                'location': 'Remote',
                'company_size': 'Startup (1-50)',
            },
        ])

        predictions = model.predict(input_data)
        assert len(predictions) == 2
        assert all(p > 0 for p in predictions)

    def test_model_predicts_different_roles(self, model):
        """Test that model produces different predictions for different roles."""
        base_input = {
            'years_experience': 5.0,
            'skills_count': 5,
            'previous_salary': 120000,
            'interview_score': 7.0,
            'education_level': 'Bachelor',
            'location': 'San Francisco',
            'company_size': 'Large (1000+)',
        }

        pred_engineer = model.predict(pd.DataFrame([{**base_input, 'job_role': 'Software Engineer'}]))[0]
        pred_manager = model.predict(pd.DataFrame([{**base_input, 'job_role': 'Engineering Manager'}]))[0]

        # Engineering Manager should generally have higher salary
        assert pred_manager > pred_engineer


if __name__ == '__main__':
    pytest.main([__file__, '-v'])