# FairSalary AI - Deployment Guide

## Overview

This guide covers deploying FairSalary AI to production using:
- **Frontend**: Vercel (global CDN, automatic HTTPS)
- **Backend**: Render (managed containers, auto-scaling)
- **Database**: Supabase (managed PostgreSQL)

---

## Prerequisites

- GitHub account
- Vercel account
- Render account
- Supabase account
- Domain name (optional)

---

## 1. Database Setup (Supabase)

### Create Project

1. Go to [supabase.com](https://supabase.com) → New Project
2. Choose organization, name: `fairsalary-prod`
3. Set database password (save securely!)
4. Select region closest to users
5. Wait for provisioning (~2 minutes)

### Configure Database

1. Go to **Settings → Database** → Connection pooling
2. Enable **Session Pooler** (port 6543)
3. Note connection string:
   ```
   postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
   ```
4. Run migrations:
   ```bash
   # Local
   cd FairSalaryAI/backend
   DATABASE_URL="postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres" \
   alembic upgrade head
   ```

### Security
- Enable **Row Level Security** on all tables
- Create read-only role for analytics
- Configure **IP allowlist** (Render IPs)

---

## 2. Backend Deployment (Render)

### Create Web Service

1. Go to [render.com](https://render.com) → New Web Service
2. Connect GitHub repo: `your-org/FairSalaryAI`
3. **Configuration:**
   - **Name**: `fairsalary-backend`
   - **Root Directory**: `FairSalaryAI/backend`
   - **Runtime**: Docker
   - **Dockerfile Path**: `./Dockerfile`
   - **Branch**: `main`

### Environment Variables

| Key | Value | Notes |
|-----|-------|-------|
| `DATABASE_URL` | `postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres?sslmode=require` | From Supabase |
| `SECRET_KEY` | `openssl rand -hex 32` | Generate securely |
| `JWT_ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | |
| `BCRYPT_ROUNDS` | `12` | |
| `FRONTEND_URL` | `https://your-app.vercel.app` | Vercel URL |
| `MODEL_PATH` | `/app/ml/models/best_model.joblib` | |
| `MODEL_METADATA_PATH` | `/app/ml/models/metadata.json` | |
| `MODEL_VERSION` | `1.0.0` | |
| `DEBUG` | `false` | Production |
| `LOG_LEVEL` | `INFO` | |
| `RATE_LIMIT_PER_MINUTE` | `60` | |
| `ENABLE_FAIRNESS_ANALYSIS` | `true` | |
| `ENABLE_SHAP_EXPLANATIONS` | `true` | |
| `ENABLE_SIMILAR_PROFILES` | `true` | |
| `ENABLE_SALARY_RANGE` | `true` | |

### Build & Deploy

1. Click **Create Web Service**
2. Render builds Docker image (~5-10 min)
3. Runs `alembic upgrade head` then `uvicorn`
4. Health check at `/health` must pass

### Custom Domain (Optional)

1. Settings → Custom Domains → Add
2. Add CNAME: `api.yourdomain.com` → `fairsalary-backend.onrender.com`
3. Render provisions SSL automatically

---

## 3. Frontend Deployment (Vercel)

### Import Project

1. Go to [vercel.com](https://vercel.com) → Add New Project
2. Import GitHub repo: `your-org/FairSalaryAI`
3. **Configuration:**
   - **Framework Preset**: Vite
   - **Root Directory**: `FairSalaryAI/frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

### Environment Variables

| Key | Value | Notes |
|-----|-------|-------|
| `VITE_API_URL` | `https://fairsalary-backend.onrender.com/api` | Backend URL |

### Deploy

1. Click **Deploy**
2. Vercel builds (`npm run build`) → ~2 min
3. Deploys to `https://your-app.vercel.app`
4. Automatic HTTPS + CDN

### Custom Domain (Optional)

1. Project Settings → Domains → Add
2. Add `app.yourdomain.com`
3. Vercel provisions SSL + DNS

### Environment-Specific Builds

**Production Build:**
```bash
# Local
cd FairSalaryAI/frontend
npm run build
# Output in dist/
```

---

## 4. Docker Deployment (Alternative)

### Local Development

```bash
# Start all services
cd FairSalaryAI
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop
docker-compose down
```

### Production Docker Build

```bash
# Build images
docker build -t fairsalary-backend:latest ./FairSalaryAI/backend
docker build -t fairsalary-frontend:latest ./FairSalaryAI/frontend

# Run
docker run -d -p 8000:8000 --env-file .env fairsalary-backend:latest
docker run -d -p 5173:80 fairsalary-frontend:latest
```

### Kubernetes (Future)

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fairsalary-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fairsalary-backend
  template:
    metadata:
      labels:
        app: fairsalary-backend
    spec:
      containers:
      - name: backend
        image: fairsalary-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: fairsalary-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: fairsalary-backend
spec:
  selector:
    app: fairsalary-backend
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

---

## 5. CI/CD Pipeline (GitHub Actions)

### Workflow File: `.github/workflows/ci-cd.yml`

**Triggers:**
- Push to `main`/`develop`
- Pull requests to `main`
- Release published

**Stages:**
1. **Backend Tests** - pytest + coverage
2. **Frontend Tests** - Vitest + lint + build
3. **ML Tests** - pytest ML tests
4. **Docker Build** - Multi-arch images
5. **Deploy Backend** → Render (main branch)
6. **Deploy Frontend** → Vercel (main branch)

### Required Secrets (GitHub Settings → Secrets)

| Secret | Description |
|--------|-------------|
| `RENDER_BACKEND_SERVICE_ID` | Render service ID |
| `RENDER_API_KEY` | Render API token |
| `VERCEL_TOKEN` | Vercel access token |
| `VERCEL_ORG_ID` | Vercel organization ID |
| `VERCEL_PROJECT_ID` | Vercel project ID |

---

## 5. Monitoring & Observability

### Health Checks

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Full system status |
| `GET /health/ready` | K8s readiness |
| `GET /health/live` | K8s liveness |

### Metrics (Prometheus)

| Metric | Type | Description |
|--------|--------|-------------|
| `http_requests_total` | Counter | Total requests |
| `http_request_duration_seconds` | Histogram | Latency |
| `predictions_total` | Counter | Predictions made |
| `prediction_latency_seconds` | Histogram | Prediction latency |

### Logging

**Structured JSON** (structlog):
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "event": "prediction_made",
  "user_id": 42,
  "prediction_id": 123,
  "latency_ms": 45
}
```

**Log Levels:**
- `DEBUG` - Development
- `INFO` - Production
- `WARNING` - Recoverable issues
- `ERROR` - Failed requests

### Error Tracking (Sentry)

```bash
# Backend
SENTRY_DSN=https://xxx@sentry.io/123

# Frontend
VITE_SENTRY_DSN=https://xxx@sentry.io/456
```

### Uptime Monitoring

**UptimeRobot / Pingdom / Better Uptime:**
- Monitor `/health` every 60s
- Alert on 2 consecutive failures
- Slack/email/PagerDuty notifications

---

## 6. Security Checklist

### Pre-Deployment

- [ ] All secrets in environment variables (not code)
- [ ] `DEBUG=false` in production
- [ ] `SECRET_KEY` generated with `openssl rand -hex 32`
- [ ] Database SSL mode `require`
- [ ] CORS restricted to frontend domain
- [ ] Rate limiting enabled
- [ ] Password hashing (bcrypt, 12 rounds)
- [ ] JWT tokens with expiry + refresh rotation
- [ ] CORS headers configured
- [ ] Security headers (HSTS, CSP, etc.)

### Database
- [ ] Row Level Security enabled
- [ ] Connection pooling (PgBouncer)
- [ ] Automated backups (daily + PITR)
- [ ] Read replica for analytics
- [ ] Encryption at rest + in transit

### API Security
- [ ] Rate limiting (60 req/min)
- [ ] Input validation (Pydantic)
- [ ] SQL injection protection (SQLAlchemy ORM)
- [ ] JWT with short expiry + refresh rotation
- [ ] CORS restricted to frontend domain
- [ ] No sensitive data in logs

---

## 6. Rollback Procedures

### Backend (Render)
1. Dashboard → Deploys → Select previous deploy
2. Click **Rollback**
3. Automatic redeploy (~2 min)

### Frontend (Vercel)
1. Vercel Dashboard → Deployments
2. Click **...** → **Rollback** on previous deployment
3. Instant rollback

### Database (Supabase)
```bash
# Point-in-time recovery
# Supabase Dashboard → Backups → Restore
# Select timestamp before issue
```

### Model Rollback
```bash
# Git revert model commit
git revert <commit-hash>
git push origin main
# CI/CD rebuilds and redeploys
```

---

## 7. Cost Optimization

### Estimated Monthly Costs (USD)

| Service | Tier | Est. Cost |
|---------|------|-----------|
| Supabase (PostgreSQL) | Pro | $25/mo |
| Render (Backend) | Starter | $7/mo |
| Vercel (Frontend) | Pro | $20/mo |
| **Total** | | **~$52/mo** |

### Cost Optimization Tips
- Use Supabase free tier for dev/staging
- Render free tier for staging
- Vercel hobby tier for personal projects
- Enable caching for static assets
- Use CDN for model artifacts (if large)

---

## 7. Troubleshooting

### Backend Won't Start
```bash
# Check logs
render logs fairsalary-backend

# Common issues:
# - DATABASE_URL incorrect
# - SECRET_KEY not set
# - Model file missing
# - Port binding (use PORT env var)
```

### Frontend Build Fails
```bash
# Clear cache
npm run clean
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Must be 18+
```

### Database Connection Issues
```bash
# Test connection
psql "postgresql://user:pass@host:5432/db?sslmode=require"

# Check:
# - SSL mode (require)
# - IP allowlist (Render IPs)
# - Connection pooler port (6543)
```

### CORS Errors
```bash
# Check:
# - FRONTEND_URL matches exactly (including protocol)
# - No trailing slash
# - Credentials: true in Axios
```

---

## 8. Maintenance

### Regular Tasks

| Frequency | Task |
|-----------|------|
| Daily | Check health endpoints |
| Weekly | Review error logs, metrics |
| Monthly | Update dependencies, security scan |
| Quarterly | Rotate secrets, review costs |
| On Release | Run full test suite, update changelog |

### Dependency Updates

```bash
# Backend
cd backend
pip list --outdated
pip install -U package_name
# Test, then update requirements.txt

# Frontend
cd frontend
npm outdated
npm update
# Test, then commit package-lock.json
```

### Database Maintenance

```sql
-- Vacuum analyze (weekly)
VACUUM ANALYZE;

-- Check index usage
SELECT * FROM pg_stat_user_indexes 
WHERE idx_scan = 0 AND schemaname = 'public';

-- Monitor table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 8. Support & Escalation

### Incident Response

| Severity | Response Time | Action |
|----------|---------------|--------|
| Critical (down) | 15 min | Page on-call, status page |
| High (degraded) | 1 hour | Investigate, mitigate |
| Medium (bug) | 4 hours | Triaged, scheduled fix |
| Low (enhancement) | Next sprint | Backlog |

### Contacts

| Role | Contact |
|------|---------|
| Backend Lead | backend-lead@company.com |
| Frontend Lead | frontend-lead@company.com |
| ML Engineer | ml-engineer@company.com |
| DevOps | devops@company.com |

### Status Page

- **Statuspage.io** or **Better Uptime**
- Components: API, Database, Frontend, ML Models
- Incident communication template

---

## Appendix: Useful Commands

```bash
# View backend logs
docker-compose logs -f backend

# Run backend tests
cd backend && pytest tests/ -v

# Run frontend tests
cd frontend && npm run test

# Database shell
docker-compose exec postgres psql -U fairsalary -d fairsalary

# Backup database
pg_dump -h localhost -U fairsalary fairsalary > backup.sql

# Restore database
psql -h localhost -U fairsalary -d fairsalary < backup.sql

# Check disk space
df -h

# Check memory
free -h

# Check ports
netstat -tulpn | grep -E '5432|8000|5173'
```