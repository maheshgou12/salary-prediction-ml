import streamlit as st
import pickle
import numpy as np

# Page config
st.set_page_config(
    page_title="Salary Predictor",
    page_icon="💼",
    layout="centered"
)

# Load model
model = pickle.load(open("salary_model.pkl", "rb"))

# Title
st.markdown("<h1 style='text-align: center; color: #2E86C1;'>💼 Salary Prediction System</h1>", unsafe_allow_html=True)

st.markdown("---")

# Sidebar inputs
st.sidebar.header("Enter Candidate Details")

exp = st.sidebar.slider("Experience (Years)", 0, 15, 1)
test = st.sidebar.slider("Test Score", 0, 10, 5)
interview = st.sidebar.slider("Interview Score", 0, 10, 5)

st.write("### Candidate Inputs")
st.write("Experience:", exp)
st.write("Test Score:", test)
st.write("Interview Score:", interview)

st.markdown("---")

# Prediction button
if st.button("Predict Salary"):

    prediction = model.predict([[exp, test, interview]])

    st.success(f"🎯 Predicted Expected CTC: {prediction[0]:.2f} LPA")

st.markdown("---")
st.markdown("### 📈 Model Performance")

st.write("Random Forest R2 Score: 0.91")
st.progress(91)



# Project info
st.write("### 📊 Project Description")
st.write("""
This system predicts expected salary using Machine Learning.
Model used: Random Forest Regression.
It analyzes candidate experience, test performance and interview score.
""")

# Footer
st.markdown(
    "<p style='text-align:center'>Developed for Placement Project 🚀</p>",
    unsafe_allow_html=True
)

st.markdown("### 🔎 Important Features")

st.image("feature_importance.png", use_container_width=True)