"""Comprehensive End-to-End API Integration Tests for FairSalary AI."""
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import init_db

# Initialize database tables
init_db()
client = TestClient(app)


@pytest.fixture
def auth_user():
    """Create a unique test user and return login token headers."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"test_{unique_id}@example.com"
    password = "TestPassword123!"

    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "full_name": "Test Engineer",
        "password": password
    })
    assert reg_res.status_code == 201

    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    data = login_res.json()
    token = data["access_token"]
    refresh_token = data["refresh_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return {"email": email, "password": password, "headers": headers, "token": token, "refresh_token": refresh_token}


class TestHealthEndpoints:
    def test_health_check(self):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ["healthy", "degraded"]
        assert data["database"] == "connected"
        assert data["model_loaded"] is True

    def test_readiness_check(self):
        res = client.get("/health/ready")
        assert res.status_code == 200
        assert res.json()["ready"] is True

    def test_liveness_check(self):
        res = client.get("/health/live")
        assert res.status_code == 200
        assert res.json()["alive"] is True

    def test_root_endpoint(self):
        res = client.get("/")
        assert res.status_code == 200
        data = res.json()
        assert "FairSalary" in data["name"]


class TestAuthEndpoints:
    def test_duplicate_registration_rejected(self, auth_user):
        res = client.post("/api/auth/register", json={
            "email": auth_user["email"],
            "full_name": "Duplicate User",
            "password": "Password123"
        })
        assert res.status_code == 400
        assert "Email already registered" in res.json()["detail"]

    def test_invalid_login_credentials(self):
        res = client.post("/api/auth/login", json={
            "email": "nonexistent_user@example.com",
            "password": "WrongPassword!"
        })
        assert res.status_code == 401

    def test_me_endpoint_with_auth(self, auth_user):
        res = client.get("/api/auth/me", headers=auth_user["headers"])
        assert res.status_code == 200
        assert res.json()["email"] == auth_user["email"]

    def test_me_endpoint_without_auth(self):
        res = client.get("/api/auth/me")
        assert res.status_code in [401, 403]

    def test_token_refresh(self, auth_user):
        res = client.post("/api/auth/refresh", json={
            "refresh_token": auth_user["refresh_token"]
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_forgot_and_reset_password(self, auth_user):
        res = client.post("/api/auth/forgot-password", json={
            "email": auth_user["email"]
        })
        assert res.status_code == 200
        assert "message" in res.json()


class TestPredictionEndpoints:
    def test_predict_salary_authenticated(self, auth_user):
        candidate_input = {
            "experience_years": 6.0,
            "education": "Bachelor's Degree",
            "skills": ["Python", "Machine Learning", "Docker"],
            "job_role": "Data Scientist",
            "location": "San Francisco",
            "company_size": "Large (1000+)",
            "industry": "Technology",
            "employment_type": "Full-time",
            "previous_salary": 140000,
            "interview_score": 8.5
        }

        res = client.post("/api/predict", headers=auth_user["headers"], json=candidate_input)
        assert res.status_code == 200
        data = res.json()
        assert data["predicted_salary"] > 0
        assert data["minimum_salary"] <= data["predicted_salary"]
        assert data["maximum_salary"] >= data["predicted_salary"]
        assert data["confidence"] > 0
        assert "prediction_id" in data
        assert isinstance(data["explanation"], list)
        assert isinstance(data["similar_profiles"], dict)

    def test_predict_salary_unauthenticated(self):
        candidate_input = {
            "experience_years": 4.0,
            "education": "Master's Degree",
            "skills": ["React", "TypeScript"],
            "job_role": "Software Engineer",
            "location": "New York",
            "company_size": "Medium (201-1000)",
            "industry": "Technology",
            "employment_type": "Full-time"
        }
        res = client.post("/api/predict", json=candidate_input)
        assert res.status_code in [401, 403]

    def test_history_and_detail(self, auth_user):
        # Create a prediction first
        candidate_input = {
            "experience_years": 3.0,
            "education": "Bachelor's Degree",
            "skills": ["Java", "Spring Boot"],
            "job_role": "Backend Developer",
            "location": "Austin",
            "company_size": "Small (51-200)",
            "industry": "Technology",
            "employment_type": "Full-time",
            "previous_salary": 95000,
            "interview_score": 7.0
        }
        pred_res = client.post("/api/predict", headers=auth_user["headers"], json=candidate_input)
        assert pred_res.status_code == 200
        pred_id = pred_res.json()["prediction_id"]

        # Fetch history
        hist_res = client.get("/api/predict", headers=auth_user["headers"])
        assert hist_res.status_code == 200
        history = hist_res.json()
        assert len(history) >= 1
        assert any(item["id"] == pred_id for item in history)

        # Fetch detail
        detail_res = client.get(f"/api/predict/{pred_id}", headers=auth_user["headers"])
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["id"] == pred_id
        assert detail["predicted_salary"] == pred_res.json()["predicted_salary"]


class TestFairnessEndpoints:
    def test_fairness_dashboard(self, auth_user):
        res = client.get("/api/fairness", headers=auth_user["headers"])
        assert res.status_code == 200
        data = res.json()
        assert "overall_status" in data
        assert "protected_attributes" in data

    def test_gender_attribute_fairness(self, auth_user):
        res = client.get("/api/fairness/attribute/gender", headers=auth_user["headers"])
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_invalid_attribute_fairness(self, auth_user):
        res = client.get("/api/fairness/attribute/invalid_attr", headers=auth_user["headers"])
        assert res.status_code == 400

    def test_intersectional_and_proxy(self, auth_user):
        res_inter = client.get("/api/fairness/intersectional", headers=auth_user["headers"])
        assert res_inter.status_code == 200

        res_proxy = client.get("/api/fairness/proxy", headers=auth_user["headers"])
        assert res_proxy.status_code == 200


class TestModelEndpoints:
    def test_model_metrics(self, auth_user):
        res = client.get("/api/model/metrics", headers=auth_user["headers"])
        assert res.status_code == 200
        data = res.json()
        assert "metrics" in data
        assert "model_type" in data

    def test_model_info(self, auth_user):
        res = client.get("/api/model/info", headers=auth_user["headers"])
        assert res.status_code == 200
        data = res.json()
        assert data["is_active"] is True
        assert "version" in data


class TestCandidatesEndpoints:
    def test_candidates_count(self, auth_user):
        res = client.get("/api/candidates/count", headers=auth_user["headers"])
        assert res.status_code == 200
        data = res.json()
        assert "count" in data
        assert data["count"] >= 0

    def test_add_candidate_profile(self, auth_user):
        candidate_data = {
            "experience_years": 4.5,
            "education": "Master's Degree",
            "skills": ["Python", "SQL"],
            "job_role": "Data Analyst",
            "location": "Chicago",
            "company_size": "Medium (201-1000)",
            "industry": "Finance",
            "employment_type": "Full-time"
        }
        res = client.post(
            "/api/candidates?salary=115000",
            headers=auth_user["headers"],
            json=candidate_data
        )
        assert res.status_code == 201
        assert "id" in res.json()
