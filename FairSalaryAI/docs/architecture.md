# FairSalary AI - Architecture Documentation

## System Overview

FairSalary AI is a microservices-based application with three main components:

1. **Frontend** - React + TypeScript SPA (Vite + Tailwind)
2. **Backend** - FastAPI REST API (Python + SQLAlchemy + PostgreSQL)
3. **ML Pipeline** - Scikit-learn/XGBoost models with SHAP/Fairlearn integration

## Architecture Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│     Backend     │────▶│   PostgreSQL    │
│   (React/Vite)  │     │   (FastAPI)     │     │   (Supabase)    │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
              ┌───────────────┐       ┌───────────────┐
              │  ML Pipeline  │       │   ML Models   │
              │  (Training)   │       │  (Artifacts)  │
              └───────────────┘       └───────────────┘
```

## Data Flow

### Prediction Request Flow

1. **Client** submits candidate profile via `/api/predict`
2. **Backend** validates input with Pydantic schemas
3. **PredictionService** loads model pipeline and makes prediction
4. **Similar profiles** queried from PostgreSQL
5. **SHAP explanations** generated via KernelExplainer
6. **Fairness disclaimer** attached
7. **Prediction** stored in database with user ownership
8. **Response** returned with salary range, explanation, similar profiles

### Training Flow

1. **Data Generation** → Synthetic CSV
2. **Preprocessing** → ColumnTransformer pipeline
3. **Model Training** → Multiple algorithms + Optuna tuning
4. **Ensemble Selection** → Stacking ensemble
5. **Fairness Audit** → Fairlearn metrics
6. **Conformal Prediction** → Calibration set
7. **SHAP Analysis** → Global + local explanations
8. **Model Artifacts** → Joblib serialization

## Component Details

### Frontend (React + Vite + TypeScript)

```
frontend/
├── src/
│   ├── components/     # Reusable UI (Layout, forms, charts)
│   ├── pages/          # Page components (Home, Predict, Results, etc.)
│   ├── services/       # API client (Axios with interceptors)
│   ├── hooks/          # Custom hooks (useAuth, etc.)
│   ├── utils/          # Helpers (formatting, validation)
│   ├── App.tsx         # Routes + providers
│   └── main.tsx        # Entry point
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
└── Dockerfile
```

**Key Libraries:**
- React 18 + TypeScript
- Vite for fast HMR
- Tailwind CSS for styling
- React Router v6 for routing
- Axios for API (with auth interceptors)
- Recharts for visualizations
- Lucide React for icons

### Backend (FastAPI + SQLAlchemy)

```
backend/
├── app/
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py            # Pydantic Settings
│   ├── database.py          # SQLAlchemy engine + session
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic request/response
│   ├── dependencies.py      # FastAPI dependencies
│   ├── routes/              # API route modules
│   │   ├── auth.py          # /api/auth/*
│   │   ├── prediction.py    # /api/predict/*
│   │   ├── fairness.py      # /api/fairness/*
│   │   ├── model.py         # /api/model/*
│   │   └── health.py        # /health
│   ├── services/            # Business logic
│   │   ├── prediction_service.py
│   │   ├── fairness_service.py
│   └── security/            # Auth utilities
│       ├── auth.py          # JWT tokens
│       └── password.py      # bcrypt hashing
├── alembic/                 # Database migrations
├── tests/                   # Pytest tests
├── requirements.txt
├── Dockerfile
└── alembic.ini
```

**Key Design Decisions:**
- **Dependency Injection**: FastAPI `Depends()` for DB, auth, services
- **Async/Await**: Native async for I/O (DB, HTTP)
- **Pydantic v2**: Fast validation, serialization
- **SQLAlchemy 2.0**: Modern ORM with async support
- **JWT + bcrypt**: Stateless auth with refresh tokens
- **Rate Limiting**: In-memory (Redis for production)

### ML Pipeline

```
ml/
├── data/
│   ├── raw/              # Raw CSV files
│   └── processed/        # Cleaned parquet files
├── notebooks/            # Jupyter EDA
├── src/
│   ├── data_loader.py    # CSV loading + validation
│   ├── preprocessing.py  # ColumnTransformer pipeline
│   ├── feature_engineering.py  # Feature creation
│   ├── train.py          # Model training + Optuna
│   ├── evaluate.py       # Metrics + comparison
│   ├── fairness.py       # Fairlearn auditing
│   ├── explainability.py # SHAP analysis
│   └── predict.py        # Inference interface
├── models/               # Joblib artifacts
└── scripts/
    └── generate_data.py  # Synthetic data generation
```

**Model Artifacts:**
- `best_model.joblib` - Full pipeline (preprocessor + ensemble)
- `metadata.json` - Version, metrics, feature names
- `fairness_audit.json` - Fairlearn results
- `conformal_summary.json` - Conformal quantile
- `shap_analysis.json` - Global SHAP values

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/me` | Current user info |

### Predictions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/predict` | Single prediction |
| GET | `/api/predict` | List user predictions |
| GET | `/api/predict/{id}` | Get prediction details |

### Fairness
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/fairness` | Dashboard data |
| GET | `/api/fairness/attribute/{attr}` | Specific attribute |
| GET | `/api/fairness/intersectional` | Intersectional analysis |

### Model
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/model/metrics` | Performance metrics |
| GET | `/api/model/info` | Model details |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/health/ready` | Readiness probe |
| GET | `/health/live` | Liveness probe |

## Database Schema

### Tables

1. **users** - Authentication + profile
2. **predictions** - User predictions + results
3. **candidate_profiles** - Historical training data
4. **model_versions** - Model registry

### Key Indexes
- `users.email` (unique)
- `predictions.user_id + created_at`
- `candidate_profiles.job_role + location`
- `candidate_profiles.gender`, `age`

## Security

### Authentication
- **JWT Access Tokens**: 30 min expiry, HS256
- **Refresh Tokens**: 7 days, rotated on use
- **Password Hashing**: bcrypt (12 rounds)
- **Protected Routes**: FastAPI `Depends(get_current_user)`

### Data Protection
- **No PII in ML Features**: Gender/age only for fairness
- **Password Hashing**: bcrypt + salt
- **CORS**: Restricted to frontend origin
- **Rate Limiting**: 60 req/min (Redis in prod)
- **Input Validation**: Pydantic schemas

### Secrets Management
- **Development**: `.env` file (gitignored)
- **Production**: Render/Vercel environment variables
- **Database**: Supabase connection pooling
- **Secrets**: Render/Vercel secret stores

## Deployment Architecture

### Production (Render + Vercel + Supabase)

```
┌─────────────────┐
│     Vercel      │  ← Frontend (React)
│  (Global CDN)   │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│     Render      │  ← Backend API
│  (Web Service)  │
└────────┬────────┘
         │ Internal
         ▼
┌─────────────────┐
│   Supabase      │  ← PostgreSQL
│  (PostgreSQL)   │
└─────────────────┘
```

### Environment Variables

| Variable | Frontend | Backend | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | ✅ | | Backend URL |
| `DATABASE_URL` | | ✅ | PostgreSQL connection |
| `SECRET_KEY` | | ✅ | JWT signing |
| `FRONTEND_URL` | | ✅ | CORS origin |

## Monitoring & Observability

### Health Checks
- `/health` - Full system status
- `/health/ready` - Kubernetes readiness
- `/health/live` - Kubernetes liveness

### Metrics (Prometheus)
- Request latency (histogram)
- Request count (counter)
- Active requests (gauge)
- Prediction latency (histogram)

### Logging
- Structured JSON logs (structlog)
- Request/response logging
- Error tracking (Sentry)

## Scaling Considerations

### Horizontal Scaling
- **Frontend**: Vercel auto-scales
- **Backend**: Render auto-scales (stateless)
- **Database**: Supabase read replicas

### Caching
- **Model**: Loaded in memory at startup
- **Predictions**: Consider Redis for caching
- **Fairness**: Precomputed, cached

### Database
- Connection pooling (SQLAlchemy)
- Read replicas for analytics
- Partitioning for large prediction tables

## Disaster Recovery

### Backups
- **Database**: Supabase daily + point-in-time
- **Models**: Versioned in Git/MLflow
- **Code**: GitHub + GitHub Actions artifacts

### Rollback
- **Backend**: Render rollback to previous deploy
- **Frontend**: Vercel instant rollback
- **Database**: Supabase point-in-time recovery

## Development Workflow

### Local Development
```bash
# Start all services
docker-compose up -d

# Backend only
cd FairSalaryAI/backend
uvicorn app.main:app --reload

# Frontend only
cd FairSalaryAI/frontend
npm run dev
```

### Testing
```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npm run test

# ML
cd ml && pytest tests/ -v
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Future Extensibility

### Planned Features
- [ ] Batch prediction API
- [ ] A/B testing framework
- [ ] Model monitoring + drift detection
- [ ] Advanced intersectional fairness
- [ ] Counterfactual explanations
- [ ] Multi-language support
- [ ] Advanced RBAC
- [ ] Audit logging

### Integration Points
- **HR Systems**: Webhook callbacks
- **ATS**: Greenhouse, Lever integration
- **Payroll**: ADP, Gusto integration
- **Analytics**: Mixpanel, Amplitude