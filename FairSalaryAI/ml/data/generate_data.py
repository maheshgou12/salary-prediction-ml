"""Generate synthetic salary dataset for FairPay project."""
import numpy as np
import pandas as pd
from pathlib import Path


def generate_salary_data(n_samples: int = 2500, random_state: int = 42) -> pd.DataFrame:
    """Generate realistic synthetic salary data with protected attributes for fairness auditing.

    Args:
        n_samples: Number of samples to generate.
        random_state: Random seed for reproducibility.

    Returns:
        DataFrame with salary data and protected attributes.
    """
    np.random.seed(random_state)

    # Define categories
    education_levels = ['High School', 'Bachelor', 'Master', 'PhD']
    education_weights = [0.15, 0.45, 0.30, 0.10]

    job_roles = [
        'Software Engineer', 'Data Scientist', 'ML Engineer', 'DevOps Engineer',
        'Frontend Developer', 'Backend Developer', 'Full Stack Developer',
        'Data Analyst', 'Product Manager', 'Engineering Manager'
    ]
    role_weights = [0.20, 0.12, 0.10, 0.08, 0.10, 0.10, 0.10, 0.08, 0.07, 0.05]

    locations = ['San Francisco', 'New York', 'Seattle', 'Austin', 'Boston', 'Remote', 'Chicago', 'Los Angeles']
    location_weights = [0.20, 0.15, 0.12, 0.10, 0.08, 0.15, 0.10, 0.10]

    company_sizes = ['Startup (1-50)', 'Small (51-200)', 'Medium (201-1000)', 'Large (1000+)']
    company_weights = [0.25, 0.30, 0.25, 0.20]

    genders = ['Male', 'Female', 'Non-binary']
    gender_weights = [0.55, 0.42, 0.03]

    # Generate base features
    years_experience = np.random.exponential(scale=5, size=n_samples).clip(0, 30).round(1)
    education_level = np.random.choice(education_levels, n_samples, p=education_weights)
    job_role = np.random.choice(job_roles, n_samples, p=role_weights)
    location = np.random.choice(locations, n_samples, p=location_weights)
    company_size = np.random.choice(company_sizes, n_samples, p=company_weights)
    gender = np.random.choice(genders, n_samples, p=gender_weights)
    age = np.random.normal(32, 8, n_samples).clip(22, 65).round().astype(int)

    # Skills count correlated with experience and education
    edu_skill_boost = {'High School': 0, 'Bachelor': 1, 'Master': 2, 'PhD': 3}
    skills_base = np.random.poisson(3, n_samples)
    skills_edu = np.array([edu_skill_boost[e] for e in education_level])
    skills_exp = (years_experience / 3).astype(int)
    skills_count = (skills_base + skills_edu + skills_exp + np.random.poisson(1, n_samples)).clip(1, 20)

    # Interview score (1-10) with some correlation to experience and education
    interview_base = np.random.normal(6.5, 1.5, n_samples).clip(1, 10)
    interview_exp_boost = np.minimum(years_experience / 10, 1.5)
    interview_edu_boost = np.array([edu_skill_boost[e] * 0.3 for e in education_level])
    interview_score = (interview_base + interview_exp_boost + interview_edu_boost + np.random.normal(0, 0.5, n_samples)).clip(1, 10).round(1)

    # Previous salary based on experience, role, location, with some noise
    role_base_salary = {
        'Software Engineer': 120000, 'Data Scientist': 130000, 'ML Engineer': 140000,
        'DevOps Engineer': 125000, 'Frontend Developer': 110000, 'Backend Developer': 115000,
        'Full Stack Developer': 120000, 'Data Analyst': 90000, 'Product Manager': 135000,
        'Engineering Manager': 160000
    }
    location_multiplier = {
        'San Francisco': 1.4, 'New York': 1.35, 'Seattle': 1.25, 'Austin': 1.1,
        'Boston': 1.2, 'Remote': 1.0, 'Chicago': 1.05, 'Los Angeles': 1.15
    }
    company_multiplier = {
        'Startup (1-50)': 0.9, 'Small (51-200)': 1.0, 'Medium (201-1000)': 1.1, 'Large (1000+)': 1.2
    }
    edu_multiplier = {'High School': 0.85, 'Bachelor': 1.0, 'Master': 1.15, 'PhD': 1.3}

    prev_salary = np.zeros(n_samples)
    for i in range(n_samples):
        base = role_base_salary[job_role[i]]
        exp_factor = 1 + min(years_experience[i] * 0.03, 0.6)
        prev_salary[i] = base * exp_factor * location_multiplier[location[i]] * company_multiplier[company_size[i]] * edu_multiplier[education_level[i]]
        prev_salary[i] *= np.random.lognormal(0, 0.1)  # Add noise

    prev_salary = prev_salary.round(-3).astype(int)  # Round to nearest 1000

    # Target salary: similar logic but with interview score influence and less noise
    target_salary = np.zeros(n_samples)
    for i in range(n_samples):
        base = role_base_salary[job_role[i]]
        exp_factor = 1 + min(years_experience[i] * 0.035, 0.7)
        interview_factor = 1 + (interview_score[i] - 5.5) * 0.04
        target_salary[i] = base * exp_factor * interview_factor * location_multiplier[location[i]] * company_multiplier[company_size[i]] * edu_multiplier[education_level[i]]
        target_salary[i] *= np.random.lognormal(0, 0.08)

    target_salary = target_salary.round(-3).astype(int)

    # Create DataFrame
    df = pd.DataFrame({
        'years_experience': years_experience,
        'education_level': education_level,
        'skills_count': skills_count,
        'job_role': job_role,
        'previous_salary': prev_salary,
        'interview_score': interview_score,
        'location': location,
        'company_size': company_size,
        'gender': gender,  # Protected attribute - ONLY for fairness auditing
        'age': age,        # Protected attribute - ONLY for fairness auditing
        'salary': target_salary  # Target variable
    })

    # Introduce some realistic missing values (1-3% per column)
    missing_cols = ['previous_salary', 'interview_score', 'skills_count']
    for col in missing_cols:
        mask = np.random.random(n_samples) < 0.02
        df.loc[mask, col] = np.nan

    return df


if __name__ == '__main__':
    output_path = Path(__file__).parent / 'salary_data.csv'
    df = generate_salary_data(5000)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} samples")
    print(f"Saved to {output_path}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nMissing values:\n{df.isnull().sum()}")
    print(f"\nSalary stats:\n{df['salary'].describe()}")
    print(f"\nGender distribution:\n{df['gender'].value_counts()}")
    print(f"\nAge stats:\n{df['age'].describe()}")