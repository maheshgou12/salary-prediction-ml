"""Seed candidate_profiles from training data (idempotent)."""
import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "backend" / "fairsalary.db"
CSV = ROOT / "ml" / "data" / "salary_data.csv"

EDU_MAP = {
    "High School": "High School",
    "Bachelor": "Bachelor's Degree",
    "Master": "Master's Degree",
    "PhD": "PhD",
    "Associate": "Associate Degree",
}

con = sqlite3.connect(DB)
rows = list(csv.DictReader(open(CSV)))
data = []
for r in rows:
    skills = json.dumps([f"skill{i}" for i in range(int(float(r["skills_count"] or 0)))])
    data.append((
        float(r["years_experience"]),
        EDU_MAP.get(r["education_level"], r["education_level"]),
        r["job_role"], r["location"], skills, "Technology",
        r["company_size"], "Full-time", int(float(r["salary"])),
        r["gender"], int(float(r["age"])), "seed",
    ))
con.execute("DELETE FROM candidate_profiles")
con.executemany(
    "INSERT INTO candidate_profiles (experience_years, education, job_role, location, skills, industry, company_size, employment_type, salary, gender, age, source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
    data,
)
con.commit()
print("seeded:", con.execute("select count(*) from candidate_profiles").fetchone()[0])
