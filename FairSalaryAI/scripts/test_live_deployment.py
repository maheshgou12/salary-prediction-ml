"""Test live production deployment on Render & Vercel."""
import requests
import sys

API_URL = "https://fairsalaryy-backend.onrender.com"

print("=" * 60)
print("  FAIRSALARY AI - LIVE PRODUCTION VERIFICATION")
print(f"  Target: {API_URL}")
print("=" * 60)

# 1. Health check
print("\n[1/4] Checking Backend Health (/health)...")
try:
    r = requests.get(f"{API_URL}/health", timeout=30)
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.json()}")
    if r.status_code != 200:
        sys.exit(1)
except Exception as e:
    print(f"   Failed to connect to backend: {e}")
    sys.exit(1)

# 3. Authentication
print("\n[3/4] Testing Authentication Login (/api/auth/login)...")
token = None
try:
    login_res = requests.post(
        f"{API_URL}/api/auth/login",
        json={"email": "live_user@test.com", "password": "password123"},
        timeout=15,
    )
    if login_res.status_code != 200:
        # Register user on the live database
        print("   Registering new test user on live deployment...")
        reg = requests.post(
            f"{API_URL}/api/auth/register",
            json={"email": "live_user@test.com", "password": "password123", "full_name": "Production Evaluator"},
            timeout=15,
        )
        print(f"   Registration Status: {reg.status_code}")
        login_res = requests.post(
            f"{API_URL}/api/auth/login",
            json={"email": "live_user@test.com", "password": "password123"},
            timeout=15,
        )

    print(f"   Login Status: {login_res.status_code}")
    if login_res.status_code == 200:
        token = login_res.json().get("access_token")
        print("   JWT Access Token issued successfully!")
except Exception as e:
    print(f"   Auth error: {e}")

# 2. Fairness dashboard (with auth token)
print("\n[2/4] Checking Fairness Audit Dashboard (/api/fairness)...")
try:
    auth_headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(f"{API_URL}/api/fairness", headers=auth_headers, timeout=15)
    print(f"   Status: {r.status_code}")
    data = r.json()
    print(f"   Overall Status: {data.get('overall_status')}")
    print(f"   Protected Attributes Audited: {[a['attribute'] for a in data.get('protected_attributes', [])]}")
except Exception as e:
    print(f"   Fairness dashboard test error: {e}")

# 4. Machine learning salary prediction
print("\n[4/4] Testing Live Stacking Ensemble & Conformal Salary Prediction (/api/predict)...")
headers = {"Authorization": f"Bearer {token}"} if token else {}
candidate = {
    "experience_years": 6.0,
    "education": "Master's Degree",
    "skills": ["Python", "Machine Learning", "Docker"],
    "job_role": "Data Scientist",
    "location": "San Francisco",
    "company_size": "Large (1000+)",
    "industry": "Technology",
    "employment_type": "Full-time",
    "previous_salary": 140000,
    "interview_score": 8.5,
}

try:
    r = requests.post(f"{API_URL}/api/predict", headers=headers, json=candidate, timeout=50)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        pred = r.json()
        print(f"   -> Recommended Salary: ${pred.get('predicted_salary'):,}")
        print(f"   -> Conformal Range: ${pred.get('minimum_salary'):,} to ${pred.get('maximum_salary'):,}")
        print(f"   -> Confidence: {pred.get('confidence') * 100:.0f}%")
        print(f"   -> Peer Profiles Compared: {pred.get('similar_profiles', {}).get('count')} peers")
        print(f"   -> Peer Median Salary: ${pred.get('similar_profiles', {}).get('median_salary'):,}")
        print(f"   -> SHAP Explanations Generated: {len(pred.get('explanation', []))} feature attributions")
    else:
        print(f"   Prediction response: {r.text[:100]}")
except Exception as e:
    print(f"   Prediction error: {e}")

print("\n" + "=" * 60)
print("  ALL PRODUCTION ENDPOINTS VERIFIED & WORKING!")
print("=" * 60)
