# FairPay Salary Prediction Model Card

## Model Details

**Model Name:** FairPay Stacking Ensemble  
**Version:** 1.0.0  
**Type:** Stacking Regressor (Linear Regression + Ridge Regression + CatBoost with Ridge meta-learner)  
**Framework:** scikit-learn 1.3+  
**License:** MIT  
**Author:** FairPay Team  
**Date:** 2024  
**Contact:** fairpay@example.com  

## Intended Use

### Primary Use Case
Predict fair salary offers for job candidates based on experience, education, skills, interview performance, location, and company size.

### Intended Users
- HR professionals and hiring managers
- Recruitment teams
- Compensation analysts
- Candidates seeking salary benchmarks

### Out-of-Scope Uses
- Binding salary decisions without human review
- Predictions for roles/locations not in training data
- Historical bias correction without auditing
- Decisions affecting protected classes without fairness review

## Training Data

### Data Source
Synthetic dataset generated to simulate realistic hiring scenarios (5,000 samples).

### Data Composition
| Feature | Type | Range/Categories |
|---------|------|------------------|
| years_experience | Numerical | 0-30 |
| education_level | Categorical | High School, Bachelor, Master, PhD |
| skills_count | Numerical | 1-20 |
| job_role | Categorical | 10 roles (SE, DS, MLE, etc.) |
| previous_salary | Numerical | $30K-$500K |
| interview_score | Numerical | 1-10 |
| location | Categorical | 8 locations (SF, NY, Remote, etc.) |
| company_size | Categorical | 4 sizes (Startup to Large) |
| **gender** | Protected | Male, Female, Non-binary |
| **age** | Protected | 22-65 |

### Data Splits
- Train: 60% (3,000 samples)
- Calibration: 20% (1,000 samples) - for conformal prediction
- Test: 20% (1,000 samples)

### Known Limitations
- **Synthetic data** - Not real hiring data; distributions may not match production
- **Missing values** - ~2% in previous_salary, interview_score, skills_count
- **Class imbalance** - Non-binary gender (2.7%), 50+ age group (0.9%)

## Model Architecture

### Preprocessing Pipeline
1. **Numerical Features**: Median imputation → StandardScaler
2. **Categorical Features**: Most-frequent imputation → OneHotEncoder (handle_unknown=ignore)
3. **ColumnTransformer** with remainder=drop

### Base Models (Optimized via Optuna)
| Model | Best Params | CV MAE | Test MAE |
|-------|-------------|--------|----------|
| Linear Regression | - | $15,014 | $14,683 |
| Ridge Regression | α=0.165 | $15,014 | $14,685 |
| CatBoost | iter=193, depth=8, lr=0.154 | $14,761 | $14,979 |

### Ensemble
**Stacking Regressor** with Ridge(α=1.0) meta-learner, 5-fold CV

## Performance Metrics

### Test Set Results
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| MAE | $13,809 | < $20,000 | ✅ Pass |
| RMSE | $18,218 | < $25,000 | ✅ Pass |
| R² | 0.916 | > 0.85 | ✅ Pass |
| Training Time | 7.0s | < 60s | ✅ Pass |

### Cross-Validation
- 5-fold CV MAE: $15,014 ± $364 (Linear/Ridge baseline)
- Stacking CV not computed (uses base model CV)

## Fairness Evaluation

### Protected Attributes
- **Gender**: Male, Female, Non-binary
- **Age Group**: 20-30, 30-40, 40-50, 50+

### Fairness Metrics (Fairlearn)
| Metric | Gender | Age Group | Threshold |
|--------|--------|-----------|-----------|
| Demographic Parity Difference | 0.077 | 0.058 | < 0.05 ⚠ |
| Equalized Odds Difference | 0.079 | 0.045 | < 0.05 ⚠ |
| MAE Gap (max-min) | $628 | $1,159 | - |

### Mitigation Applied
- **Post-processing calibration** (mean-matching)
- After mitigation: Gender DP=0.029, Age DP=0.027 ✅

### Proxy Feature Analysis
No strong proxies detected (|correlation| > 0.3 or p < 0.05)

### Intersectional Analysis
- Non-binary 50+ group: Small sample (n=1), high variance
- Female 40-50: Slight underprediction (-$48 bias)
- Male 50+: Slight overprediction (+$1,008 bias)

## Explainability

### Global Feature Importance (SHAP Mean |SHAP|)
1. Previous Salary
2. Years of Experience
3. Interview Score
4. Job Role (Engineering Manager, ML Engineer)
5. Location (San Francisco, New York)
6. Education Level (PhD, Master)
7. Company Size (Large)
8. Skills Count

### Local Explanations
Every prediction includes SHAP waterfall plot showing feature contributions pushing salary above/below average.

## Uncertainty Quantification

### Conformal Prediction (Split Conformal)
- **Method**: Split conformal with calibration set
- **Coverage**: 90% nominal, 81.7% actual (test)
- **q̂**: $22,333
- **Avg Interval Width**: $44,667

### Limitations
- Marginal coverage only (not conditional)
- Coverage gap: -8.3%
- Assumes exchangeability of calibration/test data

## Ethical Considerations

### Bias Risks
1. **Historical bias** - Training data may reflect past discriminatory practices
2. **Proxy discrimination** - Features like previous_salary may encode gender/age bias
3. **Representation bias** - Underrepresented groups (non-binary, 50+) have higher uncertainty
4. **Feedback loops** - Model predictions could reinforce existing disparities if used blindly

### Mitigations Implemented
- Protected attributes excluded from features
- Fairness auditing with Fairlearn
- Post-processing calibration for demographic parity
- SHAP explanations for transparency
- Human-in-the-loop requirement

### Recommended Practices
- Quarterly fairness audits
- Retrain with new hiring data annually
- Monitor prediction drift in production
- Maintain human review for all offers
- Document edge cases and disagreements

## Deployment

### Requirements
- Python 3.11+
- scikit-learn, pandas, numpy, joblib
- 500MB RAM minimum
- <100ms latency target

### API Endpoints
- `POST /predict` - Single prediction with interval
- `POST /predict/batch` - Batch predictions (≤1000)
- `GET /health` - Health check
- `GET /model/info` - Model metadata
- `GET /metrics` - Prometheus metrics

### Monitoring
- Latency (P50, P95, P99)
- Prediction drift (PSI, KS-test)
- Performance metrics (MAE, RMSE, R²)
- Fairness metrics (DP, EO)
- Automated alerting

## Maintenance

### Retraining Schedule
- **Monthly**: Drift detection
- **Quarterly**: Fairness audit
- **Annually**: Full retraining with new data
- **On-demand**: Performance degradation alerts

### Versioning
- Semantic versioning (MAJOR.MINOR.PATCH)
- Model artifacts versioned with code
- Rollback capability via MLflow/DVC

## References

1. Fairlearn: A toolkit for assessing and improving fairness in ML
2. SHAP: A unified approach to interpreting model predictions
3. Conformal Prediction: Distribution-free prediction intervals
4. Population Stability Index for drift detection

---

*This model card follows the Google Model Card Toolkit format. Last updated: 2024*