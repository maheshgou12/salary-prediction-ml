# FairSalary AI - API Documentation

## Base URL

| Environment | URL |
|-------------|-----|
| Local Development | `http://localhost:8000/api` |
| Production | `https://your-backend.onrender.com/api` |

## Authentication

All protected endpoints require a JWT Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Token Types

| Token | Expiry | Purpose |
|-------|--------|---------|
| Access Token | 30 minutes | API authentication |
| Refresh Token | 7 days | Obtain new access token |

---

## Authentication Endpoints

### Register User

Creates a new user account.

**Request**
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

**Response** (201 Created)
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": null
}
```

**Error Responses**
- `400` - Email already registered
- `422` - Validation error (password requirements)

---

### Login

Authenticates user and returns JWT tokens.

**Request**
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response** (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses**
- `401` - Invalid email or password
- `403` - Account deactivated

---

### Refresh Access Token

Obtain new access token using refresh token.

**Request**
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses**
- `401` - Invalid or expired refresh token

---

### Get Current User

Returns authenticated user profile.

**Request**
```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

**Response** (200 OK)
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-15T10:30:00Z"
}
```

---

### Logout

Invalidates tokens client-side (tokens must be deleted on client).

```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

**Response** (200 OK)
```json
{
  "message": "Successfully logged out"
}
```

---

## Prediction Endpoints

### Predict Salary

Generates salary prediction with range, explanation, and fairness analysis.

**Request**
```http
POST /api/predict
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "experience_years": 3.5,
  "education": "Bachelor's Degree",
  "job_role": "Software Engineer",
  "location": "Bangalore",
  "skills": ["Python", "SQL", "React", "AWS"],
  "industry": "Technology",
  "company_size": "Medium (201-1000)",
  "employment_type": "Full-time"
}
```

**Field Descriptions**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `experience_years` | number | Yes | Years of experience (0-50) |
| `education` | string | Yes | Education level |
| `job_role` | string | Yes | Job title |
| `location` | string | Yes | Work location |
| `skills` | array[string] | Yes | Technical skills |
| `industry` | string | Yes | Industry sector |
| `company_size` | string | Yes | Company size category |
| `employment_type` | string | No | Employment type (default: Full-time) |

**Valid Values**

| Field | Valid Options |
|-------|---------------|
| `education` | High School, Associate Degree, Bachelor's Degree, Master's Degree, PhD |
| `company_size` | Startup (1-50), Small (51-200), Medium (201-1000), Large (1000+) |
| `employment_type` | Full-time, Part-time, Contract, Internship, Freelance |

**Response** (200 OK)
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
    {
      "feature": "experience_years",
      "contribution": 180000,
      "direction": "positive"
    },
    {
      "feature": "skills",
      "contribution": 120000,
      "direction": "positive"
    },
    {
      "feature": "location",
      "contribution": -50000,
      "direction": "negative"
    }
  ],
  "model_version": "1.0.0",
  "fairness_disclaimer": "This prediction was made without using protected attributes...",
  "prediction_id": 42
}
```

**Error Responses**
- `401` - Unauthorized
- `422` - Validation error
- `500` - Prediction failed

---

### Get Prediction History

Returns paginated list of user's predictions.

**Request**
```http
GET /api/predict?page=1&page_size=20
Authorization: Bearer <access_token>
```

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `page_size` | integer | 20 | Items per page (max 100) |

**Response** (200 OK)
```json
[
  {
    "id": 42,
    "input_data": {
      "experience_years": 3.5,
      "education": "Bachelor's Degree",
      "job_role": "Software Engineer",
      "location": "Bangalore",
      "skills": ["Python", "SQL", "React", "AWS"],
      "industry": "Technology",
      "company_size": "Medium (201-1000)",
      "employment_type": "Full-time"
    },
    "predicted_salary": 1250000,
    "minimum_salary": 1150000,
    "maximum_salary": 1350000,
    "confidence": 0.87,
    "model_version": "1.0.0",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### Get Prediction Details

Returns full prediction with explanation and similar profiles.

```http
GET /api/predict/{id}
Authorization: Bearer <access_token>
```

**Response** (200 OK)
```json
{
  "id": 42,
  "input_data": {...},
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
  "explanation": [...],
  "model_version": "1.0.0",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## Fairness Endpoints

### Get Fairness Dashboard

Returns comprehensive fairness analysis across protected attributes.

```http
GET /api/fairness
Authorization: Bearer <access_token>
```

**Response** (200 OK)
```json
{
  "overall_status": "PASS",
  "model_version": "1.0.0",
  "protected_attributes": [
    {
      "attribute": "gender",
      "status": "PASS",
      "demographic_parity_difference": 0.029,
      "mean_prediction_difference": 128000,
      "mae_by_group": {"Male": 113000, "Female": 113000, "Non-binary": 119000},
      "rmse_by_group": {"Male": 148000, "Female": 148000, "Non-binary": 156000},
      "groups": [
        {
          "group": "Male",
          "count": 2806,
          "mean_predicted": 204900,
          "mean_actual": 204291,
          "mae": 115000,
          "rmse": 147800,
          "bias": 611
        }
      ],
      "recommendations": []
    }
  ],
  "recommendations": []
}
```

---

### Get Attribute Fairness

```http
GET /api/fairness/attribute/{attribute}
Authorization: Bearer <access_token>
```

**Path Parameters**
- `attribute` - `gender` or `age`

---

### Get Intersectional Fairness

```http
GET /api/fairness/intersectional
Authorization: Bearer <access_token>
```

---

### Get Proxy Feature Analysis

```http
GET /api/fairness/proxy
Authorization: Bearer <access_token>
```

---

## Model Endpoints

### Get Model Metrics

```http
GET /api/model/metrics
Authorization: Bearer <access_token>
```

**Response**
```json
{
  "version": "1.0.0",
  "model_type": "StackingEnsemble",
  "metrics": {
    "mae": 13809,
    "rmse": 18217,
    "r2": 0.916
  },
  "fairness_metrics": {...},
  "features": [...]
}
```

---

### Get Model Info

```http
GET /api/model/info
Authorization: Bearer <access_token>
```

---

## Health Endpoints

### Health Check

```http
GET /health
```

**Response**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "model_loaded": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Readiness Probe

```http
GET /health/ready
```

### Liveness Probe

```http
GET /health/live
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error description",
  "error_code": "ERROR_CODE"
}
```

### Common HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `UNAUTHORIZED` | Missing or invalid token |
| `FORBIDDEN` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `INTERNAL_ERROR` | Server error |
| `RATE_LIMITED` | Too many requests |

---

## Rate Limiting

| Endpoint | Limit |
|----------|-------|
| Auth endpoints | 10 req/min |
| Predictions | 60 req/min |
| Other | 60 req/min |

Rate limit headers:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

---

## Request/Response Examples

### cURL Examples

**Login**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123"}'
```

**Predict with Token**
```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "experience_years": 3,
    "education": "Bachelor'\''s Degree",
    "job_role": "Software Engineer",
    "location": "Bangalore",
    "skills": ["Python", "SQL"],
    "industry": "Technology",
    "company_size": "Medium (201-1000)",
    "employment_type": "Full-time"
  }'
```

**Get History**
```bash
curl -X GET "http://localhost:8000/api/predict?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## SDK Examples

### JavaScript/TypeScript

```typescript
const API_URL = 'https://api.fairsalary.ai/api';

async function login(email: string, password: string) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const { access_token, refresh_token } = await response.json();
  localStorage.setItem('access_token', access_token);
  localStorage.setItem('refresh_token', refresh_token);
}

async function predictSalary(data: any) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`${API_URL}/predict`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  return response.json();
}
```

### Python

```python
import requests

API_URL = "http://localhost:8000/api"

def login(email: str, password: str) -> dict:
    response = requests.post(f"{API_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    response.raise_for_status()
    return response.json()

def predict_salary(token: str, data: dict) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/predict", json=data, headers=headers)
    response.raise_for_status()
    return response.json()

# Usage
tokens = login("user@example.com", "SecurePass123")
result = predict_salary(tokens["access_token"], {
    "experience_years": 3,
    "education": "Bachelor's Degree",
    "job_role": "Software Engineer",
    "location": "Bangalore",
    "skills": ["Python", "SQL"],
    "industry": "Technology",
    "company_size": "Medium (201-1000)",
})
print(result)
```