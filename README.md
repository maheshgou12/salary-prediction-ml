# FairSalary AI — Salary Prediction & Pay Equity Platform

End-to-end ML platform that predicts fair salaries and audits for bias across protected groups (gender, age).

- **Backend**: FastAPI + JWT auth + SQLite (`backend/`)
- **Frontend**: React 18 + TypeScript + Vite + Tailwind (`frontend/`)
- **ML**: Stacking Ensemble (R² 0.913, MAE $14k), conformal intervals, SHAP, fairness auditing (`ml/`)

## Live Demo

- Frontend: _add your Vercel link here after deploy_
- API docs: _add your Render link here after deploy_ (`/docs`)

Demo login: `demo@test.com` / `Password123`

## Quick Start

```bash
pip install -r FairSalaryAI/backend/requirements.txt
cd FairSalaryAI/backend && python -m uvicorn app.main:app --port 8000

cd FairSalaryAI/frontend && npm install && npm run dev
```

- UI: http://localhost:5173
- API docs: http://localhost:8000/docs

## Documentation

Full docs in [FairSalaryAI/README.md](FairSalaryAI/README.md) and [FairSalaryAI/docs](FairSalaryAI/docs).

## Deployment

- Backend → Render (Blueprint reads `render.yaml`)
- Frontend → Vercel (Root Directory: `FairSalaryAI/frontend`, env `VITE_API_URL`)
