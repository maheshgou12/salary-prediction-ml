# FairSalary AI 💼⚖️

**An Enterprise-Grade, Machine Learning Platform for Fair Compensation Recommendation, Uncertainty Quantification, and Algorithmic Bias Auditing.**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18_TypeScript-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS_v3-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Machine Learning](https://img.shields.io/badge/Ensemble-CatBoost_|_XGBoost_|_LightGBM-FF6F00.svg)](https://scikit-learn.org)
[![Explainability](https://img.shields.io/badge/XAI-SHAP_TreeExplainer-brightgreen.svg)](https://shap.readthedocs.io)
[![Fairness](https://img.shields.io/badge/Fairness-Fairlearn_Auditing-blueviolet.svg)](https://fairlearn.org)
[![Tests](https://img.shields.io/badge/Tests-38_Passed_|_100%25-success.svg)](file:///FairSalaryAI/tests)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌐 Live Deployments

* **Frontend Dashboard (Vercel)**: [https://salary-prediction-ml-ivory.vercel.app](https://salary-prediction-ml-ivory.vercel.app)
* **Backend API Documentation (Render / Swagger)**: [https://fairsalaryy-backend.onrender.com/docs](https://fairsalaryy-backend.onrender.com/docs)
* **Repository**: [https://github.com/maheshgou12/salary-prediction-ml](https://github.com/maheshgou12/salary-prediction-ml)

---

## 📋 The Business Problem (Company X Case Study)

> **Human Resources Challenge**:  
> To ensure there is no discrimination between employees, it is imperative for the Human Resources department of **Company X** to maintain a salary range for each employee with similar profiles.  
> 
> Apart from existing compensation, a considerable number of factors—such as an employee's experience, abilities, and interview scores—are evaluated during hiring. This project provides an automated, auditable system to determine fair compensation offers, minimizing arbitrary human judgment and systematically eliminating wage disparity across protected demographics.

---

## 🌟 Core System Pillars

### 1. Multi-Model Stacking Ensemble ($R^2 = 0.913$)
Evaluates candidate credentials (`experience_years`, `previous_salary`, `interview_score`, `education_level`, `skills_count`, `job_role`, `company_size`, `location`) using a heterogeneous stacking ensemble:
* **CatBoost Regressor** (depth=4, iterations=276)
* **XGBoost Regressor** (depth=3, n_estimators=289)
* **LightGBM Regressor** (num_leaves=97, n_estimators=218)
* **Ridge Meta-Learner** for final blending
* **Test Metrics**: $R^2 = 0.913$, $\text{MAE} = \$14,142$, $\text{RMSE} = \$18,503$.

### 2. Conformal Prediction Salary Ranges
Rather than presenting a risky, single-point salary recommendation, the system computes **statistically guaranteed prediction intervals**:
$$\text{Salary Range} = [\hat{y} - \hat{q}, \; \hat{y} + \hat{q}]$$
with **90% coverage guarantee** ($\alpha = 0.10$), providing HR with clear minimum, target, and maximum offer boundaries.

### 3. Explainable AI with SHAP Tree Attributions
Eliminates opaque "black box" decisions. For every candidate evaluated, the engine computes exact Shapley values using `shap.TreeExplainer`, detailing the exact positive or negative dollar impact of each credential on the salary recommendation.

### 4. Demographic Parity & Fairness Auditing
Protected attributes (`gender`, `age`) are **strictly excluded** from feature inputs to prevent direct disparate treatment. An automated Fairlearn audit suite computes:
* **Demographic Parity Difference**
* **Equalized Odds / Disparity Ratios**
* **EEOC 80% (Four-Fifths) Adverse Impact Rule**
* **Instant CSV Export** for HR compliance records

### 5. Enterprise Authentication & Security
* **JWT Authentication**: Passwords hashed with `bcrypt` (12 rounds).
* **Non-Expiring Work Sessions**: Long-lived access tokens (1 year) paired with automatic refresh interceptors so evaluators and recruiters never experience mid-session session timeouts.
* **SMTP Password Reset Flow**: Registered users can reset credentials via cryptographic 30-minute JWT links delivered directly to their email inbox.

---

## 🏗️ System Architecture

```text
       ┌────────────────────────────────────────────────────────┐
       │                React 18 + TypeScript UI                │
       │     (Tailwind CSS, Recharts, Lucide, Dark/Light Mode)  │
       └───────────────────────────┬────────────────────────────┘
                                   │ HTTP / REST / Bearer JWT
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                  FastAPI Backend Gateway               │
       │    (Pydantic v2, CORS Middleware, Structured Logging)   │
       └─────┬─────────────────────┬──────────────────────┬─────┘
             │                     │                      │
             ▼                     ▼                      ▼
 ┌──────────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
 │  ML Inference Engine │ │ Database Layer  │ │  Security & Alerts  │
 │ ├─ Stacking Ensemble │ │ ├─ SQLite /     │ │ ├─ PyJWT Auth       │
 │ ├─ Conformal Range   │ │ │  Neon Postgres│ │ ├─ Bcrypt Hashing   │
 │ ├─ SHAP Explainer    │ │ ├─ 5,000 Peers  │ │ └─ SMTP Mail Service│
 │ └─ Fairlearn Audit   │ │ └─ SQLAlchemy   │ │    (IPv4 Transport) │
 └──────────────────────┘ └─────────────────┘ └─────────────────────┘
```

---

## 📁 Repository Structure

```text
salary-prediction-ml/
├── README.md                      # Primary project portfolio documentation
├── render.yaml                    # Production deployment blueprint (Render)
├── .gitignore                     # Git tracking exclusions
│
└── FairSalaryAI/
    ├── frontend/                  # React 18 + Vite + TypeScript application
    │   ├── src/
    │   │   ├── pages/             # Predict, Results, Fairness, History, Auth
    │   │   ├── components/        # Charts, navigation, form controls
    │   │   ├── services/          # Axios API client with refresh interceptors
    │   │   └── context/           # Authentication state context
    │   ├── package.json
    │   └── vite.config.ts
    │
    ├── backend/                   # FastAPI REST API
    │   ├── app/
    │   │   ├── routes/            # predict, fairness, auth, model, health
    │   │   ├── services/          # prediction_service, fairness_service, email
    │   │   ├── security/          # JWT tokens and password hashing
    │   │   ├── models.py          # SQLAlchemy ORM definitions
    │   │   ├── schemas.py         # Pydantic request/response models
    │   │   └── config.py          # Environment settings and DB resolution
    │   ├── fairsalary.db          # Persistent SQLite database (5,000 profiles)
    │   └── requirements.txt
    │
    ├── ml/                        # Machine Learning Pipeline
    │   ├── models/                # best_model.joblib, conformal_summary.json
    │   ├── src/                   # train.py, predict.py, explain.py, uncertainty.py
    │   ├── data/                  # Synthetic training datasets and benchmarks
    │   └── notebooks/             # 01_eda.ipynb exploratory data analysis
    │
    ├── scripts/                   # seed_db.py database population scripts
    └── tests/                     # Automated pytest suite (38 unit & integration tests)
```

---

## 🚀 Quick Start (Local Setup)

### Prerequisites
* Python 3.10+
* Node.js 18+ and npm

### 1. Clone the Repository
```bash
git clone https://github.com/maheshgou12/salary-prediction-ml.git
cd salary-prediction-ml
```

### 2. Backend Setup
```bash
cd FairSalaryAI/backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* Backend API runs at: `http://localhost:8000`
* Interactive API Documentation (Swagger UI): `http://localhost:8000/docs`

### 3. Frontend Setup
In a new terminal window:
```bash
cd FairSalaryAI/frontend
npm install
npm run dev
```
* Frontend Dashboard runs at: `http://localhost:5173`

---

## 🧪 Automated Testing

The codebase includes an automated test suite verifying all 4 business requirements, preprocessing pipelines, model inference, and REST endpoints:

```bash
cd FairSalaryAI
python -m pytest tests -v
```

```text
======================== test session starts ========================
collected 38 items

tests/test_api_endpoints.py::TestHealthEndpoints::test_health_check PASSED
tests/test_api_endpoints.py::TestAuthEndpoints::test_forgot_and_reset_password PASSED
tests/test_api_endpoints.py::TestPredictionEndpoints::test_predict_salary_authenticated PASSED
tests/test_api_endpoints.py::TestFairnessEndpoints::test_fairness_dashboard PASSED
tests/test_api_endpoints.py::TestFairnessEndpoints::test_gender_attribute_fairness PASSED
tests/test_preprocessing.py::TestFeatureConfiguration::test_protected_attributes_not_in_features PASSED
tests/test_preprocessing.py::TestPrediction::test_model_predicts_single_sample PASSED
...
======================== 38 passed in 14.50s ========================
```

---

## 🛠️ Step-by-Step "Forever Free" Setup Guide

### 1. Permanent PostgreSQL Database (Never Expires)
Instead of Render's 30-day temporary database, use **[Neon.tech](https://neon.tech/)** (or Supabase):
1. Sign up at **[neon.tech](https://neon.tech/)** (Free forever, no credit card required).
2. Click **Create Project** (Name: `fairsalary-db`).
3. Under **Connection Details**, copy the PostgreSQL connection string. It looks like:
   ```text
   postgresql://user:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. Save this string. This database is permanent and will **never be deleted**.
5. *Note*: The backend automatically runs `init_db()` and auto-seeds all 5,000 historical candidate profiles into Neon upon first startup.

---

### 2. Backend on Render (Always Awake 24/7)
1. Sign in to **[render.com](https://render.com/)**.
2. Click **New +** ➔ **Web Service** (not blueprint).
3. Connect your GitHub repository (`maheshgou12/salary-prediction-ml`).
4. Set the following settings:
   * **Name**: `fairsalary-backend`
   * **Region**: Oregon (US West) or Ohio (US East)
   * **Root Directory**: `.` (leave empty or root)
   * **Runtime**: `Python 3`
   * **Build Command**: `pip install -r FairSalaryAI/backend/requirements.txt`
   * **Start Command**: `cd FairSalaryAI/backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   * **Instance Type**: `Free`
5. Under **Environment Variables**, add:
   * `DATABASE_URL`: *(Your Neon PostgreSQL connection string from Step 1)*
   * `SECRET_KEY`: `my_super_secret_production_key_2026_xyz`
   * `ACCESS_TOKEN_EXPIRE_MINUTES`: `525600` *(1 full year - tokens never expire)*
   * `REFRESH_TOKEN_EXPIRE_DAYS`: `365` *(1 full year)*
   * `FRONTEND_URL`: `https://frontend-six-zeta-70.vercel.app`
   * `SMTP_HOST`: `smtp.gmail.com`
   * `SMTP_PORT`: `587`
   * `SMTP_USER`: `maheshburra2712@gmail.com`
   * `SMTP_PASSWORD`: `your-16-character-app-password`
6. Click **Deploy Web Service**. You will get your backend URL:  
   👉 **`https://fairsalary-backend.onrender.com`**

---

### 3. Keep Backend Awake 24/7 (Zero Sleep / Zero Cold Starts)
Render free services sleep after 15 minutes of inactivity. To keep it running 24/7 for free:
1. Go to **[uptimerobot.com](https://uptimerobot.com/)** (100% free account).
2. Click **Add New Monitor**:
   * **Monitor Type**: `HTTP(s)`
   * **Friendly Name**: `FairSalary Backend Keep-Alive`
   * **URL (or IP)**: `https://fairsalary-backend.onrender.com/health`
   * **Monitoring Interval**: `Every 5 minutes`
3. Click **Create Monitor**.
4. **Result**: UptimeRobot pings your backend `/health` endpoint every 5 minutes so it **never sleeps**, ensuring instant responses whenever someone opens your application.

---

### 4. Zero-Cost ML & Explainability Guarantee
* **No External API Keys or Token Costs Needed**: Unlike LLM-only APIs that charge per token, FairSalary AI's heterogeneous Stacking Ensemble (CatBoost, XGBoost, LightGBM), SHAP Tree Explainer, and Conformal Uncertainty intervals execute directly within the backend container.
* **100% Reliable**: Zero rate limits, zero quotas, and zero monthly API charges.

---

### 5. Frontend on Vercel (Fast & Free Forever)
1. Go to **[vercel.com](https://vercel.com/)** and click **Add New...** ➔ **Project**.
2. Select your repository: `maheshgou12/salary-prediction-ml`.
3. Set **Root Directory** to `FairSalaryAI/frontend`.
4. Under **Environment Variables**, add:
   * **Name**: `VITE_API_URL`
   * **Value**: `https://fairsalary-backend.onrender.com`
5. Click **Deploy**. You will get your live frontend URL:  
   👉 **`https://frontend-six-zeta-70.vercel.app`**

---

### 📋 Summary Checklist

* [x] **Database**: Permanent on Neon PostgreSQL (no 30-day limit, auto-seeded).
* [x] **Backend**: Kept awake 24/7 by UptimeRobot pinging `/health` (no cold starts).
* [x] **Sessions**: 1-year non-expiring JWT tokens (`ACCESS_TOKEN_EXPIRE_MINUTES=525600`).
* [x] **Frontend**: Global edge CDN delivery on Vercel.
* [x] **Compliance**: Company X HR requirements fully audited and satisfied.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
