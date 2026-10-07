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
