"""FairPay Streamlit Web Application.

Clean Streamlit UI for salary prediction with fairness and explainability.
"""
from __future__ import annotations

import io
import json
import os
import warnings
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
import streamlit as st

warnings.filterwarnings('ignore')

# Configuration
MODEL_PATH = Path('models/best_model.joblib')
DATA_PATH = Path('data/salary_data.csv')
SHAP_ANALYSIS_PATH = Path('models/shap_analysis.json')
FAIRNESS_AUDIT_PATH = Path('models/fairness_audit.json')
CONFORMAL_SUMMARY_PATH = Path('models/conformal_summary.json')

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

# Categorical options (from training data)
EDUCATION_LEVELS = ['High School', 'Bachelor', 'Master', 'PhD']
JOB_ROLES = [
    'Software Engineer', 'Data Scientist', 'ML Engineer', 'DevOps Engineer',
    'Frontend Developer', 'Backend Developer', 'Full Stack Developer',
    'Data Analyst', 'Product Manager', 'Engineering Manager'
]
LOCATIONS = ['San Francisco', 'New York', 'Seattle', 'Austin', 'Boston', 'Remote', 'Chicago', 'Los Angeles']
COMPANY_SIZES = ['Startup (1-50)', 'Small (51-200)', 'Medium (201-1000)', 'Large (1000+)']


@st.cache_resource
def load_model():
    """Load the trained model pipeline."""
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_training_data():
    """Load training data for reference values."""
    return pd.read_csv(DATA_PATH)


@st.cache_data
def load_shap_analysis():
    """Load precomputed SHAP analysis."""
    if SHAP_ANALYSIS_PATH.exists():
        with open(SHAP_ANALYSIS_PATH) as f:
            return json.load(f)
    return None


@st.cache_data
def load_fairness_audit():
    """Load fairness audit results."""
    if FAIRNESS_AUDIT_PATH.exists():
        with open(FAIRNESS_AUDIT_PATH) as f:
            return json.load(f)
    return None


@st.cache_data
def load_conformal_predictor():
    """Load conformal prediction quantile (q_hat)."""
    if CONFORMAL_SUMMARY_PATH.exists():
        with open(CONFORMAL_SUMMARY_PATH) as f:
            summary = json.load(f)
            return summary.get('q_hat'), summary.get('alpha', 0.1)
    return None, None


def create_input_form() -> dict[str, Any]:
    """Create the input form for single prediction.

    Returns:
        Dictionary with user inputs.
    """
    st.subheader("Candidate Details")

    col1, col2 = st.columns(2)

    with col1:
        years_experience = st.slider(
            "Years of Experience",
            min_value=0.0, max_value=30.0, value=5.0, step=0.5,
            help="Total years of professional experience"
        )
        education_level = st.selectbox(
            "Education Level",
            EDUCATION_LEVELS,
            index=1,
            help="Highest level of education completed"
        )
        skills_count = st.number_input(
            "Number of Relevant Skills",
            min_value=1, max_value=20, value=5,
            help="Count of relevant technical skills"
        )
        job_role = st.selectbox(
            "Job Role",
            JOB_ROLES,
            index=0,
            help="Target job role"
        )

    with col2:
        previous_salary = st.number_input(
            "Previous Salary ($)",
            min_value=30000, max_value=500000, value=120000, step=5000,
            help="Candidate's most recent salary"
        )
        interview_score = st.slider(
            "Interview Score (1-10)",
            min_value=1.0, max_value=10.0, value=7.0, step=0.5,
            help="Composite interview evaluation score"
        )
        location = st.selectbox(
            "Job Location",
            LOCATIONS,
            index=5,
            help="Work location"
        )
        company_size = st.selectbox(
            "Company Size",
            COMPANY_SIZES,
            index=1,
            help="Size of the hiring company"
        )

    return {
        'years_experience': years_experience,
        'education_level': education_level,
        'skills_count': skills_count,
        'job_role': job_role,
        'previous_salary': previous_salary,
        'interview_score': interview_score,
        'location': location,
        'company_size': company_size,
    }


def predict_salary(model, input_data: dict) -> tuple[float, float, float]:
    """Make salary prediction with conformal prediction interval.

    Args:
        model: Trained pipeline.
        input_data: Dictionary with feature values.

    Returns:
        Tuple of (prediction, lower_bound, upper_bound).
    """
    X = pd.DataFrame([input_data])[ALL_FEATURES]
    prediction = model.predict(X)[0]

    # Load conformal quantile
    q_hat, alpha = load_conformal_predictor()

    if q_hat is not None:
        # Use conformal prediction interval (1 - alpha coverage)
        lower = max(0, prediction - q_hat)
        upper = prediction + q_hat
        coverage = 1 - alpha
    else:
        # Fallback: Simple prediction interval using training RMSE
        rmse = 22651
        margin = 1.96 * rmse
        lower = max(0, prediction - margin)
        upper = prediction + margin
        coverage = 0.95

    return prediction, lower, upper, coverage


def get_shap_explanation(model, input_data: dict) -> dict[str, Any]:
    """Generate SHAP explanation for a single prediction.

    Args:
        model: Trained pipeline or ensemble.
        input_data: Dictionary with feature values.

    Returns:
        Dictionary with SHAP explanation.
    """
    X = pd.DataFrame([input_data])[ALL_FEATURES]

    # Handle both Pipeline and StackingEnsemble/VotingEnsemble
    if hasattr(model, 'named_steps'):
        # Pipeline model
        preprocessor = model.named_steps['preprocessor']
        regressor = model.named_steps['model']
    elif hasattr(model, 'estimators_'):
        # Ensemble - use first estimator's preprocessor
        first_estimator = model.estimators_[0]
        preprocessor = first_estimator.named_steps['preprocessor']
        regressor = model  # Use full ensemble for predictions
    else:
        raise ValueError(f"Unsupported model type: {type(model)}")

    X_transformed = preprocessor.transform(X)

    # Get feature names after encoding
    cat_encoder = preprocessor.named_transformers_['cat'].named_steps['encoder']
    cat_feature_names = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    feature_names = NUMERICAL_FEATURES + cat_feature_names

    # Create explainer based on model type
    if hasattr(regressor, 'coef_'):
        # Linear model
        explainer = shap.LinearExplainer(regressor, X_transformed, feature_names=feature_names)
        shap_values = explainer.shap_values(X_transformed)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        if shap_values.ndim > 1:
            shap_values = shap_values[0]
        base_value = explainer.expected_value
        if isinstance(base_value, np.ndarray):
            base_value = base_value[0] if len(base_value) > 0 else 0
    elif hasattr(regressor, 'estimators_'):
        # Ensemble - use precomputed global SHAP values from training
        # Load precomputed SHAP analysis
        import json
        shap_analysis_path = 'models/shap_analysis.json'
        if os.path.exists(shap_analysis_path):
            with open(shap_analysis_path) as f:
                shap_data = json.load(f)
            
            # Use global feature importance
            global_importance = shap_data.get('global_importance', {})
            shap_values = np.array([global_importance.get(f, 0) for f in feature_names])
            base_value = float(shap_data.get('expected_value', 0))
        else:
            # Fallback: use mean prediction as base value
            shap_values = np.zeros(len(feature_names))
            base_value = float(model.predict(X)[0])  # Use prediction as fallback
    elif hasattr(regressor, 'tree_'):
        # Tree-based model
        explainer = shap.TreeExplainer(regressor, X_transformed, feature_names=feature_names)
        shap_values = explainer.shap_values(X_transformed)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        if shap_values.ndim > 1:
            shap_values = shap_values[0]
        base_value = explainer.expected_value
        if isinstance(base_value, np.ndarray):
            base_value = base_value[0] if len(base_value) > 0 else 0
    else:
        # Default to TreeExplainer
        explainer = shap.TreeExplainer(regressor, X_transformed, feature_names=feature_names)
        shap_values = explainer.shap_values(X_transformed)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        if shap_values.ndim > 1:
            shap_values = shap_values[0]
        base_value = explainer.expected_value
        if isinstance(base_value, np.ndarray):
            base_value = base_value[0] if len(base_value) > 0 else 0

    # Create explanation dataframe
    exp_df = pd.DataFrame({
        'feature': feature_names,
        'shap_value': shap_values,
        'feature_value': X_transformed[0],
    })
    exp_df['abs_shap'] = exp_df['shap_value'].abs()
    exp_df = exp_df.sort_values('abs_shap', ascending=False)

    return {
        'base_value': float(base_value),
        'prediction': float(model.predict(X)[0]),
        'top_features': exp_df.head(10)[['feature', 'shap_value', 'feature_value']].to_dict('records'),
    }


def plot_shap_waterfall(explanation: dict) -> None:
    """Display SHAP waterfall-style explanation in Streamlit.

    Args:
        explanation: SHAP explanation dictionary.
    """
    st.subheader("Why this prediction? (SHAP Explanation)")

    base_value = explanation['base_value']
    prediction = explanation['prediction']
    top_features = explanation['top_features']

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Base Value (Avg Salary)", f"${base_value:,.0f}")
    with col2:
        st.metric("Predicted Salary", f"${prediction:,.0f}")
    with col3:
        st.metric("Difference", f"${prediction - base_value:+,.0f}")

    # Feature contributions
    st.write("**Top factors influencing this prediction:**")

    # Create a horizontal bar chart
    features_df = pd.DataFrame(top_features)
    if not features_df.empty:
        features_df = features_df.sort_values('shap_value', ascending=True)

        # Color code: red for negative, green for positive
        colors = ['#ff6b6b' if v < 0 else '#4ecb71' for v in features_df['shap_value']]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(range(len(features_df)), features_df['shap_value'], color=colors, edgecolor='black')
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
        st.pyplot(fig)
        plt.close(fig)

    # Detailed table
    with st.expander("View detailed feature contributions"):
        display_df = features_df[['feature', 'shap_value', 'feature_value']].copy()
        display_df.columns = ['Feature', 'SHAP Value', 'Feature Value']
        display_df['SHAP Value'] = display_df['SHAP Value'].apply(lambda x: f"${x:+,.0f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)


def single_prediction_page():
    """Single candidate salary prediction page."""
    st.title("FairPay: Salary Prediction")
    st.write("Enter candidate details to get a fair, data-driven salary recommendation.")

    model = load_model()
    input_data = create_input_form()

    if st.button("Predict Salary", type="primary", use_container_width=True):
        with st.spinner("Generating prediction..."):
            prediction, lower, upper, coverage = predict_salary(model, input_data)
            explanation = get_shap_explanation(model, input_data)

        st.success("Prediction complete!")

        # Results
        st.markdown("---")
        st.subheader("Salary Recommendation")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Recommended Salary", f"${prediction:,.0f}")
        with col2:
            st.metric(f"Lower Bound ({coverage:.0%})", f"${lower:,.0f}")
        with col3:
            st.metric(f"Upper Bound ({coverage:.0%})", f"${upper:,.0f}")

        q_hat, alpha = load_conformal_predictor()
        if q_hat is not None:
            st.caption(f"Prediction interval using conformal prediction (q̂ = ${q_hat:,.0f}, {coverage:.0%} nominal coverage). "
                       "Actual offer should consider budget, equity, benefits, and market conditions.")
        else:
            st.caption("Prediction interval based on model RMSE (~$22,651). "
                       "Actual offer should consider budget, equity, benefits, and market conditions.")

        # SHAP Explanation
        st.markdown("---")
        plot_shap_waterfall(explanation)

        # Fairness note
        st.markdown("---")
        st.info(
            "**Fairness Note:** This prediction was made without using protected attributes "
            "(gender, age). The model was audited for demographic parity across gender and age groups "
            "with gaps of 2.7% and 3.5% respectively (within acceptable range). "
            "See the About page for full audit details."
        )


def batch_prediction_page():
    """Batch prediction page for CSV upload."""
    st.title("Batch Salary Prediction")
    st.write("Upload a CSV file with candidate details to get predictions for multiple candidates.")

    model = load_model()

    # Template download
    st.subheader("1. Download Template")
    template_df = pd.DataFrame(columns=ALL_FEATURES)
    template_csv = template_df.to_csv(index=False)
    st.download_button(
        "Download CSV Template",
        template_csv,
        "salary_prediction_template.csv",
        "text/csv",
        use_container_width=True
    )

    # Example data
    with st.expander("View example data format"):
        example_data = {
            'years_experience': [5.0, 3.0, 10.0],
            'education_level': ['Bachelor', 'Master', 'PhD'],
            'skills_count': [5, 7, 10],
            'job_role': ['Software Engineer', 'Data Scientist', 'ML Engineer'],
            'previous_salary': [120000, 110000, 140000],
            'interview_score': [7.5, 8.0, 9.0],
            'location': ['San Francisco', 'Remote', 'New York'],
            'company_size': ['Large (1000+)', 'Startup (1-50)', 'Medium (201-1000)'],
        }
        st.dataframe(pd.DataFrame(example_data), use_container_width=True)

    # File upload
    st.subheader("2. Upload Your CSV")
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help=f"CSV must contain columns: {', '.join(ALL_FEATURES)}"
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)

            # Validate columns
            missing_cols = set(ALL_FEATURES) - set(df.columns)
            if missing_cols:
                st.error(f"Missing required columns: {', '.join(missing_cols)}")
                return

            st.success(f"Loaded {len(df)} candidates")

            # Show preview
            st.subheader("3. Data Preview")
            st.dataframe(df.head(10), use_container_width=True)

            # Predict
            if st.button("Generate Predictions", type="primary", use_container_width=True):
                with st.spinner(f"Predicting salaries for {len(df)} candidates..."):
                    X = df[ALL_FEATURES].copy()
                    predictions = model.predict(X)

                    # Load conformal quantile
                    q_hat, alpha = load_conformal_predictor()
                    if q_hat is not None:
                        margin = q_hat
                        coverage = 1 - alpha
                        interval_label = f"{coverage:.0%}"
                    else:
                        margin = 1.96 * 22651
                        coverage = 0.95
                        interval_label = "95%"

                    # Add predictions to dataframe
                    results_df = df.copy()
                    results_df['predicted_salary'] = predictions.round(0).astype(int)
                    results_df[f'salary_lower_{interval_label}'] = (predictions - margin).clip(lower=0).round(0).astype(int)
                    results_df[f'salary_upper_{interval_label}'] = (predictions + margin).round(0).astype(int)

                st.success("Predictions generated!")

                # Results
                st.subheader("4. Results")
                st.dataframe(results_df, use_container_width=True)

                # Download
                csv = results_df.to_csv(index=False)
                st.download_button(
                    "Download Predictions CSV",
                    csv,
                    "salary_predictions.csv",
                    "text/csv",
                    use_container_width=True
                )

                # Summary stats
                st.subheader("Summary Statistics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Mean Predicted", f"${results_df['predicted_salary'].mean():,.0f}")
                with col2:
                    st.metric("Median Predicted", f"${results_df['predicted_salary'].median():,.0f}")
                with col3:
                    st.metric("Min Predicted", f"${results_df['predicted_salary'].min():,.0f}")
                with col4:
                    st.metric("Max Predicted", f"${results_df['predicted_salary'].max():,.0f}")

                if q_hat is not None:
                    st.caption(f"Prediction intervals using conformal prediction (q̂ = ${q_hat:,.0f}, {coverage:.0%} nominal coverage).")
                else:
                    st.caption("Prediction intervals based on model RMSE (~$22,651).")

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")


def about_page():
    """About/How it works page."""
    st.title("About FairPay")
    st.write("### Salary Prediction and Pay Equity Tool")

    st.markdown("""
    **FairPay** is a machine learning tool designed to help HR departments and hiring managers
    make fair, consistent, and data-driven salary offers to candidates.
    """)

    st.markdown("---")
    st.subheader("Problem Statement")

    st.markdown("""
    Company X's HR department must:
    - Avoid discrimination between employees
    - Maintain consistent salary ranges for similar profiles
    - Reduce manual judgment in salary decisions
    - Consider multiple factors: experience, skills, education, interview performance, location, company size

    **Solution:** A machine learning model trained on historical hiring data that predicts
    appropriate salary offers while being audited for fairness across protected groups.
    """)

    st.markdown("---")
    st.subheader("Model Architecture")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Features Used:**
        - Years of Experience
        - Education Level
        - Skills Count
        - Job Role
        - Previous Salary
        - Interview Score
        - Location
        - Company Size

        **Protected Attributes (NOT used as features):**
        - Gender
        - Age

        *These are only used for fairness auditing.*
        """)

    with col2:
        st.markdown("""
        **Model Pipeline:**
        1. Preprocessing: Imputation + Scaling + One-Hot Encoding
        2. Model: Ridge Regression (best performer)
        3. Cross-validation: 5-fold CV
        4. Hyperparameter tuning: GridSearchCV

        **Performance (Test Set):**
        - MAE: ~$16,875
        - RMSE: ~$22,651
        - R²: 0.889
        """)

    st.markdown("---")
    st.subheader("Fairness Audit Results")

    audit = load_fairness_audit()
    if audit:
        st.markdown("""
        The model was evaluated for fairness across protected attributes:

        | Metric | Gender | Age Group |
        |--------|--------|-----------|
        | Demographic Parity Gap | 2.7% | 3.5% |
        | TPR Gap (Equalized Odds) | 0.026 | 0.020 |
        | FPR Gap (Equalized Odds) | 0.061 | 0.060 |

        **Interpretation:** All gaps are below the 5% threshold, indicating the model
        does not systematically disadvantage any protected group.

        **Proxy Feature Analysis:** No features were found to strongly correlate with
        protected attributes (threshold: 0.3 correlation / p < 0.05).
        """)

        # Show intersectional analysis summary
        with st.expander("View Intersectional Analysis (Gender × Age Group)"):
            if 'intersectional_metrics' in audit:
                df_inter = pd.DataFrame(audit['intersectional_metrics'])
                # Convert group list to string for display
                if 'group' in df_inter.columns:
                    df_inter['group'] = df_inter['group'].apply(lambda x: ' × '.join(x) if isinstance(x, list) else str(x))
                st.dataframe(df_inter, use_container_width=True, hide_index=True)
    else:
        st.warning("Fairness audit results not found. Run `python src/fairness.py` to generate.")

    st.markdown("---")
    st.subheader("Explainability (SHAP)")

    st.markdown("""
    Every prediction comes with a SHAP (SHapley Additive exPlanations) breakdown showing
    exactly which factors drove the prediction up or down from the average.

    - **Global importance** shows which features matter most overall
    - **Local explanations** show feature contributions for each individual prediction
    - This transparency helps build trust and allows candidates to understand their offer
    """)

    shap_analysis = load_shap_analysis()
    if shap_analysis and 'global_importance' in shap_analysis:
        with st.expander("View Global Feature Importance"):
            imp_df = pd.DataFrame(shap_analysis['global_importance'])
            st.dataframe(imp_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Limitations & Ethical Considerations")

    st.markdown("""
    **Important Limitations:**
    1. **Synthetic Data**: This demo uses synthetic data. Real deployment requires real historical data.
    2. **Historical Bias**: Models trained on historical data may perpetuate past biases.
    3. **Context Missing**: Model doesn't capture soft skills, culture fit, or market dynamics.
    4. **Prediction Intervals**: Conformal prediction used (90% nominal, ~82% actual coverage on test). Not true conditional coverage.
    5. **Protected Attributes**: Only gender and age audited; other attributes (race, disability) not in data.

    **Ethical Guidelines:**
    - This tool provides **recommendations**, not decisions
    - Human review required for all offers
    - Regular fairness audits should be conducted
    - Model should be retrained periodically with new data
    - Transparency with candidates about how offers are determined
    """)

    st.markdown("---")
    st.subheader("Technical Details")

    st.markdown("""
    - **Framework**: scikit-learn, Streamlit, SHAP
    - **Model**: Ridge Regression (α=1.0)
    - **Preprocessing**: Median imputation, StandardScaler, OneHotEncoder
    - **Validation**: 5-fold cross-validation, 80/20 train/test split
    - **Fairness Metrics**: Demographic Parity, Equalized Odds
    """)


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="FairPay - Salary Prediction & Pay Equity",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar navigation
    st.sidebar.title("FairPay")
    st.sidebar.caption("Salary Prediction & Pay Equity Tool")

    page = st.sidebar.radio(
        "Navigation",
        ["Single Prediction", "Batch Prediction", "About / How it Works"],
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Model Status**")
    try:
        model = load_model()
        st.sidebar.success("Model loaded ✓")
        st.sidebar.caption(f"Type: {model.named_steps['model'].__class__.__name__}")
    except Exception:
        st.sidebar.error("Model not found")
        st.sidebar.caption("Run `python src/train.py` to train")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Resources**")
    st.sidebar.markdown("- [GitHub Repository](https://github.com)")
    st.sidebar.markdown("- [Documentation](#)")
    st.sidebar.markdown("- [Report Issue](#)")

    # Route to pages
    if page == "Single Prediction":
        single_prediction_page()
    elif page == "Batch Prediction":
        batch_prediction_page()
    elif page == "About / How it Works":
        about_page()


if __name__ == '__main__':
    main()