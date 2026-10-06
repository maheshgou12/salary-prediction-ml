# FairSalary AI - ML Methodology Documentation

## Overview

This document describes the machine learning methodology used in FairSalary AI for salary prediction, fairness analysis, and explainability.

## Problem Formulation

### Objective
Predict fair salary recommendations for job candidates based on their profile while ensuring fairness across protected groups.

### Task Type
**Regression** - Predict continuous salary values in INR.

### Features
| Feature | Type | Description |
|---------|------|-------------|
| experience_years | Numerical | Years of professional experience |
| education | Categorical | High School, Associate, Bachelor's, Master's, PhD |
| job_role | Categorical | 14+ job roles |
| location | Categorical | 10+ locations |
| skills | Categorical (multi-label) | Technical skills list |
| industry | Categorical | Industry sector |
| company_size | Categorical | Startup, Small, Medium, Large |
| employment_type | Categorical | Full-time, Part-time, Contract, etc. |

### Target
- **salary** - Annual compensation in INR

### Protected Attributes (NOT used for prediction)
- gender - Male, Female, Non-binary
- age - Numerical (binned for analysis)

---

## Data Pipeline

### 1. Synthetic Data Generation

**Method**: Statistical simulation with realistic relationships

**Key Relationships Modeled:**
- Experience → Salary (logarithmic growth, plateaus at ~15 years)
- Education → Salary (step function: HS < Bachelor < Master < PhD)
- Job Role → Salary (role-specific base salaries)
- Location → Salary (metro premium: Bangalore, Mumbai, Delhi NCR)
- Company Size → Salary (size multiplier)
- Skills → Salary (specialized skills premium)
- Experience × Education interaction
- Realistic noise (log-normal, ~15% CV)

**Data Quality:**
- 5,000+ samples
- ~2% missing values in salary-related features
- Class imbalance: Non-binary (2.7%), Age 50+ (0.9%)
- No data leakage (protected attributes separated)

### 2. Preprocessing Pipeline

**ColumnTransformer with:**
```
Numerical Features (StandardScaler + MedianImputer):
  - experience_years
  - skills_count (derived from skills list)

Categorical Features (OneHotEncoder + MostFrequentImputer):
  - education
  - job_role
  - location
  - industry
  - company_size
  - employment_type

Protected Attributes (EXCLUDED from features):
  - gender
  - age
```

**Pipeline Benefits:**
- No data leakage (fit on train only)
- Handles unknown categories (handle_unknown='ignore')
- Consistent inference preprocessing
- Saved with model for reproducibility

### 3. Feature Engineering

**Derived Features:**
- `skills_count` - Count of technical skills
- `skills_vector` - Multi-hot encoding (for similarity search)

**No Feature Selection** - All domain-relevant features retained for interpretability.

---

## Model Training

### Algorithms Evaluated

| Algorithm | Hyperparameter Tuning | CV Strategy |
|-----------|----------------------|-------------|
| Linear Regression | None | 5-fold CV |
| Ridge Regression | α ∈ [0.01, 100] (log-uniform) | 5-fold CV |
| Random Forest | n_estimators, max_depth, min_samples_split | 5-fold CV |
| Gradient Boosting | n_estimators, learning_rate, max_depth | 5-fold CV |
| XGBoost | n_estimators, learning_rate, max_depth, subsample | 5-fold CV |

### Hyperparameter Optimization

**Method**: Optuna (TPE sampler)
- **Trials**: 50 per algorithm
- **Objective**: Minimize CV MAE
- **Pruning**: Median pruner
- **Parallel**: n_jobs=-1

### Cross-Validation

- **Strategy**: 5-fold stratified (by salary bins)
- **Metrics**: MAE, RMSE, R²
- **Stratification**: Salary quintiles to ensure representation

### Train/Test Split

- **Train**: 60% (3,000 samples)
- **Calibration**: 20% (1,000 samples) - for conformal prediction
- **Test**: 20% (1,000 samples) - held out

**Stratification**: By salary quintile + protected attributes

---

## Model Selection

### Evaluation Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| MAE | mean(\|y - ŷ\|) | Average absolute error |
| RMSE | sqrt(mean((y - ŷ)²)) | Penalizes large errors |
| R² | 1 - SS_res/SS_tot | Variance explained |

### Model Comparison Results (Typical)

| Model | CV MAE | Test MAE | Test RMSE | Test R² | Training Time |
|-------|--------|----------|-----------|---------|---------------|
| Linear Regression | $15,014 | $14,683 | $19,219 | 0.906 | 3s |
| Ridge Regression | $15,014 | $14,685 | $19,221 | 0.906 | 6s |
| Random Forest | $19,769 | $19,560 | $25,149 | 0.840 | 31s |
| Gradient Boosting | $17,136 | $15,389 | $20,111 | 0.898 | 9s |
| XGBoost | $16,445 | $15,324 | $20,235 | 0.896 | 25s |
| **Stacking Ensemble** | - | **$13,809** | **$18,218** | **0.916** | 7s |
| Voting Ensemble | - | $14,151 | $18,542 | 0.913 | 3s |

### Selection Criteria

1. **Primary**: Test MAE (primary business metric)
2. **Secondary**: Test R² (explanatory power)
3. **Tertiary**: Fairness metrics (demographic parity)
4. **Stability**: Low CV std across folds
4. **Interpretability**: SHAP compatibility

**Selected**: Stacking Ensemble (Linear + Ridge + XGBoost with Ridge meta-learner)

---

## Ensemble Architecture

### Stacking Ensemble

**Base Learners:**
1. Linear Regression
2. Ridge Regression (α=0.165)
3. XGBoost (n_estimators=171, max_depth=4, lr=0.147)

**Meta-Learner:** Ridge Regression (α=1.0)

**Cross-Validation:** 5-fold for meta-learner training

**Advantages:**
- Combines linear and non-linear patterns
- Better generalization than individual models
- Lower variance than single models
- Maintains interpretability via SHAP

---

## Fairness Analysis

### Methodology

**Framework**: Fairlearn 0.9+

**Protected Attributes:**
- Gender: Male, Female, Non-binary
- Age Group: 20-30, 30-40, 40-50, 50+

### Metrics

| Metric | Formula | Threshold |
|--------|---------|-----------|
| Demographic Parity Difference | max(ŷ) - min(ŷ) across groups | < 0.05 |
| Mean Prediction Difference | max(E[ŷ]) - min(E[ŷ]) | < ₹20,000 |
| MAE by Group | mean(\|y - ŷ\|) per group | Similar across groups |
| RMSE by Group | sqrt(mean((y - ŷ)²)) per group | Similar across groups |

### Binarization for Equalized Odds

For regression, we binarize at median salary:
- y_bin = 1 if salary ≥ median else 0
- Apply classification fairness metrics

### Mitigation

**Post-Processing Calibration** (Mean Matching):
```
For each group g:
  shift_g = overall_mean - group_mean
  ŷ_calibrated = ŷ + shift_g
```

**Results:**
- Gender DP Diff: 7.7% → 2.9% (after calibration)
- Age DP Diff: 5.8% → 2.7% (after calibration)

### Proxy Feature Analysis

**Method**: Correlation + ANOVA
- Numerical: Pearson correlation with age
- Categorical: ANOVA F-test with gender
- Threshold: |r| > 0.3 or p < 0.05

**Result**: No strong proxies detected

---

## Explainability (SHAP)

### Method

**SHAP (SHapley Additive exPlanations)**

**Explainer Selection:**
- Linear models → LinearExplainer
- Tree models → TreeExplainer
- Ensembles → KernelExplainer (with background sample)

### Global Explanations

**Mean |SHAP|** across test set:
1. experience_years
2. previous_salary
3. skills_count
4. job_role (Engineering Manager, ML Engineer)
5. location (Bangalore, Mumbai)
6. education (PhD, Master's)
7. company_size (Large)
8. industry (Technology, Finance)

### Local Explanations

**Waterfall Plots** for individual predictions:
- Base value (expected salary)
- Feature contributions (positive/negative)
- Feature values
- Sum = prediction

**Background Sample**: 50 samples for KernelExplainer speed

### Interpretation Guidelines

✅ **Do:**
- Show top contributing features
- Indicate direction (push up/down)
- Explain base value concept
- Note model-specific nature

❌ **Don't:**
- Claim causal relationships
- Ignore feature interactions
- Apply to out-of-distribution samples

---

## Salary Range Estimation

### Conformal Prediction

**Method**: Split Conformal Prediction

**Procedure:**
1. Split train → calibration (20%) + test (20%)
2. Train on 60%
3. Compute residuals on calibration: rᵢ = |yᵢ - ŷᵢ|
4. Compute quantile: q̂ = (1-α)(1+1/n) quantile of residuals
5. Prediction interval: [ŷ - q̂, ŷ + q̂]

**Parameters:**
- α = 0.1 (90% nominal coverage)
- Calibration size: 1,000 samples

**Results:**
- Nominal: 90%
- Actual coverage: ~81.7% (conservative)
- q̂: ₹22,333
- Avg interval width: ₹44,667

### Alternative: RMSE-based

**Fallback** when conformal not available:
- margin = 1.96 × RMSE
- interval = [ŷ - margin, ŷ + margin]
- coverage ≈ 95% (assuming normality)

---

## Similar Profiles Analysis

### Method: k-Nearest Neighbors

**Distance Metric**: Weighted Euclidean on preprocessed features

**Weights:**
- experience_years: 2.0
- education: 1.5
- job_role: 2.0
- location: 1.5
- skills: 1.5
- industry: 1.0
- company_size: 1.0
- employment_type: 0.5

**Procedure:**
1. Filter by job_role (exact match)
2. Filter by location (exact match)
3. Filter experience ± 2 years
3. Compute weighted distance
4. Take top N=50 neighbors
5. Compute statistics

**Statistics Reported:**
- Count of similar profiles
- Median salary
- 25th percentile
- 75th percentile

---

## Model Artifacts

### Saved Files

| File | Description | Format |
|------|-------------|--------|
| `best_model.joblib` | Full pipeline (preprocessor + ensemble) | joblib |
| `metadata.json` | Version, metrics, features | JSON |
| `fairness_audit.json` | Fairlearn results | JSON |
| `conformal_summary.json` | q̂, coverage stats | JSON |
| `shap_analysis.json` | Global SHAP values | JSON |
| `drift_report.json` | PSI/KS drift metrics | JSON |

### Versioning

**Model Version Format**: `MAJOR.MINOR.PATCH`
- MAJOR: Architecture change
- MINOR: Retraining with new data
- PATCH: Bug fixes, metadata updates

---

## Reproducibility

### Random Seeds
- Data generation: 42
- Train/test split: 42
- Optuna: 42
- SHAP: 42

### Environment
- Python 3.11+
- Requirements pinned in requirements.txt
- Docker for containerization

### Tracking
- MLflow for experiment tracking (optional)
- Git for code versioning
- DVC for data versioning (optional)

---

## Validation Checklist

Before deployment, verify:

- [ ] Test MAE < ₹20,000
- [ ] Test R² > 0.85
- [ ] DP Difference < 0.05 for all attributes
- [ ] MAE by group within 20% of overall
- [ ] Conformal coverage > 80%
- [ ] SHAP explanations generate correctly
- [ ] Similar profiles return reasonable results
- [ ] Fairness recommendations actionable
- [ ] No data leakage in pipeline
- [ ] Protected attributes not in features
- [ ] Model loads and predicts in < 100ms
- [ ] All tests pass

---

## Future Improvements

### Short-term
- [ ] Active learning loop
- [ ] Drift monitoring dashboard
- [ ] A/B testing framework
- [ ] Counterfactual explanations

### Long-term
- [ ] Causal inference for fairness
- [ ] Multi-objective optimization (accuracy + fairness)
- [ ] Federated learning for multi-org
- [ ] Real-time drift alerts
- [ ] Automated retraining pipeline