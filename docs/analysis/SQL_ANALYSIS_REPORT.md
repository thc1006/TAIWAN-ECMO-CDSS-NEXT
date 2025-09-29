# MIMIC-IV ECMO SQL Query Analysis Report

**Analysis Date:** 2025-09-30
**Files Analyzed:**
- `sql/identify_ecmo.sql` (267 lines) - Main ECMO episode identification
- `sql/mimic_ecmo_itemids.sql` (1 line) - Item ID lookup query

**Overall Quality Score:** 7.5/10
**Technical Debt Estimate:** 16 hours

---

## Executive Summary

The SQL query provides a **multi-method approach** to identifying ECMO episodes in MIMIC-IV using:
1. **Procedure codes** (ICD-9/ICD-10-PCS) - HIGH confidence
2. **ECMO medications** (anticoagulation, vasopressors) - MEDIUM confidence
3. **Chart events** (monitoring parameters) - HIGH confidence
4. **Clinical notes** (text mentions) - MEDIUM confidence

**Key Strengths:**
- Comprehensive 4-method identification increases robustness
- Well-structured CTEs with clear documentation
- Confidence scoring via method count aggregation

**Critical Issues:**
- ⚠️ **HIGH**: Full-text search performance bottleneck (lines 99-120)
- ⚠️ **HIGH**: Itemids 227287-227289 require validation
- ⚠️ **MEDIUM**: ECMO type determination overly simplistic

---

## 1. Query Structure

### 1.1 Common Table Expressions (CTEs)

| CTE Name | Lines | Purpose | Output Columns |
|----------|-------|---------|----------------|
| `ecmo_procedures` | 17-44 | ICD-9/10 procedure code identification | subject_id, hadm_id, seq_num, icd_code, icd_version, procedure_description, identification_method |
| `ecmo_medications` | 46-63 | ECMO-related drug identification | subject_id, hadm_id, starttime, endtime, medication_name, identification_method |
| `ecmo_chartevents` | 65-97 | Monitoring parameter identification | subject_id, hadm_id, stay_id, charttime, itemid, label, value, valuenum, identification_method |
| `ecmo_notes` | 99-120 | Clinical note text search | subject_id, hadm_id, chartdate, category, description, identification_method |
| `all_ecmo_episodes` | 123-131 | UNION of all 4 methods | subject_id, hadm_id, identification_method |
| `ecmo_episodes_summary` | 134-142 | Aggregation by patient/admission | subject_id, hadm_id, identification_methods, num_identification_methods |

### 1.2 Main Query Structure

**Final SELECT:** Lines 145-188
- Joins summary with patients, admissions, procedures
- Calculates derived fields (mortality, LOS, ECMO type)
- Orders by confidence (num_identification_methods DESC)

### 1.3 Supplementary Queries

**Query 2: ECMO Timeline** (lines 192-221)
- Time-series parameter extraction
- Categories: flow, pressure, ventilator, temperature, other

**Query 3: Outcomes & Complications** (lines 223-252)
- Complication mapping from ICD diagnosis codes
- Discharge disposition categorization

---

## 2. Database Tables Referenced

### 2.1 MIMIC-IV Hospital Schema (`mimiciv_hosp`)

| Table | Alias | Columns Used | Purpose |
|-------|-------|--------------|---------|
| `procedures_icd` | p | subject_id, hadm_id, seq_num, icd_code, icd_version | Procedure code source |
| `d_icd_procedures` | d | icd_code, icd_version, long_title | Procedure descriptions |
| `patients` | p | subject_id, gender, anchor_age | Demographics |
| `admissions` | a | hadm_id, admittime, dischtime, deathtime, admission_type, admission_location, discharge_location | Admission context |
| `diagnoses_icd` | d | hadm_id, icd_code | Complications |

### 2.2 MIMIC-IV ICU Schema (`mimiciv_icu`)

| Table | Alias | Columns Used | Purpose |
|-------|-------|--------------|---------|
| `prescriptions` | p | subject_id, hadm_id, starttime, endtime, drug, dose_val_rx | Medications |
| `chartevents` | c | subject_id, hadm_id, stay_id, charttime, itemid, value, valuenum, valueuom | Monitoring data |
| `d_items` | d | itemid, label, category | Item definitions |

### 2.3 MIMIC-IV Notes Schema (`mimiciv_note`)

| Table | Alias | Columns Used | Purpose |
|-------|-------|--------------|---------|
| `noteevents` | n | subject_id, hadm_id, chartdate, category, description, text | Clinical notes |

### 2.4 Join Conditions

**Main Query Joins:**
```sql
ecmo_episodes_summary es
  LEFT JOIN patients p ON es.subject_id = p.subject_id
  LEFT JOIN admissions a ON es.hadm_id = a.hadm_id
  LEFT JOIN ecmo_procedures ep ON es.subject_id = ep.subject_id
    AND es.hadm_id = ep.hadm_id
    AND ep.seq_num = (SELECT MIN(seq_num) FROM ecmo_procedures ep2
                      WHERE ep2.subject_id = ep.subject_id
                        AND ep2.hadm_id = ep.hadm_id)
```

⚠️ **Performance Issue:** Correlated subquery for MIN(seq_num) - recommend window function

---

## 3. Codes and Identifiers

### 3.1 ICD-10-PCS Codes (lines 32-38)

| Code | Description | Category |
|------|-------------|----------|
| **5A1522F** | ECMO continuous 24-96 hours | Extracorporeal Assistance |
| **5A1532F** | ECMO continuous >96 hours | Extracorporeal Assistance |
| **5A1522G** | ECMO intermittent <6 hours/day | Extracorporeal Assistance |
| **5A15223** | Extracorporeal oxygenation, membrane | Extracorporeal Assistance |
| **5A1935Z** | Respiratory ventilation <24 hours | Extracorporeal Assistance |

### 3.2 ICD-9 Codes (lines 40-43)

| Code | Description |
|------|-------------|
| **3965** | Extracorporeal membrane oxygenation |
| **3966** | Percutaneous cardiopulmonary bypass |

### 3.3 Medication Patterns (lines 57-62)

| Pattern | Threshold | Purpose | Case-Sensitive |
|---------|-----------|---------|----------------|
| `%heparin%` | - | ECMO anticoagulation | No |
| `%bivalirudin%` | - | Alternative anticoagulation | No |
| `%argatroban%` | - | HIT anticoagulation | No |
| `%norepinephrine%` | >0.5 dose_val_rx | High-dose vasopressor → VA-ECMO | No |
| `%epinephrine%` | >0.3 dose_val_rx | High-dose vasopressor → VA-ECMO | No |

⚠️ **FALSE POSITIVE RISK:** Medications used for many non-ECMO patients

### 3.4 Chart Events Item IDs (lines 91-96)

| ItemID | Label | Status |
|--------|-------|--------|
| **227287** | ECMO Flow | ⚠️ **REQUIRES VERIFICATION** |
| **227288** | ECMO Sweep Gas | ⚠️ **REQUIRES VERIFICATION** |
| **227289** | ECMO Pressure | ⚠️ **REQUIRES VERIFICATION** |

**Action Required:** Run `mimic_ecmo_itemids.sql` to validate

### 3.5 Chart Events Label Patterns (lines 81-89)

| Pattern | Category | Case-Sensitive |
|---------|----------|----------------|
| `%ecmo%flow%` | flow | No (ILIKE) |
| `%extracorporeal%flow%` | flow | No |
| `%ecmo%pressure%` | pressure | No |
| `%sweep%gas%` | ventilator | No |
| `%oxygenator%` | ventilator | No |
| `%cannula% AND %ecmo%` | device | No |
| `%ecmo%circuit%` | device | No |
| `%membrane%oxygenator%` | device | No |

### 3.6 Clinical Notes Text Patterns (lines 111-119)

| Pattern | Purpose | Case-Sensitive |
|---------|---------|----------------|
| `%ecmo%` | Direct ECMO mention | No (LOWER) |
| `%extracorporeal membrane oxygenation%` | Full term | No |
| `%extracorporeal life support%` | Alternative term | No |
| `%ecls%` | ECLS abbreviation | No |
| `%cannul% AND %extracorporeal%` | Cannulation procedure | No |
| `%decannul%` | ECMO removal | No |
| `%wean% AND %ecmo%` | ECMO weaning | No |

### 3.7 Complication ICD Codes (lines 230-234)

| Code Pattern | Description | Complication Type |
|--------------|-------------|-------------------|
| `T82.%` | Device complication | Device-related |
| `D65, D68.%` | Coagulopathy | Bleeding/Clotting |
| `N17.%` | Acute kidney injury | Renal |
| `G93.%` | Brain injury | Neurological |

---

## 4. Identification Methods Analysis

### 4.1 Method Comparison

| Method | Confidence | False Positive Risk | False Negative Risk | Should Use Alone? |
|--------|------------|---------------------|---------------------|-------------------|
| **procedure_code** | HIGH | Low | Medium (undercoding) | ✅ Yes |
| **ecmo_medication** | MEDIUM | HIGH (non-ECMO patients) | Low | ❌ No - supporting only |
| **chart_events** | HIGH | Low | Medium (incomplete documentation) | ✅ Yes |
| **clinical_notes** | MEDIUM | Medium (past ECMO, discussions) | Low | ⚠️ With caution |

### 4.2 Combination Logic (lines 123-142)

**Aggregation Method:** UNION of all four methods

**Confidence Scoring:**
```sql
COUNT(DISTINCT identification_method) as num_identification_methods
```

**Interpretation:**
- **4 methods:** Very high confidence - ECMO confirmed ✅✅✅✅
- **3 methods:** High confidence - likely ECMO ✅✅✅
- **2 methods:** Moderate confidence - review recommended ✅✅
- **1 method:** Low confidence - manual validation required ⚠️

**Sorting:** `ORDER BY num_identification_methods DESC` - highest confidence first

---

## 5. ECMO Type Determination

### 5.1 Current Logic (lines 165-173)

```sql
CASE
    WHEN ep.icd_code IN ('5A1522F', '5A1532F', '5A1522G') THEN
        CASE
            WHEN a.admission_type IN ('URGENT', 'EMERGENCY')
                 OR a.admission_location LIKE '%EMERGENCY%'
            THEN 'VA_likely'
            ELSE 'VV_likely'
        END
    ELSE 'unknown'
END as probable_ecmo_type
```

### 5.2 Logic Rules

| Condition | Result | Rationale |
|-----------|--------|-----------|
| ICD codes present + URGENT/EMERGENCY admission | **VA_likely** | Emergency → cardiogenic shock → VA-ECMO |
| ICD codes present + NOT emergency | **VV_likely** | Elective → respiratory failure → VV-ECMO |
| Other cases | **unknown** | Insufficient information |

### 5.3 Limitations

⚠️ **CRITICAL ISSUES:**
1. **Overly simplistic:** Emergency admissions can have VV-ECMO (e.g., ARDS)
2. **No diagnosis code analysis:** Should check for cardiogenic shock vs respiratory failure
3. **No hybrid configurations:** Doesn't capture VA-VV hybrid ECMO
4. **No hemodynamic data:** Ignores lactate, cardiac output indicators

### 5.4 Improvement Recommendations

**Priority 1 (HIGH):**
- Add diagnosis code analysis:
  - Cardiogenic shock (I50.1, R57.0) → VA-ECMO
  - Respiratory failure (J96.0, J80 ARDS) → VV-ECMO
  - Cardiac arrest (I46.9) → VA-ECMO

**Priority 2 (MEDIUM):**
- Include hemodynamic parameters:
  - Lactate >4 mmol/L → VA-ECMO
  - PaO2/FiO2 <80 → VV-ECMO

**Priority 3 (LOW):**
- NLP extraction of cannulation configuration from procedure notes

---

## 6. Output Schema

### 6.1 Main Query Columns (lines 145-188)

| Column | Data Type | Source | Description | Derived? |
|--------|-----------|--------|-------------|----------|
| `subject_id` | INTEGER | patients.subject_id | Patient identifier | No |
| `gender` | VARCHAR | patients.gender | Patient gender | No |
| `age_at_admission` | INTEGER | patients.anchor_age | Age at admission | No |
| `hadm_id` | INTEGER | admissions.hadm_id | Admission identifier | No |
| `admittime` | TIMESTAMP | admissions.admittime | Admission timestamp | No |
| `dischtime` | TIMESTAMP | admissions.dischtime | Discharge timestamp | No |
| `deathtime` | TIMESTAMP | admissions.deathtime | Death timestamp (NULL if survived) | No |
| `admission_type` | VARCHAR | admissions.admission_type | URGENT, EMERGENCY, ELECTIVE | No |
| `admission_location` | VARCHAR | admissions.admission_location | Admission source | No |
| `discharge_location` | VARCHAR | admissions.discharge_location | Discharge destination | No |
| `identification_methods` | TEXT | STRING_AGG(identification_method) | Comma-separated methods | ✅ Yes |
| `num_identification_methods` | INTEGER | COUNT(DISTINCT identification_method) | Method count (1-4) | ✅ Yes |
| `died_during_admission` | INTEGER | CASE WHEN deathtime IS NOT NULL | Binary mortality (0/1) | ✅ Yes |
| `length_of_stay_days` | NUMERIC | DATE_PART('day', dischtime - admittime) | Hospital LOS (days) | ✅ Yes |
| `probable_ecmo_type` | VARCHAR | CASE statement | VA_likely, VV_likely, unknown | ✅ Yes |
| `primary_ecmo_procedure` | TEXT | d_icd_procedures.long_title | First ECMO procedure description | No |

### 6.2 Query 2: Timeline Columns (lines 192-221)

| Column | Description |
|--------|-------------|
| `subject_id` | Patient identifier |
| `hadm_id` | Admission identifier |
| `stay_id` | ICU stay identifier |
| `charttime` | Measurement timestamp |
| `parameter_name` | ECMO parameter label |
| `value` | Text value |
| `valuenum` | Numeric value |
| `unit_of_measure` | Unit (L/min, mmHg, etc.) |
| `parameter_category` | flow, pressure, ventilator, temperature, other |

### 6.3 Query 3: Outcomes Columns (lines 223-252)

| Column | Description |
|--------|-------------|
| `subject_id` | Patient identifier |
| `hadm_id` | Admission identifier |
| `complications` | Comma-separated complication types |
| `survived_to_discharge` | Binary survival (0/1) |
| `discharge_disposition` | home, rehabilitation, skilled_nursing, hospice, other |

---

## 7. Performance Analysis

### 7.1 Critical Bottlenecks

#### 🔴 **HIGH SEVERITY: Full-Text Search** (lines 99-120)

**Issue:** Multiple LIKE patterns on `noteevents.text`
```sql
LOWER(n.text) LIKE '%ecmo%'
OR LOWER(n.text) LIKE '%extracorporeal membrane oxygenation%'
...
```

**Impact:** Query may **time out** on large databases
**Estimated Performance:** Can be 10-100x slower than indexed search

**Recommended Fix:**
```sql
-- Create full-text index
CREATE INDEX idx_noteevents_text_fts ON mimiciv_note.noteevents
USING GIN (to_tsvector('english', text));

-- Replace LIKE with full-text search
WHERE to_tsvector('english', n.text) @@
      to_tsquery('ecmo | extracorporeal | ecls')
```

**Expected Improvement:** 10-100x faster

---

#### 🟡 **MEDIUM SEVERITY: Correlated Subquery** (lines 182-186)

**Issue:** MIN(seq_num) subquery executes for EACH row
```sql
AND ep.seq_num = (
    SELECT MIN(seq_num)
    FROM ecmo_procedures ep2
    WHERE ep2.subject_id = ep.subject_id
      AND ep2.hadm_id = ep.hadm_id
)
```

**Recommended Fix:**
```sql
-- Use window function instead
WITH ranked_procedures AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY subject_id, hadm_id
               ORDER BY seq_num
           ) as rn
    FROM ecmo_procedures
)
SELECT ... FROM ranked_procedures WHERE rn = 1
```

**Expected Improvement:** 2-5x faster for patients with multiple procedures

---

#### 🟡 **MEDIUM SEVERITY: Multiple ILIKE on Labels** (lines 81-89)

**Issue:** Multiple pattern matches on `d_items.label`

**Recommended Fix:**
```sql
-- Create materialized view of ECMO-related items
CREATE MATERIALIZED VIEW ecmo_items AS
SELECT * FROM mimiciv_icu.d_items
WHERE label ILIKE '%ecmo%'
   OR label ILIKE '%extracorporeal%'
   OR label ILIKE '%sweep%gas%'
   OR label ILIKE '%oxygenator%';

-- Then join to materialized view
FROM mimiciv_icu.chartevents c
INNER JOIN ecmo_items d ON c.itemid = d.itemid
```

**Expected Improvement:** Faster chartevents filtering

---

### 7.2 Missing Indexes

**Recommended Indexes:**

```sql
-- Procedure codes (high priority)
CREATE INDEX idx_procedures_icd_code_version
ON mimiciv_hosp.procedures_icd (icd_code, icd_version);

-- Medications (medium priority)
CREATE INDEX idx_prescriptions_drug_gin
ON mimiciv_icu.prescriptions USING GIN (drug gin_trgm_ops);

-- Chartevents (high priority)
CREATE INDEX idx_chartevents_itemid_subj_hadm
ON mimiciv_icu.chartevents (itemid, subject_id, hadm_id);

-- Clinical notes (critical priority)
CREATE INDEX idx_noteevents_text_fts
ON mimiciv_note.noteevents USING GIN (to_tsvector('english', text));
```

---

### 7.3 Query Plan Analysis

**Recommended Actions:**
1. Run `EXPLAIN ANALYZE` on main query
2. Document execution time and plan costs
3. Identify sequential scans vs. index scans
4. Monitor temp file usage for sorts/aggregations

---

## 8. Data Quality Issues

### 8.1 Missing Codes

#### 🔴 **Critical: Limited ICD-10-PCS Coverage**

**Issue:** Only 5 ICD-10-PCS codes included

**Missing Codes:**
- `5A1522H` - VA-ECMO specific configuration
- Additional pump configurations
- CPT codes (33946-33989) - mentioned in comments but not implemented

**Risk:** False negatives - missing ECMO episodes

**Recommendation:**
1. Review ELSO registry for comprehensive code list
2. Add CPT code filtering if available in MIMIC-IV
3. Cross-reference with CMS ECMO billing codes

---

#### 🔴 **Critical: Itemids Not Validated**

**Issue:** Itemids 227287-227289 marked as "requires verification"

**Risk:** **Zero ECMO chartevents** if itemids are incorrect

**Action Required:**
```sql
-- Run this query to validate
SELECT itemid, label, category
FROM mimiciv_icu.d_items
WHERE LOWER(label) ~ '(ecmo|oxygenator|circuit|sweep)'
ORDER BY itemid;
```

**Next Step:** Update query with actual itemids from MIMIC-IV

---

### 8.2 False Positive Risks

| Source | Risk Level | Description | Mitigation |
|--------|------------|-------------|------------|
| **ecmo_medications** | 🔴 HIGH | Heparin/anticoagulation used for DVT prophylaxis, A-fib, etc. | Use as supporting evidence only; require ≥2 methods |
| **ecmo_notes** | 🟡 MEDIUM | Text may refer to past ECMO, contraindications, family discussions | Implement NLP negation detection |
| **high-dose vasopressors** | 🟡 MEDIUM | Used in septic shock, not just cardiogenic shock | Combine with diagnosis codes |

---

### 8.3 False Negative Risks

| Source | Risk Level | Description | Mitigation |
|--------|------------|-------------|------------|
| **procedure codes** | 🟡 MEDIUM | Undercoding/miscoding of ECMO procedures | Use multiple methods to compensate |
| **chartevents** | 🟡 MEDIUM | Incomplete documentation of ECMO parameters | Validate itemids; add more label patterns |
| **medication data** | 🟢 LOW | Medication name variations/abbreviations | Add more patterns |

---

### 8.4 Missing Critical Fields for ELSO Alignment

**ELSO Registry Requirements NOT Captured:**

🔴 **Critical Missing:**
- Pre-ECMO diagnosis (respiratory failure, cardiac arrest, sepsis)
- Cannulation site and configuration (femoral-femoral, VV dual-lumen, etc.)
- **ECMO duration in hours** (only admission-level data, not ECMO-specific)
- Pre-ECMO severity scores (SOFA, RESP, SAVE)

🟡 **Important Missing:**
- Pre-ECMO ventilator settings (FiO2, PEEP, PIP)
- Pre-ECMO hemodynamics (lactate, pH, PaO2/FiO2)
- ECMO flow rates over time (timeline query partial coverage)
- Sweep gas settings over time
- Transfusion requirements
- Weaning success/failure

**Recommendations for ELSO Compliance:**

```sql
-- Add pre-ECMO severity extraction
WITH pre_ecmo_labs AS (
    SELECT
        subject_id, hadm_id,
        MAX(CASE WHEN itemid = 50813 THEN valuenum END) as lactate,
        MAX(CASE WHEN itemid = 50820 THEN valuenum END) as ph,
        MAX(CASE WHEN itemid = 50821 THEN valuenum END) as pao2
    FROM mimiciv_icu.chartevents
    WHERE charttime < (first_ecmo_time) -- need to define
    GROUP BY subject_id, hadm_id
)
```

---

## 9. Code Quality Assessment

### 9.1 Quality Scoring

| Category | Score | Max | Comments |
|----------|-------|-----|----------|
| **Readability** | 9/10 | 10 | Clear CTEs, good comments, consistent formatting ✅ |
| **Maintainability** | 7/10 | 10 | Long CTEs, magic numbers, repeated patterns ⚠️ |
| **Performance** | 5/10 | 10 | Critical bottlenecks in text search 🔴 |
| **Security** | 9/10 | 10 | No SQL injection risks, parameterized where needed ✅ |
| **Best Practices** | 7/10 | 10 | Good use of CTEs; correlated subquery antipattern ⚠️ |
| **OVERALL** | **7.5/10** | **10** | **Good foundation, needs optimization** |

---

### 9.2 Strengths ✅

1. **Well-structured with clear CTEs** - Logical separation of identification methods
2. **Multiple identification methods** - Robust multi-source approach
3. **Comprehensive code coverage** - Both ICD-9 and ICD-10-PCS
4. **Supplementary queries** - Timeline and outcomes analysis
5. **Good aggregation logic** - STRING_AGG for method combination
6. **Explicit LEFT JOINs** - Clear join relationships
7. **Usage notes included** - Validation guidance in comments

---

### 9.3 Code Smells 🚩

#### **1. Magic Numbers** (lines 61-62)
```sql
OR (LOWER(p.drug) LIKE '%norepinephrine%' AND p.dose_val_rx > 0.5)
OR (LOWER(p.drug) LIKE '%epinephrine%' AND p.dose_val_rx > 0.3)
```

**Recommendation:** Define as named constants
```sql
-- At top of query
WITH config AS (
    SELECT 0.5 as norepinephrine_threshold,
           0.3 as epinephrine_threshold
)
```

---

#### **2. Repeated ILIKE Patterns**
Multiple CTEs repeat similar pattern matching logic

**Recommendation:** Create helper function
```sql
CREATE OR REPLACE FUNCTION contains_any(text, text[]) RETURNS boolean AS $$
    SELECT $1 ~* ('(' || array_to_string($2, '|') || ')')
$$ LANGUAGE SQL IMMUTABLE;

-- Usage
WHERE contains_any(n.text, ARRAY['ecmo', 'extracorporeal', 'ecls'])
```

---

#### **3. Long CTE Definitions**
`ecmo_chartevents` CTE spans 33 lines with complex WHERE clause

**Recommendation:** Break into focused sub-CTEs
```sql
-- Separate item selection from chartevent filtering
WITH ecmo_relevant_items AS (
    SELECT itemid FROM mimiciv_icu.d_items
    WHERE label ILIKE '%ecmo%' OR ...
),
ecmo_chartevents AS (
    SELECT ... FROM mimiciv_icu.chartevents c
    INNER JOIN ecmo_relevant_items ei ON c.itemid = ei.itemid
)
```

---

### 9.4 Refactoring Opportunities

#### **Opportunity 1: Configuration Separation**
**Current:** Codes and thresholds embedded in query
**Proposed:** Separate configuration tables

```sql
-- Create configuration tables
CREATE TABLE ecmo_icd_codes (
    icd_version INT,
    icd_code VARCHAR(10),
    description TEXT,
    ecmo_type VARCHAR(10) -- 'VA', 'VV', 'both'
);

-- Query references configuration
WHERE (p.icd_version, p.icd_code) IN (
    SELECT icd_version, icd_code FROM ecmo_icd_codes
)
```

**Benefit:** Update codes without modifying query
**Effort:** 2-3 hours

---

#### **Opportunity 2: Data Quality Checks**
**Proposed:** Add validation CTEs

```sql
WITH data_quality_checks AS (
    SELECT
        COUNT(*) as total_admissions,
        COUNT(DISTINCT subject_id) as unique_patients,
        SUM(CASE WHEN deathtime IS NULL THEN 1 ELSE 0 END) as missing_outcomes,
        -- Alert if no ECMO episodes found
        CASE WHEN COUNT(*) = 0 THEN 'WARNING: No ECMO episodes identified'
             ELSE 'OK' END as status
    FROM all_ecmo_episodes
)
```

**Benefit:** Early warning of data issues
**Effort:** 2-4 hours

---

#### **Opportunity 3: Modular Query Design**
**Proposed:** Create reusable views

```sql
-- View 1: ECMO identification core
CREATE VIEW ecmo_episodes_core AS
SELECT ... FROM (all 4 methods UNION)

-- View 2: Patient demographics
CREATE VIEW ecmo_patient_details AS
SELECT ... FROM ecmo_episodes_core JOIN patients ...

-- View 3: Clinical outcomes
CREATE VIEW ecmo_outcomes AS
SELECT ... FROM ecmo_episodes_core JOIN admissions ...
```

**Benefit:** Reusable components for dashboards, reports
**Effort:** 3-4 hours

---

## 10. Validation Requirements

### 10.1 Required Validation Steps

| Step | Action | Purpose | Owner | Time |
|------|--------|---------|-------|------|
| 1 | Run query on MIMIC-IV Demo | Verify execution without errors | Data Engineer | 30 min |
| 2 | Validate itemids with `mimic_ecmo_itemids.sql` | Confirm itemids exist and are ECMO-related | Data Analyst | 30 min |
| 3 | Manual chart review (n=20-50) | Validate true positives vs. false positives | Clinical SME | 8 hours |
| 4 | Search for missed ECMO cases | Identify false negatives | Data Analyst | 2 hours |
| 5 | Validate ECMO type classification | Compare VA/VV prediction with documentation | Clinical SME | 4 hours |
| 6 | Run EXPLAIN ANALYZE | Assess performance and bottlenecks | Database Admin | 1 hour |

### 10.2 Quality Metrics to Calculate

| Metric | Formula | Target | How to Calculate |
|--------|---------|--------|------------------|
| **Sensitivity (Recall)** | TP / (TP + FN) | >90% | Chart review gold standard |
| **Specificity** | TN / (TN + FP) | >95% | Random sample of non-ECMO patients |
| **PPV (Precision)** | TP / (TP + FP) | >90% | Chart review of identified episodes |
| **Agreement by Method Count** | Accuracy stratified by num_methods | Hypothesis: ↑ methods = ↑ accuracy | Calculate accuracy for 1, 2, 3, 4 method groups |

### 10.3 Validation Query Example

```sql
-- Gold standard comparison
WITH gold_standard AS (
    -- Manually reviewed ECMO episodes
    SELECT hadm_id, is_ecmo, ecmo_type FROM manual_review
),
query_results AS (
    SELECT hadm_id,
           CASE WHEN num_identification_methods >= 2 THEN 1 ELSE 0 END as predicted_ecmo
    FROM ecmo_episodes_summary
)
SELECT
    SUM(CASE WHEN g.is_ecmo = 1 AND q.predicted_ecmo = 1 THEN 1 ELSE 0 END) as true_positives,
    SUM(CASE WHEN g.is_ecmo = 0 AND q.predicted_ecmo = 1 THEN 1 ELSE 0 END) as false_positives,
    SUM(CASE WHEN g.is_ecmo = 1 AND q.predicted_ecmo = 0 THEN 1 ELSE 0 END) as false_negatives,
    -- Calculate metrics
    ROUND(100.0 * SUM(CASE WHEN g.is_ecmo = 1 AND q.predicted_ecmo = 1 THEN 1 ELSE 0 END) /
          NULLIF(SUM(g.is_ecmo), 0), 1) as sensitivity_pct,
    ROUND(100.0 * SUM(CASE WHEN g.is_ecmo = 1 AND q.predicted_ecmo = 1 THEN 1 ELSE 0 END) /
          NULLIF(SUM(q.predicted_ecmo), 0), 1) as ppv_pct
FROM gold_standard g
FULL OUTER JOIN query_results q ON g.hadm_id = q.hadm_id;
```

---

## 11. Technical Debt Estimate

**Total Estimated Hours:** 16 hours

| Priority | Task | Hours | Owner |
|----------|------|-------|-------|
| 🔴 **HIGH** | Performance optimization (full-text search, window functions) | 4 | Database Developer |
| 🔴 **HIGH** | Validate and update itemids | 2 | Data Engineer |
| 🟡 **MEDIUM** | Improve ECMO type determination logic | 3 | Clinical Informatician |
| 🟡 **MEDIUM** | Add ECMO duration calculation | 3 | Data Engineer |
| 🟡 **MEDIUM** | Create unit tests and validation framework | 4 | QA Engineer |

---

## 12. Next Steps

### 12.1 Immediate Actions (Week 1)

✅ **Action 1:** Run `mimic_ecmo_itemids.sql` to validate itemids
- **Owner:** Data Engineer
- **Time:** 30 minutes
- **Output:** List of actual ECMO-related itemids in MIMIC-IV

✅ **Action 2:** Execute query on MIMIC-IV Demo
- **Owner:** Data Analyst
- **Time:** 1 hour
- **Output:** Query results with episode counts, execution time

✅ **Action 3:** Implement critical performance optimizations
- **Owner:** Database Developer
- **Time:** 4 hours
- **Changes:** Full-text search, window functions, indexes

### 12.2 Medium-Term Actions (Weeks 2-4)

📋 **Action 4:** Conduct manual chart review validation
- **Owner:** Clinical SME + Data Analyst
- **Time:** 8 hours
- **Output:** Sensitivity, specificity, PPV metrics

📋 **Action 5:** Enhance ECMO type classification
- **Owner:** Clinical Informatician
- **Time:** 3 hours
- **Changes:** Add diagnosis code logic, hemodynamic parameters

📋 **Action 6:** Add ECMO duration extraction
- **Owner:** Data Engineer
- **Time:** 3 hours
- **Output:** ECMO start/end timestamps, duration in hours

### 12.3 Long-Term Actions (Month 2+)

🔮 **Action 7:** ELSO registry alignment
- Map all ELSO required fields
- Add pre-ECMO severity scores (SOFA, RESP, SAVE)
- Extract cannulation configurations

🔮 **Action 8:** Create automated validation pipeline
- Unit tests for each CTE
- Integration tests with known ECMO episodes
- Performance regression testing

🔮 **Action 9:** Dashboard and visualization
- Streamlit dashboard for ECMO episodes
- Time-series parameter visualization
- Outcome stratification by ECMO type

---

## 13. Appendix: Query Execution Checklist

### Pre-Execution Checklist

- [ ] Verify MIMIC-IV database connection
- [ ] Confirm all schema tables exist (mimiciv_hosp, mimiciv_icu, mimiciv_note)
- [ ] Check database version compatibility
- [ ] Validate itemids against data dictionary
- [ ] Review query timeout settings (recommend 10+ minutes for large databases)

### Post-Execution Checklist

- [ ] Record execution time
- [ ] Document number of episodes identified
- [ ] Review distribution of identification methods
- [ ] Check for NULL values in critical fields
- [ ] Export results for validation
- [ ] Run EXPLAIN ANALYZE and save query plan

### Validation Checklist

- [ ] Manual review of high-confidence episodes (4 methods)
- [ ] Manual review of low-confidence episodes (1 method)
- [ ] Search discharge summaries for "ECMO" in non-identified admissions
- [ ] Compare VA/VV classification with clinical notes
- [ ] Calculate sensitivity, specificity, PPV
- [ ] Document false positives and false negatives

---

## 14. Summary of ALL Extracted Data

### Complete Code Inventory

**ICD-10-PCS:** 5A1522F, 5A1532F, 5A1522G, 5A15223, 5A1935Z (5 codes)
**ICD-9:** 3965, 3966 (2 codes)
**Complication ICD:** T82.%, D65, D68.%, N17.%, G93.% (5 patterns)
**ItemIDs:** 227287, 227288, 227289 (3 itemids - **UNVALIDATED**)
**Medications:** heparin, bivalirudin, argatroban, norepinephrine (>0.5), epinephrine (>0.3) (5 patterns)
**Chart Label Patterns:** 8 patterns (flow, pressure, sweep gas, oxygenator, cannula, circuit, membrane)
**Note Text Patterns:** 7 patterns (ecmo, extracorporeal membrane oxygenation, ecls, cannulation, decannulation, weaning)

### Database Objects

**Total Tables Referenced:** 9
**Total CTEs:** 6
**Total Queries:** 3 (main + 2 supplementary)
**Total Lines:** 267
**Total Columns Output:** 16 (main query) + 9 (timeline) + 5 (outcomes) = 30 columns

---

**Analysis Complete. For questions or clarifications, contact the Taiwan ECMO CDSS Team.**

---

## 15. Files Generated

1. **C:\Users\thc1006\Desktop\dev\TAIWAN-ECMO-CDSS-NEXT\docs\analysis\sql_query_analysis.json**
   - Comprehensive JSON analysis (all data structured)

2. **C:\Users\thc1006\Desktop\dev\TAIWAN-ECMO-CDSS-NEXT\docs\analysis\SQL_ANALYSIS_REPORT.md**
   - This markdown report (human-readable)

**Next:** Store summary in memory for agent coordination.