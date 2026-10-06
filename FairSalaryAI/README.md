# FairSalary AI

**AI-Powered Fair Salary Recommendation and Bias Analysis Platform**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6.svg)](https://typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Project Overview

FairSalary AI is a production-ready web application that helps organizations make fair, data-driven salary decisions while actively monitoring for bias. Built as an internship-level AI/ML portfolio project, it demonstrates end-to-end ML engineering skills from data generation to deployment.

### Business Problem

Organizations struggle with:
- **Unconscious bias** in salary decisions
- **Inconsistent** compensation for similar roles
- **Lack of transparency** in how salaries are determined
- **No systematic fairness auditing** of compensation practices

### Solution

FairSalary AI provides:
1. **Salary Prediction** - ML-powered salary recommendations based on candidate profile
2. **Salary Ranges** - Confidence intervals instead of single numbers
3. **Explainability** - SHAP-based feature contribution analysis
3. **Similar Profiles** - Historical comparison with similar candidates
4. **Fairness Dashboard** - Bias analysis across protected groups
5. **Secure History** - JWT-authenticated prediction tracking

---

## ✨ Features

### Core Functionality
- 🎯 **Salary Prediction** - XGBoost/Random Forest ensemble with preprocessing pipeline
- 📊 **Salary Range** - Conformal prediction intervals (not fake confidence scores)
- 🔍 **SHAP Explanations** - Feature-level contribution breakdown
- 👥 **Similar Profiles** - k-NN historical comparison with salary statistics
- ⚖️ **Fairness Analysis** - Fairlearn-powered bias detection across protected groups

### Technical Features
- 🔐 **JWT Authentication** - Secure register/login with bcrypt password hashing
- 🗄️ **PostgreSQL** - SQLAlchemy ORM with proper migrations
- 🐳 **Docker Ready** - Multi-container setup for local and production
- 🧪 **Test Coverage** - Pytest for backend, Vitest for frontend
- 📱 **Responsive UI** - Mobile-first React + Tailwind CSS

---

## 🏗️ Architecture

```
FairSalaryAI/
├── frontend/                 # React + Vite + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Page components (Home, Predict, Results, etc.)
│   │   ├── services/         # API clients
│   │   ├── hooks/            # Custom React hooks
│   │   └── utils/            # Helpers
│   └── package.json
│
├── backend/                  # FastAPI + SQLAlchemy + PostgreSQL
│   ├── app/
│   │   ├── main.py           # FastAPI app factory
│   │   ├── config.py         # Settings management
│   │   ├── database.py       # DB connection & session
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── dependencies.py   # FastAPI dependencies
│   │   ├── routes/           # API route modules
│   │   ├── services/         # Business logic services
│   │   └── security/         # Auth & password utilities
│   └── requirements.txt
│
├── ml/                       # Machine Learning Pipeline
│   ├── data/                 # Raw & processed data
│   ├── notebooks/            # EDA & experimentation
│   ├── src/                  # ML source code
│   │   ├── data_loader.py
│   │   ├── preprocessing.py
│   │   ├── feature_engineering.py
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   ├── fairness.py
│   │   ├── explainability.py
│   │   └── predict.py
│   └── models/               # Trained model artifacts
│
├── tests/                    # Automated tests
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
└── docker-compose.yml        # Local development stack
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Recharts, Axios |
| **Backend** | FastAPI, SQLAlchemy 2.0, Pydantic v2, PostgreSQL |
| **ML** | Scikit-learn, XGBoost, SHAP, Fairlearn, Pandas, NumPy |
| **Auth** | JWT (PyJWT), bcrypt (passlib) |
| **DevOps** | Docker, Docker Compose, GitHub Actions |
| **Deploy** | Frontend: Vercel, Backend: Render, DB: Supabase |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 16+ (or Docker)
- Git

### 1. Clone & Setup

```bash
# Clone repository
git clone <repository-url>
cd FairSalaryAI

# Copy environment file
cp .env.example .env
# Edit .env with your values
```

### 2. Start with Docker (Recommended)

```bash
# Start all services (PostgreSQL, Backend, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f

# Access:
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 3. Manual Setup (Development)

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (if using Alembic)
# alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

---

## 📊 Machine Learning Pipeline

### Data Generation
```bash
cd ml
python scripts/generate_data.py
```
Generates 5,000+ synthetic records with realistic relationships:
- Experience → Salary (positive correlation)
- Skills → Salary (specialized skills premium)
- Role/Education/Location/Company Size effects
- Realistic noise for meaningful prediction task

### Training
```bash
python src/train.py
```
Trains and compares:
- Linear Regression (baseline)
- Random Forest Regressor
- Gradient Boosting Regressor
- XGBoost Regressor

Selects best model by validation MAE + fairness considerations.

### Evaluation
```bash
python src/evaluate.py
```
Computes MAE, RMSE, R² on test set + fairness metrics.

### Fairness Analysis
```bash
python src/fairness.py
```
Fairlearn-powered analysis:
- Demographic parity differences
- Mean prediction by group
- Error rate differences (MAE/RMSE by group)
- Visualization-ready outputs

### Explainability
```bash
python src/explainability.py
```
SHAP explanations:
- Global feature importance
- Local (per-prediction) explanations
- Waterfall plots

---

## 🔐 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/auth/refresh` | Refresh access token |

### Predictions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/predict` | Get salary prediction |
| GET | `/api/predictions` | List user's predictions |
| GET | `/api/predictions/{id}` | Get prediction details |

### Fairness & Model
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/fairness` | Fairness dashboard data |
| GET | `/api/model/metrics` | Model performance metrics |
| GET | `/health` | Health check |

### Example Prediction Request
```json
POST /api/predict
{
  "experience_years": 3,
  "education": "Masters",
  "job_role": "Data Scientist",
  "location": "Bangalore",
  "skills": ["Python", "SQL", "Machine Learning", "PyTorch"],
  "industry": "Technology",
  "company_size": "Medium",
  "employment_type": "Full-time"
}
```

### Example Prediction Response
```json
{
  "predicted_salary": 1250000,
  "minimum_salary": 1150000,
  "maximum_salary": 1350000,
  "confidence": 0.87,
  "similar_profiles": {
    "count": 127,
    "median_salary": 1240000,
    "percentile_25": 1150000,
    "percentile_75": 1320000
  },
  "explanation": [
    {"feature": "experience_years", "contribution": 180000, "direction": "positive"},
    {"feature": "skills", "contribution": 120000, "direction": "positive"},
    {"feature": "location", "contribution": -50000, "direction": "negative"}
  ],
  "model_version": "1.0.0",
  "fairness_disclaimer": "This prediction was made without using protected attributes..."
}
```

---

## 🗄️ Database Schema

### Users
- `id` (PK), `email` (unique), `hashed_password`, `full_name`, `is_active`, `created_at`

### Predictions
- `id` (PK), `user_id` (FK), `input_data` (JSONB), `predicted_salary`, `min_salary`, `max_salary`, `confidence`, `model_version`, `similar_profiles` (JSONB), `explanation` (JSONB), `created_at`

### Candidate Profiles (Historical)
- `id` (PK), `experience_years`, `education`, `job_role`, `location`, `skills` (JSONB), `industry`, `company_size`, `employment_type`, `salary`, `gender` (protected, not used for prediction), `created_at`

### Model Versions
- `id` (PK), `version`, `model_type`, `metrics` (JSONB), `fairness_metrics` (JSONB), `created_at`, `is_active`

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm run test

# ML tests
cd ml
python -m pytest tests/ -v
```

### Test Coverage
- ✅ ML: model loading, preprocessing, prediction, invalid input handling
- ✅ API: health, auth, prediction, unauthorized access, invalid requests
- ✅ DB: connection, prediction storage, user management
- ✅ Fairness: metric calculations, missing group handling

---

## 🐳 Docker

### Development Stack
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: fairsalary
      POSTGRES_USER: fairuser
      POSTGRES_PASSWORD: fairpass
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://fairuser:fairpass@postgres:5432/fairsalary
    depends_on: [postgres]

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    environment:
      VITE_API_URL: http://localhost:8000
    depends_on: [backend]
```

```bash
# Build and run
docker-compose up -d --build

# Stop
docker-compose down

# Stop with volumes (resets DB)
docker-compose down -v
```

---

## ☁️ Deployment

### Frontend → Vercel
1. Connect GitHub repo to Vercel
2. Set Root Directory: `frontend`
3. Add Environment Variables:
   - `VITE_API_URL` = `https://your-backend.onrender.com`
4. Deploy

### Backend → Render
1. Create Web Service from GitHub
2. Set Root Directory: `backend`
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables from `.env.example`
4. Add PostgreSQL database (Supabase or Render PostgreSQL)

### Database → Supabase
1. Create Supabase project
2. Get connection string
3. Add to `DATABASE_URL` in backend env
5. Run migrations: `alembic upgrade head`

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System design & data flow |
| [API Documentation](docs/api.md) | Complete API reference |
| [ML Methodology](docs/ml_methodology.md) | Model training & evaluation details |
| [Deployment Guide](docs/deployment.md) | Step-by-step deployment |

---

## ⚠️ Responsible AI & Limitations

### Disclaimer
> **This system provides an AI-assisted salary recommendation based on synthetic demonstration data. It should not be used as the sole basis for employment, compensation, promotion, or other high-impact decisions. Predictions may contain errors or reflect biases present in the underlying data.**

### Privacy Notice
> **Do not upload confidential employee information.** This application uses synthetic data for demonstration. In production, ensure compliance with GDPR, CCPA, and local privacy laws.

### Limitations
- Synthetic data may not reflect real-world distributions
- Fairness metrics are proxies; cannot prove absence of discrimination
- SHAP explanations are model interpretations, not causal proofs
- Confidence intervals are statistical estimates, not guarantees
- Model requires retraining with real organizational data

---

## 🔮 Future Improvements

- [ ] Active learning loop for model improvement
- [ ] Counterfactual explanations
- [ ] Intersectional fairness analysis
- [ ] Batch prediction API
- [ ] Model monitoring & drift detection
- [ ] A/B testing framework
- [ ] Multi-language support
- [ ] Advanced role-based access control

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

Built as an internship-level AI/ML portfolio project demonstrating:
- End-to-end ML engineering
- Production API development
- Modern frontend architecture
- Responsible AI practices
- DevOps & deployment readiness

---

## 🙏 Acknowledgments

- [Fairlearn](https://fairlearn.org/) for fairness metrics
- [SHAP](https://github.com/slundberg/shap) for explainability
- [scikit-learn](https://scikit-learn.org/) for ML foundations
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent framework