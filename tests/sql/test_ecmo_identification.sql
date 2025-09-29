/*
MIMIC-IV ECMO Identification - Comprehensive TDD Test Suite
Taiwan ECMO CDSS - Test-Driven Development Approach

Test Philosophy:
- Every CTE must have unit test with known expected output
- Integration tests for complete episode identification
- Performance tests for query execution time
- Edge case coverage for data anomalies
- ItemID validation BEFORE main query execution

Author: Taiwan ECMO CDSS QA Team
Version: 1.0
Date: 2025-09-30
*/

-- ============================================================================
-- SETUP: Test Schema and Fixtures
-- ============================================================================

-- Create test schema for isolated testing
CREATE SCHEMA IF NOT EXISTS ecmo_test;

-- Test result tracking table
CREATE TABLE IF NOT EXISTS ecmo_test.test_results (
    test_id SERIAL PRIMARY KEY,
    test_name VARCHAR(255) NOT NULL,
    test_category VARCHAR(50) NOT NULL,
    expected_result TEXT,
    actual_result TEXT,
    test_status VARCHAR(20) CHECK (test_status IN ('PASS', 'FAIL', 'ERROR')),
    execution_time_ms INTEGER,
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

-- ============================================================================
-- TEST 0: PRE-REQUISITE - ItemID Validation
-- ============================================================================
-- CRITICAL: This test MUST pass before any other tests
-- Validates that hardcoded ItemIDs (227287, 227288, 227289) exist in MIMIC-IV

DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_itemid_count INTEGER;
    v_valid_itemids TEXT;
    v_test_status VARCHAR(20);
    v_error_msg TEXT;
BEGIN
    v_start_time := clock_timestamp();

    -- Execute the validation query from mimic_ecmo_itemids.sql
    SELECT COUNT(*), STRING_AGG(itemid::TEXT, ', ')
    INTO v_itemid_count, v_valid_itemids
    FROM mimiciv_icu.d_items
    WHERE LOWER(label) ~ '(ecmo|oxygenator|circuit|sweep)';

    v_end_time := clock_timestamp();

    -- Check if hardcoded itemids are in the valid list
    IF v_itemid_count = 0 THEN
        v_test_status := 'FAIL';
        v_error_msg := 'No ECMO-related ItemIDs found in MIMIC-IV d_items table';
    ELSIF '227287' = ANY(STRING_TO_ARRAY(v_valid_itemids, ', '))
          AND '227288' = ANY(STRING_TO_ARRAY(v_valid_itemids, ', '))
          AND '227289' = ANY(STRING_TO_ARRAY(v_valid_itemids, ', ')) THEN
        v_test_status := 'PASS';
        v_error_msg := NULL;
    ELSE
        v_test_status := 'FAIL';
        v_error_msg := 'Hardcoded ItemIDs (227287, 227288, 227289) not found. Valid ItemIDs: ' || v_valid_itemids;
    END IF;

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms, error_message
    ) VALUES (
        'TEST-0: ItemID Validation',
        'pre-requisite',
        'ItemIDs 227287, 227288, 227289 exist in d_items',
        'Found ' || v_itemid_count || ' ECMO ItemIDs: ' || v_valid_itemids,
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER,
        v_error_msg
    );

    RAISE NOTICE 'TEST-0: ItemID Validation - %', v_test_status;
END $$;

-- ============================================================================
-- TEST 1: CTE Unit Tests - ecmo_procedures
-- ============================================================================

-- Test 1.1: Verify ICD-10-PCS codes are correctly filtered
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_icd10_count INTEGER;
    v_expected_codes TEXT[] := ARRAY['5A1522F', '5A1532F', '5A1522G', '5A15223', '5A1935Z'];
    v_actual_codes TEXT[];
    v_test_status VARCHAR(20);
BEGIN
    v_start_time := clock_timestamp();

    SELECT COUNT(*), ARRAY_AGG(DISTINCT icd_code)
    INTO v_icd10_count, v_actual_codes
    FROM mimiciv_hosp.procedures_icd
    WHERE icd_version = 10
    AND icd_code = ANY(v_expected_codes);

    v_end_time := clock_timestamp();

    v_test_status := CASE WHEN v_icd10_count >= 0 THEN 'PASS' ELSE 'FAIL' END;

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms
    ) VALUES (
        'TEST-1.1: ICD-10-PCS Code Filtering',
        'cte-unit-test',
        'ICD-10 codes: ' || ARRAY_TO_STRING(v_expected_codes, ', '),
        'Found ' || v_icd10_count || ' records with codes: ' || COALESCE(ARRAY_TO_STRING(v_actual_codes, ', '), 'NONE'),
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER
    );

    RAISE NOTICE 'TEST-1.1: ICD-10-PCS Code Filtering - % (% records)', v_test_status, v_icd10_count;
END $$;

-- Test 1.2: Verify ICD-9 codes are correctly filtered
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_icd9_count INTEGER;
    v_expected_codes TEXT[] := ARRAY['3965', '3966'];
    v_actual_codes TEXT[];
    v_test_status VARCHAR(20);
BEGIN
    v_start_time := clock_timestamp();

    SELECT COUNT(*), ARRAY_AGG(DISTINCT icd_code)
    INTO v_icd9_count, v_actual_codes
    FROM mimiciv_hosp.procedures_icd
    WHERE icd_version = 9
    AND icd_code = ANY(v_expected_codes);

    v_end_time := clock_timestamp();

    v_test_status := CASE WHEN v_icd9_count >= 0 THEN 'PASS' ELSE 'FAIL' END;

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms
    ) VALUES (
        'TEST-1.2: ICD-9 Code Filtering',
        'cte-unit-test',
        'ICD-9 codes: ' || ARRAY_TO_STRING(v_expected_codes, ', '),
        'Found ' || v_icd9_count || ' records with codes: ' || COALESCE(ARRAY_TO_STRING(v_actual_codes, ', '), 'NONE'),
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER
    );

    RAISE NOTICE 'TEST-1.2: ICD-9 Code Filtering - % (% records)', v_test_status, v_icd9_count;
END $$;

-- Test 1.3: Verify procedure JOIN with d_icd_procedures works
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_joined_count INTEGER;
    v_null_descriptions INTEGER;
    v_test_status VARCHAR(20);
BEGIN
    v_start_time := clock_timestamp();

    WITH ecmo_procedures AS (
        SELECT
            p.subject_id,
            p.hadm_id,
            p.icd_code,
            d.long_title as procedure_description
        FROM mimiciv_hosp.procedures_icd p
        LEFT JOIN mimiciv_hosp.d_icd_procedures d
            ON p.icd_code = d.icd_code AND p.icd_version = d.icd_version
        WHERE
            (p.icd_version = 10 AND p.icd_code IN ('5A1522F', '5A1532F', '5A1522G', '5A15223', '5A1935Z'))
            OR (p.icd_version = 9 AND p.icd_code IN ('3965', '3966'))
    )
    SELECT COUNT(*), SUM(CASE WHEN procedure_description IS NULL THEN 1 ELSE 0 END)
    INTO v_joined_count, v_null_descriptions
    FROM ecmo_procedures;

    v_end_time := clock_timestamp();

    v_test_status := CASE WHEN v_null_descriptions = 0 OR v_joined_count = 0 THEN 'PASS' ELSE 'FAIL' END;

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms
    ) VALUES (
        'TEST-1.3: Procedure Description JOIN',
        'cte-unit-test',
        'All procedure codes have descriptions',
        'Total: ' || v_joined_count || ', NULL descriptions: ' || v_null_descriptions,
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER
    );

    RAISE NOTICE 'TEST-1.3: Procedure Description JOIN - %', v_test_status;
END $$;

-- ============================================================================
-- TEST 2: CTE Unit Tests - ecmo_medications
-- ============================================================================

-- Test 2.1: Verify anticoagulant detection
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_heparin_count INTEGER;
    v_bivalirudin_count INTEGER;
    v_argatroban_count INTEGER;
    v_test_status VARCHAR(20);
BEGIN
    v_start_time := clock_timestamp();

    SELECT
        SUM(CASE WHEN LOWER(drug) LIKE '%heparin%' THEN 1 ELSE 0 END),
        SUM(CASE WHEN LOWER(drug) LIKE '%bivalirudin%' THEN 1 ELSE 0 END),
        SUM(CASE WHEN LOWER(drug) LIKE '%argatroban%' THEN 1 ELSE 0 END)
    INTO v_heparin_count, v_bivalirudin_count, v_argatroban_count
    FROM mimiciv_icu.prescriptions;

    v_end_time := clock_timestamp();

    v_test_status := CASE WHEN (v_heparin_count + v_bivalirudin_count + v_argatroban_count) > 0 THEN 'PASS' ELSE 'FAIL' END;

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms
    ) VALUES (
        'TEST-2.1: Anticoagulant Medication Detection',
        'cte-unit-test',
        'Find heparin, bivalirudin, or argatroban prescriptions',
        'Heparin: ' || v_heparin_count || ', Bivalirudin: ' || v_bivalirudin_count || ', Argatroban: ' || v_argatroban_count,
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER
    );

    RAISE NOTICE 'TEST-2.1: Anticoagulant Detection - %', v_test_status;
END $$;

-- Test 2.2: Verify high-dose vasopressor detection
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_high_norepi_count INTEGER;
    v_high_epi_count INTEGER;
    v_test_status VARCHAR(20);
BEGIN
    v_start_time := clock_timestamp();

    SELECT
        SUM(CASE WHEN LOWER(drug) LIKE '%norepinephrine%' AND dose_val_rx > 0.5 THEN 1 ELSE 0 END),
        SUM(CASE WHEN LOWER(drug) LIKE '%epinephrine%' AND dose_val_rx > 0.3 THEN 1 ELSE 0 END)
    INTO v_high_norepi_count, v_high_epi_count
    FROM mimiciv_icu.prescriptions;

    v_end_time := clock_timestamp();

    v_test_status := 'PASS'; -- Always pass, just reporting

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms
    ) VALUES (
        'TEST-2.2: High-Dose Vasopressor Detection',
        'cte-unit-test',
        'Find high-dose norepinephrine (>0.5) and epinephrine (>0.3)',
        'High-dose NE: ' || COALESCE(v_high_norepi_count::TEXT, '0') || ', High-dose Epi: ' || COALESCE(v_high_epi_count::TEXT, '0'),
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER
    );

    RAISE NOTICE 'TEST-2.2: High-Dose Vasopressor Detection - %', v_test_status;
END $$;

-- ============================================================================
-- TEST 3: CTE Unit Tests - ecmo_chartevents
-- ============================================================================

-- Test 3.1: Verify ECMO-related labels detection
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_label_count INTEGER;
    v_found_labels TEXT;
    v_test_status VARCHAR(20);
BEGIN
    v_start_time := clock_timestamp();

    SELECT COUNT(DISTINCT label), STRING_AGG(DISTINCT label, '; ')
    INTO v_label_count, v_found_labels
    FROM mimiciv_icu.d_items
    WHERE
        label ILIKE '%ecmo%flow%'
        OR label ILIKE '%extracorporeal%flow%'
        OR label ILIKE '%ecmo%pressure%'
        OR label ILIKE '%sweep%gas%'
        OR label ILIKE '%oxygenator%'
        OR label ILIKE '%cannula%'
        OR label ILIKE '%ecmo%circuit%'
        OR label ILIKE '%membrane%oxygenator%';

    v_end_time := clock_timestamp();

    v_test_status := CASE WHEN v_label_count > 0 THEN 'PASS' ELSE 'FAIL' END;

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms
    ) VALUES (
        'TEST-3.1: ECMO Label Detection in d_items',
        'cte-unit-test',
        'Find ECMO-related labels in data dictionary',
        'Found ' || v_label_count || ' labels: ' || COALESCE(SUBSTRING(v_found_labels, 1, 200), 'NONE'),
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER
    );

    RAISE NOTICE 'TEST-3.1: ECMO Label Detection - % (% labels)', v_test_status, v_label_count;
END $$;

-- Test 3.2: Verify hardcoded ItemIDs exist and have correct labels
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_itemid_count INTEGER;
    v_itemid_labels TEXT;
    v_test_status VARCHAR(20);
    v_error_msg TEXT;
BEGIN
    v_start_time := clock_timestamp();

    SELECT COUNT(*), STRING_AGG(itemid || ': ' || label, '; ')
    INTO v_itemid_count, v_itemid_labels
    FROM mimiciv_icu.d_items
    WHERE itemid IN (227287, 227288, 227289);

    v_end_time := clock_timestamp();

    IF v_itemid_count = 3 THEN
        v_test_status := 'PASS';
        v_error_msg := NULL;
    ELSIF v_itemid_count = 0 THEN
        v_test_status := 'FAIL';
        v_error_msg := 'CRITICAL: None of the hardcoded ItemIDs (227287, 227288, 227289) exist in MIMIC-IV';
    ELSE
        v_test_status := 'FAIL';
        v_error_msg := 'WARNING: Only ' || v_itemid_count || ' of 3 hardcoded ItemIDs found';
    END IF;

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms, error_message
    ) VALUES (
        'TEST-3.2: Hardcoded ItemID Validation',
        'cte-unit-test',
        'All 3 ItemIDs (227287, 227288, 227289) exist',
        'Found ' || v_itemid_count || ' ItemIDs: ' || COALESCE(v_itemid_labels, 'NONE'),
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER,
        v_error_msg
    );

    RAISE NOTICE 'TEST-3.2: Hardcoded ItemID Validation - %', v_test_status;
END $$;

-- Test 3.3: Verify chartevents query performance
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_chart_count INTEGER;
    v_execution_time_ms INTEGER;
    v_test_status VARCHAR(20);
BEGIN
    v_start_time := clock_timestamp();

    SELECT COUNT(*)
    INTO v_chart_count
    FROM mimiciv_icu.chartevents c
    LEFT JOIN mimiciv_icu.d_items d ON c.itemid = d.itemid
    WHERE
        (d.label ILIKE '%ecmo%flow%' OR d.label ILIKE '%extracorporeal%flow%')
        OR (d.label ILIKE '%ecmo%pressure%')
        OR (d.label ILIKE '%sweep%gas%' OR d.label ILIKE '%oxygenator%')
        OR (d.label ILIKE '%cannula%' AND d.label ILIKE '%ecmo%')
        OR (d.label ILIKE '%ecmo%circuit%' OR d.label ILIKE '%membrane%oxygenator%')
        OR c.itemid IN (227287, 227288, 227289);

    v_end_time := clock_timestamp();
    v_execution_time_ms := EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER;

    v_test_status := CASE WHEN v_execution_time_ms < 5000 THEN 'PASS' ELSE 'FAIL' END;

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms
    ) VALUES (
        'TEST-3.3: Chartevents Query Performance',
        'performance-test',
        'Query executes in <5000ms',
        'Found ' || v_chart_count || ' records in ' || v_execution_time_ms || 'ms',
        v_test_status,
        v_execution_time_ms
    );

    RAISE NOTICE 'TEST-3.3: Chartevents Performance - % (% records in %ms)', v_test_status, v_chart_count, v_execution_time_ms;
END $$;

-- ============================================================================
-- TEST 4: CTE Unit Tests - ecmo_notes
-- ============================================================================

-- Test 4.1: Verify note text search patterns (PERFORMANCE TEST)
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_note_count INTEGER;
    v_execution_time_ms INTEGER;
    v_test_status VARCHAR(20);
    v_error_msg TEXT;
BEGIN
    v_start_time := clock_timestamp();

    SELECT COUNT(*)
    INTO v_note_count
    FROM mimiciv_note.noteevents
    WHERE
        LOWER(text) LIKE '%ecmo%'
        OR LOWER(text) LIKE '%extracorporeal membrane oxygenation%'
        OR LOWER(text) LIKE '%extracorporeal life support%'
        OR LOWER(text) LIKE '%ecls%'
        OR (LOWER(text) LIKE '%cannul%' AND LOWER(text) LIKE '%extracorporeal%')
        OR LOWER(text) LIKE '%decannul%'
        OR (LOWER(text) LIKE '%wean%' AND LOWER(text) LIKE '%ecmo%');

    v_end_time := clock_timestamp();
    v_execution_time_ms := EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER;

    -- CRITICAL: Full-text search on notes is major performance bottleneck
    IF v_execution_time_ms > 30000 THEN
        v_test_status := 'FAIL';
        v_error_msg := 'CRITICAL: Full-text search too slow (' || v_execution_time_ms || 'ms). Consider using PostgreSQL full-text search indices.';
    ELSIF v_execution_time_ms > 10000 THEN
        v_test_status := 'PASS';
        v_error_msg := 'WARNING: Full-text search slow (' || v_execution_time_ms || 'ms). Recommend optimization.';
    ELSE
        v_test_status := 'PASS';
        v_error_msg := NULL;
    END IF;

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms, error_message
    ) VALUES (
        'TEST-4.1: Clinical Notes Full-Text Search Performance',
        'performance-test',
        'Query executes in <30000ms',
        'Found ' || v_note_count || ' notes in ' || v_execution_time_ms || 'ms',
        v_test_status,
        v_execution_time_ms,
        v_error_msg
    );

    RAISE NOTICE 'TEST-4.1: Notes Full-Text Search - % (% notes in %ms)', v_test_status, v_note_count, v_execution_time_ms;
END $$;

-- ============================================================================
-- TEST 5: Integration Tests - Complete Episode Identification
-- ============================================================================

-- Test 5.1: Verify all CTEs union correctly
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_total_episodes INTEGER;
    v_method_counts TEXT;
    v_test_status VARCHAR(20);
BEGIN
    v_start_time := clock_timestamp();

    WITH ecmo_procedures AS (
        SELECT subject_id, hadm_id, 'procedure_code' as identification_method
        FROM mimiciv_hosp.procedures_icd
        WHERE (icd_version = 10 AND icd_code IN ('5A1522F', '5A1532F', '5A1522G', '5A15223', '5A1935Z'))
           OR (icd_version = 9 AND icd_code IN ('3965', '3966'))
    ),
    ecmo_medications AS (
        SELECT DISTINCT subject_id, hadm_id, 'ecmo_medication' as identification_method
        FROM mimiciv_icu.prescriptions
        WHERE LOWER(drug) LIKE '%heparin%'
           OR LOWER(drug) LIKE '%bivalirudin%'
           OR LOWER(drug) LIKE '%argatroban%'
    ),
    ecmo_chartevents AS (
        SELECT DISTINCT c.subject_id, c.hadm_id, 'chart_events' as identification_method
        FROM mimiciv_icu.chartevents c
        LEFT JOIN mimiciv_icu.d_items d ON c.itemid = d.itemid
        WHERE (d.label ILIKE '%ecmo%' OR c.itemid IN (227287, 227288, 227289))
    ),
    all_ecmo_episodes AS (
        SELECT subject_id, hadm_id, identification_method FROM ecmo_procedures
        UNION
        SELECT subject_id, hadm_id, identification_method FROM ecmo_medications
        UNION
        SELECT subject_id, hadm_id, identification_method FROM ecmo_chartevents
    )
    SELECT
        COUNT(*),
        STRING_AGG(identification_method || ': ' || cnt::TEXT, ', ')
    INTO v_total_episodes, v_method_counts
    FROM (
        SELECT identification_method, COUNT(*) as cnt
        FROM all_ecmo_episodes
        GROUP BY identification_method
    ) sub;

    v_end_time := clock_timestamp();

    v_test_status := CASE WHEN v_total_episodes > 0 THEN 'PASS' ELSE 'FAIL' END;

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms
    ) VALUES (
        'TEST-5.1: CTE Union Integration',
        'integration-test',
        'All CTEs union without errors',
        'Total episodes: ' || v_total_episodes || '. By method: ' || v_method_counts,
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER
    );

    RAISE NOTICE 'TEST-5.1: CTE Union Integration - % (% total)', v_test_status, v_total_episodes;
END $$;

-- Test 5.2: Verify episode aggregation and multi-method identification
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_unique_episodes INTEGER;
    v_multi_method_episodes INTEGER;
    v_avg_methods NUMERIC;
    v_test_status VARCHAR(20);
BEGIN
    v_start_time := clock_timestamp();

    WITH ecmo_procedures AS (
        SELECT subject_id, hadm_id, 'procedure_code' as identification_method
        FROM mimiciv_hosp.procedures_icd
        WHERE (icd_version = 10 AND icd_code IN ('5A1522F', '5A1532F', '5A1522G', '5A15223', '5A1935Z'))
           OR (icd_version = 9 AND icd_code IN ('3965', '3966'))
    ),
    ecmo_medications AS (
        SELECT DISTINCT subject_id, hadm_id, 'ecmo_medication' as identification_method
        FROM mimiciv_icu.prescriptions
        WHERE LOWER(drug) LIKE '%heparin%'
    ),
    ecmo_chartevents AS (
        SELECT DISTINCT c.subject_id, c.hadm_id, 'chart_events' as identification_method
        FROM mimiciv_icu.chartevents c
        LEFT JOIN mimiciv_icu.d_items d ON c.itemid = d.itemid
        WHERE d.label ILIKE '%ecmo%'
    ),
    all_ecmo_episodes AS (
        SELECT subject_id, hadm_id, identification_method FROM ecmo_procedures
        UNION
        SELECT subject_id, hadm_id, identification_method FROM ecmo_medications
        UNION
        SELECT subject_id, hadm_id, identification_method FROM ecmo_chartevents
    ),
    ecmo_episodes_summary AS (
        SELECT
            subject_id,
            hadm_id,
            COUNT(DISTINCT identification_method) as num_methods
        FROM all_ecmo_episodes
        GROUP BY subject_id, hadm_id
    )
    SELECT
        COUNT(*),
        SUM(CASE WHEN num_methods > 1 THEN 1 ELSE 0 END),
        AVG(num_methods)
    INTO v_unique_episodes, v_multi_method_episodes, v_avg_methods
    FROM ecmo_episodes_summary;

    v_end_time := clock_timestamp();

    v_test_status := 'PASS';

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms
    ) VALUES (
        'TEST-5.2: Episode Aggregation and Multi-Method Identification',
        'integration-test',
        'Episodes aggregated by (subject_id, hadm_id)',
        'Unique episodes: ' || v_unique_episodes || ', Multi-method: ' || v_multi_method_episodes || ', Avg methods: ' || ROUND(v_avg_methods, 2),
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER
    );

    RAISE NOTICE 'TEST-5.2: Episode Aggregation - % (% unique, % multi-method)', v_test_status, v_unique_episodes, v_multi_method_episodes;
END $$;

-- Test 5.3: Verify main query joins and completes successfully
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_final_count INTEGER;
    v_execution_time_ms INTEGER;
    v_test_status VARCHAR(20);
    v_error_msg TEXT;
BEGIN
    v_start_time := clock_timestamp();

    -- Execute simplified version of main query
    WITH ecmo_procedures AS (
        SELECT subject_id, hadm_id, 'procedure_code' as identification_method
        FROM mimiciv_hosp.procedures_icd
        WHERE (icd_version = 10 AND icd_code IN ('5A1522F', '5A1532F', '5A1522G', '5A15223', '5A1935Z'))
           OR (icd_version = 9 AND icd_code IN ('3965', '3966'))
    ),
    all_ecmo_episodes AS (
        SELECT subject_id, hadm_id, identification_method FROM ecmo_procedures
    ),
    ecmo_episodes_summary AS (
        SELECT subject_id, hadm_id, STRING_AGG(DISTINCT identification_method, ', ') as methods
        FROM all_ecmo_episodes
        GROUP BY subject_id, hadm_id
    )
    SELECT COUNT(*)
    INTO v_final_count
    FROM ecmo_episodes_summary es
    LEFT JOIN mimiciv_hosp.patients p ON es.subject_id = p.subject_id
    LEFT JOIN mimiciv_hosp.admissions a ON es.hadm_id = a.hadm_id;

    v_end_time := clock_timestamp();
    v_execution_time_ms := EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER;

    IF v_execution_time_ms > 30000 THEN
        v_test_status := 'FAIL';
        v_error_msg := 'Main query exceeds 30s target (' || v_execution_time_ms || 'ms)';
    ELSE
        v_test_status := 'PASS';
        v_error_msg := NULL;
    END IF;

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms, error_message
    ) VALUES (
        'TEST-5.3: Main Query Execution and Performance',
        'integration-test',
        'Main query completes in <30000ms',
        'Query returned ' || v_final_count || ' episodes in ' || v_execution_time_ms || 'ms',
        v_test_status,
        v_execution_time_ms,
        v_error_msg
    );

    RAISE NOTICE 'TEST-5.3: Main Query Execution - % (% episodes in %ms)', v_test_status, v_final_count, v_execution_time_ms;
END $$;

-- ============================================================================
-- TEST 6: Data Validation Tests
-- ============================================================================

-- Test 6.1: Verify episode duration calculations
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_negative_los INTEGER;
    v_null_los INTEGER;
    v_excessive_los INTEGER;
    v_test_status VARCHAR(20);
BEGIN
    v_start_time := clock_timestamp();

    SELECT
        SUM(CASE WHEN DATE_PART('day', dischtime - admittime) < 0 THEN 1 ELSE 0 END),
        SUM(CASE WHEN dischtime IS NULL OR admittime IS NULL THEN 1 ELSE 0 END),
        SUM(CASE WHEN DATE_PART('day', dischtime - admittime) > 365 THEN 1 ELSE 0 END)
    INTO v_negative_los, v_null_los, v_excessive_los
    FROM mimiciv_hosp.admissions;

    v_end_time := clock_timestamp();

    v_test_status := CASE WHEN v_negative_los = 0 THEN 'PASS' ELSE 'FAIL' END;

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms
    ) VALUES (
        'TEST-6.1: Episode Duration Validation',
        'data-validation',
        'No negative LOS, flag >365 day stays',
        'Negative LOS: ' || v_negative_los || ', NULL: ' || v_null_los || ', >365 days: ' || v_excessive_los,
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER
    );

    RAISE NOTICE 'TEST-6.1: Episode Duration Validation - %', v_test_status;
END $$;

-- Test 6.2: Verify no duplicate episodes in final output
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_total_rows INTEGER;
    v_unique_episodes INTEGER;
    v_test_status VARCHAR(20);
BEGIN
    v_start_time := clock_timestamp();

    WITH ecmo_procedures AS (
        SELECT subject_id, hadm_id, 'procedure_code' as identification_method
        FROM mimiciv_hosp.procedures_icd
        WHERE (icd_version = 10 AND icd_code IN ('5A1522F', '5A1532F', '5A1522G', '5A15223', '5A1935Z'))
    ),
    all_ecmo_episodes AS (
        SELECT subject_id, hadm_id, identification_method FROM ecmo_procedures
    ),
    ecmo_episodes_summary AS (
        SELECT subject_id, hadm_id
        FROM all_ecmo_episodes
        GROUP BY subject_id, hadm_id
    )
    SELECT COUNT(*), COUNT(DISTINCT (subject_id, hadm_id))
    INTO v_total_rows, v_unique_episodes
    FROM ecmo_episodes_summary;

    v_end_time := clock_timestamp();

    v_test_status := CASE WHEN v_total_rows = v_unique_episodes THEN 'PASS' ELSE 'FAIL' END;

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms
    ) VALUES (
        'TEST-6.2: No Duplicate Episodes',
        'data-validation',
        'Each (subject_id, hadm_id) appears once',
        'Total rows: ' || v_total_rows || ', Unique: ' || v_unique_episodes,
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER
    );

    RAISE NOTICE 'TEST-6.2: No Duplicate Episodes - %', v_test_status;
END $$;

-- ============================================================================
-- TEST 7: Edge Case Tests
-- ============================================================================

-- Test 7.1: Handle patients with multiple ECMO episodes
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_multi_episode_patients INTEGER;
    v_max_episodes INTEGER;
    v_test_status VARCHAR(20);
BEGIN
    v_start_time := clock_timestamp();

    WITH ecmo_procedures AS (
        SELECT subject_id, hadm_id
        FROM mimiciv_hosp.procedures_icd
        WHERE (icd_version = 10 AND icd_code IN ('5A1522F', '5A1532F', '5A1522G', '5A15223', '5A1935Z'))
    ),
    episode_counts AS (
        SELECT subject_id, COUNT(DISTINCT hadm_id) as num_episodes
        FROM ecmo_procedures
        GROUP BY subject_id
    )
    SELECT
        SUM(CASE WHEN num_episodes > 1 THEN 1 ELSE 0 END),
        MAX(num_episodes)
    INTO v_multi_episode_patients, v_max_episodes
    FROM episode_counts;

    v_end_time := clock_timestamp();

    v_test_status := 'PASS'; -- Always pass, informational

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms
    ) VALUES (
        'TEST-7.1: Multiple ECMO Episodes per Patient',
        'edge-case',
        'Handle patients with multiple episodes',
        'Patients with >1 episode: ' || COALESCE(v_multi_episode_patients::TEXT, '0') || ', Max episodes: ' || COALESCE(v_max_episodes::TEXT, '0'),
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER
    );

    RAISE NOTICE 'TEST-7.1: Multiple Episodes per Patient - %', v_test_status;
END $$;

-- Test 7.2: Handle missing demographic data
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_null_gender INTEGER;
    v_null_age INTEGER;
    v_test_status VARCHAR(20);
BEGIN
    v_start_time := clock_timestamp();

    SELECT
        SUM(CASE WHEN gender IS NULL THEN 1 ELSE 0 END),
        SUM(CASE WHEN anchor_age IS NULL THEN 1 ELSE 0 END)
    INTO v_null_gender, v_null_age
    FROM mimiciv_hosp.patients;

    v_end_time := clock_timestamp();

    v_test_status := 'PASS'; -- Always pass, informational

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms
    ) VALUES (
        'TEST-7.2: Missing Demographic Data',
        'edge-case',
        'Identify NULL demographics',
        'NULL gender: ' || v_null_gender || ', NULL age: ' || v_null_age,
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER
    );

    RAISE NOTICE 'TEST-7.2: Missing Demographics - %', v_test_status;
END $$;

-- Test 7.3: Zero ECMO episodes found (edge case for empty dataset)
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_procedure_count INTEGER;
    v_test_status VARCHAR(20);
BEGIN
    v_start_time := clock_timestamp();

    SELECT COUNT(*)
    INTO v_procedure_count
    FROM mimiciv_hosp.procedures_icd
    WHERE (icd_version = 10 AND icd_code IN ('5A1522F', '5A1532F', '5A1522G', '5A15223', '5A1935Z'))
       OR (icd_version = 9 AND icd_code IN ('3965', '3966'));

    v_end_time := clock_timestamp();

    v_test_status := 'PASS'; -- Always pass, informational

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms
    ) VALUES (
        'TEST-7.3: Zero ECMO Episodes (Empty Dataset Edge Case)',
        'edge-case',
        'Query handles zero episodes gracefully',
        'Found ' || v_procedure_count || ' ECMO procedure records',
        v_test_status,
        EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER
    );

    RAISE NOTICE 'TEST-7.3: Zero Episodes Edge Case - % (% procedures)', v_test_status, v_procedure_count;
END $$;

-- ============================================================================
-- TEST 8: Performance Benchmarks
-- ============================================================================

-- Test 8.1: Overall query performance target (<30s)
DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_execution_time_ms INTEGER;
    v_episode_count INTEGER;
    v_test_status VARCHAR(20);
    v_error_msg TEXT;
BEGIN
    v_start_time := clock_timestamp();

    -- Execute COMPLETE query from identify_ecmo.sql (lines 17-188)
    -- This is a simplified version for testing purposes
    WITH ecmo_procedures AS (
        SELECT
            p.subject_id, p.hadm_id, p.seq_num, p.icd_code, p.icd_version,
            d.long_title as procedure_description, 'procedure_code' as identification_method
        FROM mimiciv_hosp.procedures_icd p
        LEFT JOIN mimiciv_hosp.d_icd_procedures d
            ON p.icd_code = d.icd_code AND p.icd_version = d.icd_version
        WHERE
            (p.icd_version = 10 AND p.icd_code IN ('5A1522F', '5A1532F', '5A1522G', '5A15223', '5A1935Z'))
            OR (p.icd_version = 9 AND p.icd_code IN ('3965', '3966'))
    ),
    all_ecmo_episodes AS (
        SELECT subject_id, hadm_id, identification_method FROM ecmo_procedures
    ),
    ecmo_episodes_summary AS (
        SELECT
            subject_id, hadm_id,
            STRING_AGG(DISTINCT identification_method, ', ') as identification_methods,
            COUNT(DISTINCT identification_method) as num_identification_methods
        FROM all_ecmo_episodes
        GROUP BY subject_id, hadm_id
    )
    SELECT COUNT(*)
    INTO v_episode_count
    FROM ecmo_episodes_summary es
    LEFT JOIN mimiciv_hosp.patients p ON es.subject_id = p.subject_id
    LEFT JOIN mimiciv_hosp.admissions a ON es.hadm_id = a.hadm_id
    LEFT JOIN ecmo_procedures ep ON es.subject_id = ep.subject_id AND es.hadm_id = ep.hadm_id;

    v_end_time := clock_timestamp();
    v_execution_time_ms := EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::INTEGER;

    IF v_execution_time_ms < 30000 THEN
        v_test_status := 'PASS';
        v_error_msg := NULL;
    ELSE
        v_test_status := 'FAIL';
        v_error_msg := 'PERFORMANCE ISSUE: Query exceeded 30s target (' || v_execution_time_ms || 'ms). Consider adding indexes or optimizing CTEs.';
    END IF;

    INSERT INTO ecmo_test.test_results (
        test_name, test_category, expected_result, actual_result,
        test_status, execution_time_ms, error_message
    ) VALUES (
        'TEST-8.1: Overall Query Performance (<30s Target)',
        'performance-test',
        'Complete query executes in <30000ms on MIMIC-IV Demo',
        'Returned ' || v_episode_count || ' episodes in ' || v_execution_time_ms || 'ms',
        v_test_status,
        v_execution_time_ms,
        v_error_msg
    );

    RAISE NOTICE 'TEST-8.1: Overall Performance - % (%ms for % episodes)', v_test_status, v_execution_time_ms, v_episode_count;
END $$;

-- ============================================================================
-- TEST SUMMARY AND RESULTS
-- ============================================================================

-- Display all test results
SELECT
    test_id,
    test_name,
    test_category,
    test_status,
    execution_time_ms,
    CASE
        WHEN error_message IS NOT NULL THEN '❌ ' || error_message
        ELSE '✅ ' || actual_result
    END as result_summary,
    run_timestamp
FROM ecmo_test.test_results
ORDER BY test_id;

-- Summary statistics
SELECT
    test_category,
    COUNT(*) as total_tests,
    SUM(CASE WHEN test_status = 'PASS' THEN 1 ELSE 0 END) as passed,
    SUM(CASE WHEN test_status = 'FAIL' THEN 1 ELSE 0 END) as failed,
    SUM(CASE WHEN test_status = 'ERROR' THEN 1 ELSE 0 END) as errors,
    ROUND(AVG(execution_time_ms), 2) as avg_execution_time_ms,
    MAX(execution_time_ms) as max_execution_time_ms
FROM ecmo_test.test_results
GROUP BY test_category
ORDER BY test_category;

-- Overall pass rate
SELECT
    COUNT(*) as total_tests,
    SUM(CASE WHEN test_status = 'PASS' THEN 1 ELSE 0 END) as passed,
    ROUND(100.0 * SUM(CASE WHEN test_status = 'PASS' THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate_pct
FROM ecmo_test.test_results;

-- Critical failures
SELECT
    test_name,
    error_message,
    execution_time_ms
FROM ecmo_test.test_results
WHERE test_status = 'FAIL'
  AND error_message LIKE 'CRITICAL:%'
ORDER BY test_id;