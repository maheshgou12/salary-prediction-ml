import streamlit as st
import pickle
import os
import numpy as np

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Salary Predictor",
    page_icon="💼",
    layout="centered"
)

# ---------------- LOAD MODEL SAFELY ----------------
model_path = os.path.join(os.path.dirname(__file__), "salary_model.pkl")

@st.cache_resource
def load_model():
    with open(model_path, "rb") as f:
        return pickle.load(f)

model = load_model()

# ---------------- TITLE ----------------
st.markdown(
    "<h1 style='text-align:center;color:#2E86C1;'>💼 Salary Prediction System</h1>",
    unsafe_allow_html=True
)

st.markdown("---")

# ---------------- SIDEBAR INPUT ----------------
st.sidebar.header("Enter Candidate Details")

exp = st.sidebar.slider("Experience (Years)", 0, 15, 1)
test = st.sidebar.slider("Test Score", 0, 10, 5)
interview = st.sidebar.slider("Interview Score", 0, 10, 5)

st.write("### Candidate Inputs")
st.write("Experience:", exp)
st.write("Test Score:", test)
st.write("Interview Score:", interview)

st.markdown("---")

# ---------------- PREDICTION ----------------
if st.button("Predict Salary"):
    try:
        prediction = model.predict([[exp, test, interview]])
        st.success(f"🎯 Predicted Expected CTC: {prediction[0]:.2f} LPA")
    except Exception as e:
        st.error("Prediction error. Please try again.")

st.markdown("---")

# ---------------- MODEL PERFORMANCE ----------------
st.markdown("### 📈 Model Performance")
st.write("Random Forest R2 Score: 0.91")
st.progress(0.91)

st.markdown("---")

# ---------------- FEATURE IMPORTANCE ----------------
st.markdown("### 🔎 Important Features")
st.image("feature_importance.png", width="stretch")

st.markdown("---")

# ---------------- PROJECT INFO ----------------
st.write("### 📊 Project Description")
st.write(
    """
This system predicts expected salary using Machine Learning.
Model used: Random Forest Regression.
It analyzes candidate experience, test performance and interview score.
"""
)

# ---------------- FOOTER ----------------
st.markdown(
    "<p style='text-align:center'>Developed for Placement Project 🚀</p>",
    unsafe_allow_html=True
)
