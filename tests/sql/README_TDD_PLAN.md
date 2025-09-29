# MIMIC-IV ECMO Identification - TDD Test Plan

**Project**: Taiwan ECMO CDSS
**Version**: 1.0
**Date**: 2025-09-30
**Analyst**: QA Testing Agent

---

## Executive Summary

This document outlines a comprehensive Test-Driven Development (TDD) approach for validating the MIMIC-IV ECMO episode identification SQL query (`sql/identify_ecmo.sql`). The query consists of 6 CTEs spanning 267 lines and uses 4 identification methods with critical dependencies on unvalidated ItemIDs.

### Critical Findings

1. **UNVALIDATED ItemIDs**: Query hardcodes ItemIDs `227287`, `227288`, `227289` without validation
2. **Performance Bottleneck**: Full-text search on clinical notes (lines 99-120) is major performance risk
3. **False Positive Risk**: Medication-based identification (heparin) may capture non-ECMO cases
4. **Complex Logic**: 6 CTEs with LEFT JOINs and nested subqueries require extensive integration testing

---

## Query Architecture Analysis

### CTE Dependency Graph

```
ecmo_procedures (lines 17-44)
    ↓
ecmo_medications (lines 46-63)
    ↓
ecmo_chartevents (lines 65-97) ← DEPENDS ON: Validated ItemIDs
    ↓
ecmo_notes (lines 99-120) ← PERFORMANCE BOTTLENECK
    ↓
all_ecmo_episodes (lines 123-131) ← UNION of all methods
    ↓
ecmo_episodes_summary (lines 134-142) ← Aggregation by (subject_id, hadm_id)
    ↓
Main Query (lines 145-188) ← JOINs with patients/admissions tables
```

### Identification Methods

| Method | Lines | ICD Codes / Criteria | Risk Level |
|--------|-------|----------------------|------------|
| **procedure_code** | 17-44 | ICD-10: `5A1522F`, `5A1532F`, `5A1522G`, `5A15223`, `5A1935Z`<br>ICD-9: `3965`, `3966` | ✅ LOW - Well-defined codes |
| **ecmo_medication** | 46-63 | Heparin, Bivalirudin, Argatroban<br>High-dose NE (>0.5), Epi (>0.3) | ⚠️ MEDIUM - May capture non-ECMO |
| **chart_events** | 65-97 | ECMO labels (ILIKE patterns)<br>ItemIDs: `227287`, `227288`, `227289` | 🔴 HIGH - ItemIDs unvalidated! |
| **clinical_notes** | 99-120 | Full-text: "ecmo", "extracorporeal", "cannul", "decannul" | 🔴 HIGH - Performance risk |

---

## TDD Test Strategy

### Test Pyramid

```
          /\
         /E2E\       ← 3 tests (Main query, performance, end-to-end)
        /------\
       /Integr.\    ← 5 tests (CTE unions, aggregations, JOINs)
      /----------\
     /   Unit    \  ← 12 tests (Each CTE, each filter, each condition)
    /--------------\
```

**Total Tests**: 20+ SQL test cases

---

## Test Categories

### 0. Pre-Requisite Tests (MUST PASS FIRST)

**TEST-0: ItemID Validation**
- **Purpose**: Validate hardcoded ItemIDs exist in MIMIC-IV `d_items` table
- **Method**: Run `sql/mimic_ecmo_itemids.sql` to discover valid ECMO ItemIDs
- **Expected**: Validate if `227287`, `227288`, `227289` are in `d_items`
- **Failure Impact**: 🔴 CRITICAL - Query will return incorrect results
- **SQL**:
  ```sql
  SELECT itemid, label, category
  FROM mimiciv_icu.d_items
  WHERE LOWER(label) ~ '(ecmo|oxygenator|circuit|sweep)'
  ORDER BY itemid;
  ```
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 36-80

---

### 1. CTE Unit Tests

#### TEST-1.1: ICD-10-PCS Code Filtering
- **Target CTE**: `ecmo_procedures` (lines 17-44)
- **Purpose**: Verify ICD-10 codes are correctly filtered
- **Expected Codes**: `5A1522F`, `5A1532F`, `5A1522G`, `5A15223`, `5A1935Z`
- **Test Logic**:
  ```sql
  SELECT COUNT(*), ARRAY_AGG(DISTINCT icd_code)
  FROM mimiciv_hosp.procedures_icd
  WHERE icd_version = 10
  AND icd_code IN ('5A1522F', '5A1532F', '5A1522G', '5A15223', '5A1935Z');
  ```
- **Pass Criteria**: Returns count ≥ 0, codes match expected set
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 85-121

#### TEST-1.2: ICD-9 Code Filtering
- **Target CTE**: `ecmo_procedures` (lines 17-44)
- **Purpose**: Verify ICD-9 codes are correctly filtered
- **Expected Codes**: `3965`, `3966`
- **Pass Criteria**: Returns count ≥ 0, codes match expected set
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 123-158

#### TEST-1.3: Procedure Description JOIN
- **Target CTE**: `ecmo_procedures` (lines 17-44)
- **Purpose**: Verify LEFT JOIN with `d_icd_procedures` works correctly
- **Test Logic**: Check for NULL `procedure_description` values
- **Pass Criteria**: All procedure codes have non-NULL descriptions (or dataset has no ECMO codes)
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 160-201

#### TEST-2.1: Anticoagulant Medication Detection
- **Target CTE**: `ecmo_medications` (lines 46-63)
- **Purpose**: Verify heparin, bivalirudin, argatroban detection
- **Test Logic**:
  ```sql
  SELECT
    SUM(CASE WHEN LOWER(drug) LIKE '%heparin%' THEN 1 ELSE 0 END) as heparin_count,
    SUM(CASE WHEN LOWER(drug) LIKE '%bivalirudin%' THEN 1 ELSE 0 END) as bivalirudin_count,
    SUM(CASE WHEN LOWER(drug) LIKE '%argatroban%' THEN 1 ELSE 0 END) as argatroban_count
  FROM mimiciv_icu.prescriptions;
  ```
- **Pass Criteria**: Finds at least one anticoagulant prescription
- **Known Risk**: ⚠️ Heparin used for DVT prophylaxis (false positives)
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 207-242

#### TEST-2.2: High-Dose Vasopressor Detection
- **Target CTE**: `ecmo_medications` (lines 46-63)
- **Purpose**: Verify high-dose NE (>0.5) and Epi (>0.3) detection
- **Pass Criteria**: Reports count (informational test)
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 244-276

#### TEST-3.1: ECMO Label Detection in d_items
- **Target CTE**: `ecmo_chartevents` (lines 65-97)
- **Purpose**: Verify ECMO-related labels exist in data dictionary
- **Test Logic**: Check for labels matching patterns: `%ecmo%flow%`, `%sweep%gas%`, `%oxygenator%`, etc.
- **Pass Criteria**: At least 1 ECMO-related label found
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 282-315

#### TEST-3.2: Hardcoded ItemID Validation
- **Target CTE**: `ecmo_chartevents` (lines 91-96)
- **Purpose**: 🔴 CRITICAL - Verify ItemIDs `227287`, `227288`, `227289` exist
- **Test Logic**:
  ```sql
  SELECT COUNT(*), STRING_AGG(itemid || ': ' || label, '; ')
  FROM mimiciv_icu.d_items
  WHERE itemid IN (227287, 227288, 227289);
  ```
- **Pass Criteria**: All 3 ItemIDs found with labels
- **Failure Impact**: Query returns incorrect chartevents data
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 317-358

#### TEST-3.3: Chartevents Query Performance
- **Target CTE**: `ecmo_chartevents` (lines 65-97)
- **Purpose**: Verify chartevents query completes in reasonable time
- **Performance Target**: < 5 seconds
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 360-401

#### TEST-4.1: Clinical Notes Full-Text Search Performance
- **Target CTE**: `ecmo_notes` (lines 99-120)
- **Purpose**: 🔴 CRITICAL - Test full-text search performance on noteevents
- **Performance Target**: < 30 seconds (warning if >10s)
- **Known Risk**: LIKE '%ecmo%' on large text field is SLOW
- **Optimization Recommendation**: Use PostgreSQL full-text search with GiST/GIN indices
- **Test Logic**:
  ```sql
  SELECT COUNT(*)
  FROM mimiciv_note.noteevents
  WHERE LOWER(text) LIKE '%ecmo%'
     OR LOWER(text) LIKE '%extracorporeal%'
     OR LOWER(text) LIKE '%decannul%';
  ```
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 407-463

---

### 5. Integration Tests

#### TEST-5.1: CTE Union Integration
- **Purpose**: Verify all 4 CTEs union correctly in `all_ecmo_episodes`
- **Target CTEs**: Lines 123-131
- **Test Logic**: Count episodes by identification method
- **Pass Criteria**: UNION executes without errors, returns episodes
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 469-528

#### TEST-5.2: Episode Aggregation and Multi-Method Identification
- **Purpose**: Verify aggregation by (subject_id, hadm_id) works correctly
- **Target CTE**: `ecmo_episodes_summary` (lines 134-142)
- **Test Metrics**:
  - Unique episodes (distinct subject_id, hadm_id pairs)
  - Multi-method episodes (num_identification_methods > 1)
  - Average methods per episode
- **Pass Criteria**: Aggregation executes, reports metrics
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 530-582

#### TEST-5.3: Main Query Execution and Performance
- **Purpose**: Verify complete main query (lines 145-188) executes successfully
- **Performance Target**: < 30 seconds on MIMIC-IV Demo
- **Test Logic**: Execute simplified version of main query with all JOINs
- **Pass Criteria**: Query completes in <30s
- **Failure Impact**: ⚠️ Query too slow for production use
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 584-652

---

### 6. Data Validation Tests

#### TEST-6.1: Episode Duration Validation
- **Purpose**: Verify length of stay calculations are valid
- **Test Logic**: Check for negative LOS, NULL dates, excessive LOS (>365 days)
- **Pass Criteria**: Zero negative LOS values
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 658-692

#### TEST-6.2: No Duplicate Episodes
- **Purpose**: Verify each (subject_id, hadm_id) appears only once in final output
- **Test Logic**: Compare COUNT(*) vs COUNT(DISTINCT (subject_id, hadm_id))
- **Pass Criteria**: Counts match exactly
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 694-735

---

### 7. Edge Case Tests

#### TEST-7.1: Multiple ECMO Episodes per Patient
- **Purpose**: Handle patients with >1 ECMO episode (different admissions)
- **Test Logic**: Count patients with multiple hadm_id values
- **Pass Criteria**: Query handles multiple episodes per patient
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 741-782

#### TEST-7.2: Missing Demographic Data
- **Purpose**: Handle NULL gender or age values
- **Test Logic**: Count NULL demographics
- **Pass Criteria**: Query doesn't fail on NULL demographics
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 784-818

#### TEST-7.3: Zero ECMO Episodes (Empty Dataset Edge Case)
- **Purpose**: Handle scenario where no ECMO episodes found
- **Test Logic**: Count ECMO procedure codes
- **Pass Criteria**: Query returns empty result set gracefully
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 820-854

---

### 8. Performance Benchmarks

#### TEST-8.1: Overall Query Performance (<30s Target)
- **Purpose**: 🔴 CRITICAL - Validate complete query meets performance target
- **Performance Target**: < 30,000 ms (30 seconds) on MIMIC-IV Demo
- **Test Logic**: Execute complete query from lines 17-188
- **Pass Criteria**: Execution time < 30s
- **Failure Impact**: Query unsuitable for production/real-time use
- **Optimization Strategies** (if test fails):
  1. Add index on `procedures_icd(icd_code, icd_version)`
  2. Add index on `chartevents(itemid)`
  3. Replace LIKE '%ecmo%' with PostgreSQL full-text search
  4. Consider materialized view for `ecmo_episodes_summary`
- **Test File**: `tests/sql/test_ecmo_identification.sql` lines 860-931

---

## Test Fixtures

### Synthetic Test Data

**File**: `tests/sql/test_fixtures.sql`

10 synthetic test cases covering:
1. ✅ Classic VV-ECMO (multi-method)
2. ✅ VA-ECMO with death (procedure + medication + notes)
3. ✅ ICD-9 legacy code
4. ✅ Chart-only ECMO (no procedure code)
5. ⚠️ FALSE POSITIVE (heparin for DVT, not ECMO)
6. ✅ Patient with 2 separate ECMO episodes
7. ✅ ECMO decannulation mentioned in notes
8. ⚠️ Missing demographic data (NULL gender/age)
9. ✅ Overlapping indicators (all 4 methods)
10. ⚠️ Very long LOS (>365 days)

**Expected Results**: 11 total episodes (including 2 episodes for patient 10006)

---

## Test Execution Plan

### Phase 1: Pre-Requisite Validation
```bash
# Step 1: Validate ItemIDs (MUST RUN FIRST)
psql -d mimic -f sql/mimic_ecmo_itemids.sql

# Expected output: List of valid ECMO ItemIDs
# ACTION: Update identify_ecmo.sql lines 91-96 with valid ItemIDs
```

### Phase 2: Unit Tests
```bash
# Step 2: Run unit tests for each CTE
psql -d mimic -f tests/sql/test_ecmo_identification.sql

# Expected: Tests 1.1 - 4.1 all PASS
# Focus on TEST-0, TEST-3.2 (ItemID validation)
```

### Phase 3: Integration Tests
```bash
# Step 3: Run integration tests
# Tests 5.1 - 5.3 validate complete query

# Expected: Query completes in <30s
```

### Phase 4: Fixture Validation
```bash
# Step 4: Run tests on synthetic data
psql -d test -f tests/sql/test_fixtures.sql

# Expected: 11 episodes identified
# Expected: Test Case 1 has 3 identification methods
# Expected: Test Case 5 is FALSE POSITIVE (1 method only)
```

### Phase 5: Production Validation
```bash
# Step 5: Run on full MIMIC-IV Demo database
psql -d mimic -f sql/identify_ecmo.sql

# Expected: Query completes in <30s
# Expected: Reasonable episode count (10-50 episodes in Demo)
# Expected: No duplicate (subject_id, hadm_id) pairs
```

---

## Performance Optimization Strategies

### If TEST-8.1 Fails (Query >30s)

#### Strategy 1: Add Database Indices
```sql
-- Index on procedure codes
CREATE INDEX idx_procedures_icd_code_version
ON mimiciv_hosp.procedures_icd(icd_code, icd_version);

-- Index on chartevents itemid
CREATE INDEX idx_chartevents_itemid
ON mimiciv_icu.chartevents(itemid);

-- Index on prescriptions drug (for LIKE queries)
CREATE INDEX idx_prescriptions_drug_lower
ON mimiciv_icu.prescriptions(LOWER(drug));
```

#### Strategy 2: Replace Full-Text LIKE with PostgreSQL FTS
```sql
-- Create full-text search index on noteevents
ALTER TABLE mimiciv_note.noteevents
ADD COLUMN text_tsv tsvector;

UPDATE mimiciv_note.noteevents
SET text_tsv = to_tsvector('english', text);

CREATE INDEX idx_noteevents_text_tsv
ON mimiciv_note.noteevents USING GIN(text_tsv);

-- Replace LIKE queries with:
WHERE text_tsv @@ to_tsquery('ecmo | extracorporeal | cannul | decannul')
```

#### Strategy 3: Materialize Intermediate Results
```sql
-- Create materialized view for episode summary
CREATE MATERIALIZED VIEW mv_ecmo_episodes_summary AS
SELECT
    subject_id, hadm_id,
    STRING_AGG(DISTINCT identification_method, ', ') as methods,
    COUNT(DISTINCT identification_method) as num_methods
FROM all_ecmo_episodes
GROUP BY subject_id, hadm_id;

-- Refresh periodically
REFRESH MATERIALIZED VIEW mv_ecmo_episodes_summary;
```

---

## Known Issues and Risks

### 🔴 CRITICAL Issues

1. **Unvalidated ItemIDs (lines 91-96)**
   - ItemIDs `227287`, `227288`, `227289` are hardcoded without validation
   - **Risk**: May not exist in MIMIC-IV, causing silent failures
   - **Mitigation**: TEST-0 and TEST-3.2 MUST pass before production use

2. **Full-Text Search Performance (lines 99-120)**
   - LIKE '%ecmo%' on large text fields is extremely slow
   - **Risk**: Query timeout on large datasets
   - **Mitigation**: TEST-4.1 monitors performance, Strategy 2 optimizes with FTS

### ⚠️ MEDIUM Issues

3. **False Positives from Medications (lines 46-63)**
   - Heparin is used for DVT prophylaxis, NOT just ECMO
   - **Risk**: Over-identification of ECMO episodes
   - **Mitigation**: Multi-method identification provides confidence scoring

4. **ECMO Type Determination (lines 165-173)**
   - Probabilistic logic may misclassify VA vs VV ECMO
   - **Risk**: Incorrect ECMO type for clinical research
   - **Mitigation**: Manual review recommended for VA/VV classification

---

## Test Deliverables

### SQL Files
1. ✅ `tests/sql/test_ecmo_identification.sql` - 20+ comprehensive tests
2. ✅ `tests/sql/test_fixtures.sql` - 10 synthetic test cases
3. ✅ `tests/sql/README_TDD_PLAN.md` - This document

### Expected Outputs
1. **Test Results Table**: `ecmo_test.test_results` with pass/fail status
2. **Test Summary**: Pass rate by category (unit, integration, performance)
3. **Performance Metrics**: Execution time for each test
4. **Critical Failures Report**: Lists TEST-0, TEST-3.2, TEST-8.1 failures

---

## Test Acceptance Criteria

### Minimum Requirements for Production Use

✅ **TEST-0**: ItemID validation PASS
✅ **All Unit Tests (1.1-4.1)**: PASS rate ≥ 90%
✅ **All Integration Tests (5.1-5.3)**: PASS rate = 100%
✅ **TEST-8.1**: Query performance < 30 seconds
✅ **No duplicate episodes**: TEST-6.2 PASS
✅ **Fixture validation**: 11/11 episodes identified correctly

### Recommended Additional Validation

🔹 Manual review of 10 randomly selected episodes
🔹 Cross-reference with hospital ECMO registry (if available)
🔹 Clinical validation of VA vs VV classification
🔹 Comparison with published ECMO cohort studies (ELSO registry)

---

## Maintenance and Monitoring

### Continuous Testing
- Run test suite monthly on updated MIMIC-IV data
- Monitor TEST-8.1 performance degradation over time
- Track false positive rate from TEST-5.2 (single-method episodes)

### Query Evolution
- Update ICD codes as ICD-11 is adopted
- Refine medication criteria based on false positive analysis
- Validate new ItemIDs if MIMIC schema updates

---

## References

- **MIMIC-IV Documentation**: https://mimic.mit.edu/docs/iv/
- **ICD-10-PCS Codes**: https://www.cms.gov/medicare/coding-billing/icd-10-codes
- **ELSO Registry**: https://www.elso.org/registry/
- **Taiwan ECMO CDSS Spec**: `CLAUDE.md`, `prompts/SQL_identify_ecmo.md`

---

**Document Status**: ✅ Complete
**Review Required**: Senior Clinical Data Engineer
**Next Steps**: Execute TEST-0 and TEST-3.2 immediately
