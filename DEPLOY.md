# Deployment Guide: FairPay

This guide provides step-by-step instructions for deploying FairPay to various platforms.

## Table of Contents
1. [Streamlit Community Cloud](#streamlit-community-cloud-recommended)
2. [Hugging Face Spaces](#hugging-face-spaces)
3. [Docker (Any Cloud)](#docker-any-cloud-provider)
4. [Local/On-Premise](#localon-premise)
5. [Environment Variables](#environment-variables)
6. [Troubleshooting](#troubleshooting)

---

## Streamlit Community Cloud (Recommended)

**Free, zero-config, auto-scaling hosting for Streamlit apps.**

### Prerequisites
- GitHub account
- Repository pushed to GitHub

### Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: FairPay salary prediction tool"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/fairpay.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository: `YOUR_USERNAME/fairpay`
   - Branch: `main`
   - Main file path: `app/streamlit_app.py`
   - Click "Deploy!"

3. **Wait for build** (2-3 minutes)
   - Streamlit installs dependencies from `requirements.txt`
   - Runs the app automatically

4. **Access your app**
   - URL: `https://fairpay-<random>.streamlit.app`
   - Share this link with your team

### Automatic Updates
- Any push to `main` branch triggers automatic rebuild
- Check "Manage app" → "Settings" → "Reboot app" if needed

---

## Hugging Face Spaces

**Free hosting optimized for ML demos, with GPU options.**

### Option A: Streamlit Template (Easiest)

1. **Create Space**
   - Go to [huggingface.co/new-space](https://huggingface.co/new-space)
   - Owner: your account or organization
   - Space name: `fairpay`
   - License: MIT
   - SDK: **Streamlit**
   - Hardware: CPU basic (free)
   - Click "Create Space"

2. **Add Files**
   - Clone the Space locally:
     ```bash
     git clone https://huggingface.co/spaces/YOUR_USERNAME/fairpay
     cd fairpay
     ```
   - Copy all project files:
     ```bash
     cp -r /path/to/fairpay/* .
     ```
   - Commit and push:
     ```bash
     git add .
     git commit -m "Add FairPay app"
     git push
     ```

3. **Auto-build**
   - HF Spaces detects `requirements.txt` and `app/streamlit_app.py`
   - Builds automatically
   - Access at: `https://huggingface.co/spaces/YOUR_USERNAME/fairpay`

### Option B: Docker Template (More Control)

1. **Create Space** with SDK: **Docker**
2. **Add Dockerfile** (already in repo)
3. **Push and build** — HF builds the Docker image

---

## Docker (Any Cloud Provider)

**For AWS ECS, Google Cloud Run, Azure Container Apps, DigitalOcean, etc.**

### Build Image

```bash
# Build
docker build -t fairpay:latest .

# Test locally
docker run -p 8501:8501 fairpay:latest
# Open http://localhost:8501
```

### Push to Registry

```bash
# Tag for your registry
docker tag fairpay:latest ghcr.io/YOUR_USERNAME/fairpay:latest
docker tag fairpay:latest YOUR_USERNAME/fairpay:latest

# Push
docker push ghcr.io/YOUR_USERNAME/fairpay:latest
# or
docker push YOUR_USERNAME/fairpay:latest
```

### Deploy to Cloud Run (Google Cloud)

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Deploy
gcloud run deploy fairpay \
  --image ghcr.io/YOUR_USERNAME/fairpay:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8501 \
  --memory 1Gi \
  --cpu 1
```

### Deploy to AWS ECS (Fargate)

1. Create ECR repository: `aws ecr create-repository --repository-name fairpay`
2. Push image to ECR
3. Create ECS task definition with:
   - Container port: 8501
   - Memory: 1024 MiB
   - CPU: 512 units
4. Create ECS service with ALB

### Deploy to Azure Container Apps

```bash
az containerapp up \
  --name fairpay \
  --resource-group myResourceGroup \
  --image ghcr.io/YOUR_USERNAME/fairpay:latest \
  --target-port 8501 \
  --ingress external
```

### Deploy to DigitalOcean App Platform

1. Create `app.yaml` in repo root:
   ```yaml
   name: fairpay
   services:
   - name: web
     source_dir: /
     github:
       repo: YOUR_USERNAME/fairpay
       branch: main
     run_command: streamlit run app/streamlit_app.py --server.port=8080 --server.address=0.0.0.0
     environment_slug: python
     instance_count: 1
     instance_size_slug: basic-xxs
     http_port: 8080
   ```
2. Connect GitHub repo in DigitalOcean dashboard
3. Deploy automatically

---

## Local/On-Premise

### Quick Start (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Generate data (if not present)
python data/generate_data.py

# Train model
python src/train.py

# Run app
streamlit run app/streamlit_app.py
```

### Production with Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  fairpay:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./models:/app/models
      - ./data:/app/data
    environment:
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_SERVER_PORT=8501
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Add nginx reverse proxy for SSL
  # nginx:
  #   image: nginx:alpine
  #   ports:
  #     - "80:80"
  #     - "443:443"
  #   volumes:
  #     - ./nginx.conf:/etc/nginx/nginx.conf
  #   depends_on:
  #     - fairpay
```

Run: `docker-compose up -d`

### Systemd Service (Linux)

Create `/etc/systemd/system/fairpay.service`:

```ini
[Unit]
Description=FairPay Salary Prediction App
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/fairpay
Environment=PATH=/opt/fairpay/venv/bin
ExecStart=/opt/fairpay/venv/bin/streamlit run app/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable fairpay
sudo systemctl start fairpay
sudo systemctl status fairpay
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAMLIT_SERVER_PORT` | 8501 | Port to run on |
| `STREAMLIT_SERVER_ADDRESS` | 0.0.0.0 | Bind address |
| `STREAMLIT_SERVER_HEADLESS` | true | Run headless |
| `STREAMLIT_BROWSER_GATHER_USAGE_STATS` | false | Disable telemetry |
| `MODEL_PATH` | models/best_model.joblib | Model file path |
| `DATA_PATH` | data/salary_data.csv | Data file path |

### Setting in Streamlit Cloud
- Go to App Settings → Secrets
- Add as TOML:
  ```toml
  MODEL_PATH = "models/best_model.joblib"
  ```

### Setting in Hugging Face Spaces
- Space Settings → Repository secrets
- Add `MODEL_PATH` etc.

### Setting in Docker
```dockerfile
ENV MODEL_PATH=/app/models/best_model.joblib
```
Or at runtime:
```bash
docker run -e MODEL_PATH=/app/models/best_model.joblib fairpay:latest
```

---

## Troubleshooting

### Common Issues

#### 1. Model file not found
```
FileNotFoundError: [Errno 2] No such file or directory: 'models/best_model.joblib'
```
**Solution**: Ensure model is trained and committed, or train on startup:
```python
# In streamlit_app.py, add at top:
if not Path('models/best_model.joblib').exists():
    import subprocess
    subprocess.run(['python', 'src/train.py'], check=True)
```

#### 2. Data file not found
**Solution**: Include `data/generate_data.py` and run on first deploy, or commit generated data (if small).

#### 3. Port binding errors
```
OSError: [Errno 98] Address already in use
```
**Solution**: Ensure only one process uses port 8501. In Docker, use `--network host` or different port.

#### 4. Memory issues on free tiers
**Solution**: 
- Reduce SHAP sample size in `src/explain.py`
- Use `--server.maxUploadSize` for batch uploads
- Consider model quantization

#### 5. Slow first prediction
**Solution**: SHAP explainer initializes on first use. Pre-warm in `@st.cache_resource`.

#### 6. Package version conflicts
**Solution**: Pin exact versions in `requirements.txt`:
```
streamlit==1.28.0
shap==0.42.1
scikit-learn==1.3.2
```

### Health Checks

All deployments should verify:
```bash
# Health endpoint
curl http://your-app-url/_stcore/health
# Should return "ok"

# App loads
curl http://your-app-url/
# Should return HTML with "FairPay"
```

### Logs

- **Streamlit Cloud**: Click "Manage app" → "Logs"
- **HF Spaces**: "Logs" tab in Space
- **Docker**: `docker logs fairpay`
- **Cloud Run**: `gcloud run services logs read fairpay`

---

## Security Checklist

- [ ] Run as non-root user (Dockerfile includes this)
- [ ] No secrets in code (use environment variables)
- [ ] HTTPS enforced (handled by platforms)
- [ ] Input validation on batch upload
- [ ] Rate limiting (add via nginx/proxy if needed)
- [ ] Regular dependency updates (`pip-audit`)

---

## Monitoring

For production deployments, consider adding:

1. **Application Monitoring**: Streamlit doesn't have built-in APM, but you can add:
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   logger.info(f"Prediction request: {input_data}")
   ```

2. **Uptime Monitoring**: Use UptimeRobot, Pingdom, or cloud provider health checks

3. **Error Tracking**: Sentry integration:
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn="YOUR_DSN")
   ```

---

## Rollback Strategy

- **Streamlit Cloud**: Re-deploy previous commit from "Manage app" → "Deploy history"
- **HF Spaces**: `git revert` and push
- **Docker**: `docker tag fairpay:previous fairpay:latest && docker push`
- **Kubernetes**: `kubectl rollout undo deployment/fairpay`

---

## Support

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/fairpay/issues)
- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)
- **HF Spaces Docs**: [huggingface.co/docs/hub/spaces](https://huggingface.co/docs/hub/spaces)
- **Docker Docs**: [docs.docker.com](https://docs.docker.com)