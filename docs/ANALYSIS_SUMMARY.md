# Taiwan ECMO CDSS - Complete ML & Economic Models Analysis

**Analysis Date:** 2025-09-30
**Files Analyzed:** 1,799 lines across 4 modules
**Findings:** 157 unique parameters, 23 formulas, 12 algorithms

## Quick Reference

**Detailed JSON Analysis:**
- `C:\Users\thc1006\Desktop\dev\TAIWAN-ECMO-CDSS-NEXT\docs\ml_models_analysis.json`
- `C:\Users\thc1006\Desktop\dev\TAIWAN-ECMO-CDSS-NEXT\docs\economic_models_analysis.json`

---

## 1. ML ARCHITECTURE

### Models
- **3 Algorithms:** LogisticRegression, RandomForest (n=100), GradientBoosting
- **Calibration:** CalibratedClassifierCV (isotonic, cv=3)
- **Selection:** Max AUC-ROC on validation set
- **Explainability:** SHAP (LinearExplainer for LR, TreeExplainer for RF/GBM)

### Features
- **VA-ECMO:** 24 features (demographics, cardiac, NIRS, labs)
- **VV-ECMO:** 25 features (demographics, respiratory, NIRS, labs)

### NIRS Engineering
```python
nirs_trend = min_24h - baseline  # Cerebral, renal, somatic
nirs_variability = abs(cerebral_baseline - cerebral_min) / cerebral_baseline
```

### Risk Scores
**SAVE-II (VA):** Age cutoffs (38, 53), weight <65kg, cardiac arrest, bicarbonate <15
**RESP (VV):** Age ranges (18-49, 60+), immunocompromised, vent >7 days

### Training
- **Split:** 80/20, stratified, random_state=42
- **Imputation:** Median fillna
- **Scaling:** StandardScaler (LR only)
- **Metrics:** AUC-ROC (primary), Brier Score (calibration)

### ⚠️ Issues Identified
1. **No hyperparameter optimization** - Uses defaults only
2. **Limited cross-validation** - Only in calibration (3-fold)
3. **No class imbalance handling** - Stratified split only
4. **Simple imputation** - Median only

---

## 2. COST PARAMETERS (USD)

### Daily Costs
| Item | Cost | Line |
|------|------|------|
| ECMO | $3,500 | 25 |
| ICU | $2,500 | 26 |
| Physician | $800 | 27 |
| Nursing | $1,200 | 28 |
| Dialysis | $1,500 | 42 |
| **Daily Total** | **$8,000** | - |

### One-Time Costs
| Procedure | Cost | Line |
|-----------|------|------|
| Cannulation | $15,000 | 31 |
| Decannulation | $8,000 | 32 |

### Complications (Rate → Cost)
| Complication | Rate | Cost | Lines |
|--------------|------|------|-------|
| Major bleeding | 15% | $25,000 | 130, 35 |
| Stroke | 8% | $45,000 | 137, 36 |
| AKI | 25% | $20,000 | 144, 37 |
| Infection | 20% | $15,000 | 151, 38 |

### Equipment
- **Circuit replacement:** $3,000 every 7 days (line 41, 165)
- **Taiwan multiplier:** 0.65 (35% reduction, line 45, 180)

### Total Cost Formula
```python
total = (daily_cost * duration_days +
         cannulation + decannulation +
         complications + circuits) * 0.65
```

**Example (5-day run):**
$8,000×5 + $15,000 + $8,000 + $20,000 + $3,000 = $86,000 × 0.65 = **$55,900**

---

## 3. QALY CALCULATIONS

### Health Utilities (0-1 scale)
| State | Value | Line |
|-------|-------|------|
| Normal health | 0.90 | 51 |
| On ECMO | 0.20 | 52 |
| Good outcome | 0.80 | 53 |
| Moderate disability | 0.60 | 54 |
| Severe disability | 0.30 | 55 |
| Death | 0.00 | 56 |

### Outcome Distribution (Survivors)
| Outcome | Probability | Utility | Lines |
|---------|-------------|---------|-------|
| Normal | 50% | 0.80 | 212 |
| Mild deficit | 25% | 0.80 | 214 |
| Moderate deficit | 15% | 0.60 | 216 |
| Severe deficit | 10% | 0.30 | 218 |

### Life Expectancy
```python
base = 80 - age_years
adjusted = max(base - 2.0, 0)  # 2-year critical illness reduction
```

### QALY Formula
```python
qalys = utility * adjusted_life_expectancy

# Discounting (mid-point)
if discount_rate > 0:
    factor = 1 / (1 + rate)**(life_exp / 2)
    discounted_qalys = qalys * factor
```

**Example (55yo, good outcome, 3% discount):**
- Life expectancy: (80-55)-2 = 23 years
- QALYs: 0.80 × 23 = 18.4
- Discount factor: 1/(1.03^11.5) = 0.695
- **Discounted QALYs: 12.8**

---

## 4. COST-EFFECTIVENESS METRICS

### ICER Formula
```python
ICER = (intervention_cost - comparator_cost) /
       (intervention_qaly - comparator_qaly)
```

### Interpretation Thresholds (USD/QALY)
| Range | Interpretation | Line |
|-------|----------------|------|
| < $0 | Cost-saving (dominant) | 315 |
| $0 - $20,000 | Very cost-effective | 317 |
| $20,000 - $50,000 | Cost-effective | 319 |
| $50,000 - $100,000 | Moderately CE | 321 |
| ≥ $100,000 | Not cost-effective | 323 |

### WTP Thresholds
- **$50,000/QALY:** Conservative (line 304)
- **$100,000/QALY:** Liberal (line 305)

---

## 5. BUDGET IMPACT ANALYSIS

### Inputs
| Parameter | Default | Range | Line |
|-----------|---------|-------|------|
| Population | 100,000 | 1K-1M | 468 |
| Utilization | 0.001 (0.1%) | 0.01%-1% | 469 |
| Time horizon | 5 years | 1-10 | 470 |
| Discount rate | 3% | 0-10% | 471 |

### Calculations
```python
annual_cases = population × utilization_rate
# Example: 100,000 × 0.001 = 100 cases/year

discount_factor_year_n = 1 / (1 + rate)^(n-1)
yearly_cost = annual_cost × discount_factor
```

### 5-Year Example (100 cases/year, $55,900/case, 3% discount)
| Year | Cases | Cost | Discount | Discounted |
|------|-------|------|----------|------------|
| 1 | 100 | $5.59M | 1.000 | $5.59M |
| 2 | 100 | $5.59M | 0.971 | $5.43M |
| 3 | 100 | $5.59M | 0.943 | $5.27M |
| 4 | 100 | $5.59M | 0.915 | $5.12M |
| 5 | 100 | $5.59M | 0.888 | $4.96M |
| **Total** | **500** | - | - | **$26.37M** |

---

## 6. SENSITIVITY ANALYSIS

### Method
One-way sensitivity: Vary each parameter (low/base/high) while holding others constant

### Output
```python
{parameter: [
    {value: low, icer: X, change: -Y%},
    {value: base, icer: Z, change: 0%},
    {value: high, icer: W, change: +Q%}
]}
```

---

## 7. STREAMLIT DASHBOARD

### Pages
1. **Home** - Overview & quick stats
2. **Risk Assessment** - NIRS-enhanced prediction
3. **Cost-Effectiveness** - Economic analysis
4. **Analytics** - Visualizations
5. **About** - Documentation

### Simplified Risk Model (Demo)
**Base:** 30% mortality risk

| Factor | Condition | Add |
|--------|-----------|-----|
| Age | >65 | +20% |
| Age | >50 | +10% |
| Cerebral rSO2 | <60% | +25% |
| Cerebral rSO2 | <70% | +10% |
| pH | <7.2 | +15% |
| Lactate | >5 | +20% |
| Cardiac arrest (VA) | True | +25% |
| LVEF (VA) | <20% | +15% |
| Immunocompromised (VV) | True | +15% |
| Murray (VV) | >3 | +10% |

**Cap:** 95%

### Feature Contributions (Dashboard)
```python
Age: (age - 50) × 0.005
Cerebral: (70 - rSO2) × 0.003
Renal: (75 - rSO2) × 0.002
pH: (7.35 - pH) × 0.5
Lactate: (lactate - 2) × 0.05
Cardiac arrest: 0.15 if true
LVEF: (40 - LVEF) × 0.003
Murray: (murray - 2) × 0.05
Immunocompromised: 0.1 if true
```

### Clinical Recommendations
| Trigger | Recommendation | Line |
|---------|----------------|------|
| Risk >70% | Multidisciplinary discussion | 437 |
| Cerebral <60% | Monitor neuro complications | 440 |
| Lactate >5 | Address hypoperfusion | 444 |
| VA + arrest | Temperature management | 447 |
| VA + LVEF<20 | Monitor LV distension | 449 |
| VV + immunocomp | Enhanced surveillance | 452 |
| Always | Continue NIRS monitoring | 454 |
| Always | Reassess daily | 455 |

---

## 8. ALL NUMERIC THRESHOLDS

### Risk Scoring
- **SAVE-II:** Age (38, 53), Weight (65), Bicarb (15)
- **RESP:** Age (18-49, 60), Vent duration (7)

### NIRS References
- **Cerebral:** 70%, **Renal:** 75%, **Somatic:** 70%

### Cost/Economic
- **Circuit interval:** 7 days
- **Taiwan multiplier:** 0.65
- **Life expectancy base:** 80 years
- **Critical illness loss:** 2 years

### ICER Thresholds
- **Low:** $20,000/QALY
- **Mid:** $50,000/QALY
- **High:** $100,000/QALY

### Dashboard
- **High risk:** 70%
- **Moderate risk:** 40%
- **Low cerebral:** 60%
- **High lactate:** 5 mmol/L
- **Low pH:** 7.2
- **Low LVEF:** 20%
- **High Murray:** 3

---

## 9. KEY ISSUES & RECOMMENDATIONS

### Critical Issues ⚠️⚠️

**1. No Hyperparameter Optimization**
- Current: Default sklearn parameters
- Impact: Potential 5-15% AUC improvement missed
- Fix: Implement RandomizedSearchCV
```python
param_dist = {
    'n_estimators': [50, 100, 200, 300],
    'max_depth': [10, 20, 30, None],
    'min_samples_split': [2, 5, 10]
}
RandomizedSearchCV(RF(), param_dist, n_iter=50, cv=5)
```

**2. Limited Cross-Validation**
- Current: 3-fold in calibration only
- Impact: Unreliable performance estimates
- Fix: 5-fold StratifiedKFold for model selection

### Moderate Issues ⚠️

**3. No Class Imbalance Handling**
- Current: Stratified split only
- Options: SMOTE, class weights, balanced sampling

**4. Simple Imputation**
- Current: Median fillna
- Options: IterativeImputer, KNNImputer, missingness indicators

**5. External Validation Needed**
- Test on ELSO registry
- Multi-center Taiwan data
- Temporal validation

### Minor Issues

**6. Complication Rates**
- Current: Fixed probabilities with random sampling
- Improvement: Patient-specific risk models

---

## 10. DEMO DATA DISTRIBUTIONS

### Continuous Variables
| Variable | Distribution | Mean | Std | Range |
|----------|-------------|------|-----|-------|
| age_years | Normal | 55 | 15 | [18,85] |
| weight_kg | Normal | 75 | 15 | [40,150] |
| cerebral_so2 | Normal | 70 | 10 | [40,90] |
| lactate | Exponential | scale=3 | - | [0.5,20] |

### Binary Variables
| Variable | P(True) | VA/VV |
|----------|---------|-------|
| cardiac_arrest | 0.40 | VA |
| immunocompromised | 0.30 | VV |
| prone_positioning | 0.60 | VV |
| survived | 0.60 | Both |

### Survival Model
```python
risk = (age-50)*0.02 + (cerebral-70)*-0.03 + (lactate-2)*0.1 + N(0,0.5)
survival_prob = 1 / (1 + exp(risk))
```

---

## 11. COMPLETE ALGORITHM INVENTORY

**Machine Learning (3):**
1. LogisticRegression(random_state=42, max_iter=1000)
2. RandomForestClassifier(n_estimators=100, random_state=42)
3. GradientBoostingClassifier(random_state=42)

**Calibration (1):**
4. CalibratedClassifierCV(method='isotonic', cv=3)

**Feature Engineering (3):**
5. StandardScaler()
6. NIRS trend calculation
7. NIRS variability calculation

**Risk Scoring (2):**
8. SAVE-II score
9. RESP score

**Economic (3):**
10. Cost calculation algorithm
11. QALY calculation algorithm
12. ICER calculation algorithm

---

## 12. VALIDATION CHECKLIST

### ML Model
- [ ] Internal validation (80/20): AUC >0.75
- [ ] Cross-validation (5-fold): AUC >0.72
- [ ] Calibration: slope 0.9-1.1
- [ ] External validation: AUC >0.70
- [ ] Temporal validation: stable over time
- [ ] Subgroup analysis: VA vs VV
- [ ] SHAP: clinically sensible
- [ ] Prospective: 100+ patients
- [ ] Clinical review: expert sign-off
- [ ] Regulatory: FDA/TFDA

### Economic Model
- [ ] Cost parameters: Taiwan-verified
- [ ] Utilities: literature-validated
- [ ] ICER sensitivity: robust
- [ ] Budget impact: institution-aligned
- [ ] Expert review: health economists
- [ ] Stakeholder: administration

### Dashboard
- [ ] UI/UX: clinician-tested
- [ ] Input validation: edge cases
- [ ] Output: clear & actionable
- [ ] Performance: <2s response
- [ ] Mobile: tablet-compatible
- [ ] Accessibility: WCAG 2.1 AA

---

## 13. NEXT STEPS

### Week 1-2 (Immediate)
1. Implement RandomizedSearchCV hyperparameter tuning
2. Add 5-fold StratifiedKFold cross-validation
3. Test SMOTE vs class weights for imbalance

### Month 1-3 (Short-term)
4. Collect 500 VA + 500 VV real patients (Taiwan centers)
5. External validation on ELSO registry subset
6. Prospective validation study (100 patients)

### Month 3-6 (Medium-term)
7. Advanced feature engineering (time-series, interactions)
8. Ensemble methods (stacking, voting)
9. Deep learning exploration (LSTM for NIRS)

### Month 6-12 (Long-term)
10. Multi-center deployment (5+ Taiwan hospitals)
11. Continuous learning pipeline (quarterly updates)
12. Regulatory approval (FDA/TFDA submission)

---

## 14. FILE INVENTORY

### Source Code
- `nirs/risk_models.py` (506 lines) - ML models
- `nirs/features.py` (14 lines) - Feature engineering
- `econ/cost_effectiveness.py` (532 lines) - Economics
- `econ/dashboard.py` (747 lines) - Web UI

### Analysis Outputs
- `docs/ml_models_analysis.json` - Complete ML analysis
- `docs/economic_models_analysis.json` - Complete economic analysis
- `docs/ANALYSIS_SUMMARY.md` - This summary

### Memory Storage
- Claude Flow: `analysis/complete`
- Claude Flow: `analysis/economic`

---

## 15. SUMMARY STATISTICS

**Total Lines Analyzed:** 1,799
**Functions:** 35
**Classes:** 4
**Unique Parameters:** 157
**Formulas Documented:** 23
**Algorithms Identified:** 12
**Cost Values:** 12
**Probability Values:** 10
**Thresholds:** 25+

---

**Analysis Status:** ✅ Complete
**Clinical Review:** ⏳ Pending
**Regulatory Compliance:** ⏳ Pending
**Production Readiness:** ⚠️ Requires validation

---

*This analysis provides complete transparency into all algorithms, hyperparameters, thresholds, costs, and formulas. All values are explicitly documented for reproducibility and regulatory compliance.*
