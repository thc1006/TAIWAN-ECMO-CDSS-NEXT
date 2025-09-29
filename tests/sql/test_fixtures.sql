/*
MIMIC-IV ECMO Identification - Test Data Fixtures
Taiwan ECMO CDSS - Synthetic Test Data for TDD

This file creates synthetic test data for validating ECMO identification logic
WITHOUT requiring access to the full MIMIC-IV database.

Author: Taiwan ECMO CDSS QA Team
Version: 1.0
Date: 2025-09-30
*/

-- ============================================================================
-- FIXTURE SETUP: Create Test Tables
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS ecmo_test_fixtures;

-- Drop existing test tables
DROP TABLE IF EXISTS ecmo_test_fixtures.procedures_icd CASCADE;
DROP TABLE IF EXISTS ecmo_test_fixtures.d_icd_procedures CASCADE;
DROP TABLE IF EXISTS ecmo_test_fixtures.prescriptions CASCADE;
DROP TABLE IF EXISTS ecmo_test_fixtures.chartevents CASCADE;
DROP TABLE IF EXISTS ecmo_test_fixtures.d_items CASCADE;
DROP TABLE IF EXISTS ecmo_test_fixtures.noteevents CASCADE;
DROP TABLE IF EXISTS ecmo_test_fixtures.patients CASCADE;
DROP TABLE IF EXISTS ecmo_test_fixtures.admissions CASCADE;

-- Create test tables with same schema as MIMIC-IV
CREATE TABLE ecmo_test_fixtures.patients (
    subject_id INTEGER PRIMARY KEY,
    gender VARCHAR(1),
    anchor_age INTEGER
);

CREATE TABLE ecmo_test_fixtures.admissions (
    subject_id INTEGER,
    hadm_id INTEGER PRIMARY KEY,
    admittime TIMESTAMP,
    dischtime TIMESTAMP,
    deathtime TIMESTAMP,
    admission_type VARCHAR(50),
    admission_location VARCHAR(100),
    discharge_location VARCHAR(100)
);

CREATE TABLE ecmo_test_fixtures.d_icd_procedures (
    icd_code VARCHAR(10),
    icd_version INTEGER,
    long_title TEXT,
    PRIMARY KEY (icd_code, icd_version)
);

CREATE TABLE ecmo_test_fixtures.procedures_icd (
    subject_id INTEGER,
    hadm_id INTEGER,
    seq_num INTEGER,
    icd_code VARCHAR(10),
    icd_version INTEGER
);

CREATE TABLE ecmo_test_fixtures.prescriptions (
    subject_id INTEGER,
    hadm_id INTEGER,
    starttime TIMESTAMP,
    endtime TIMESTAMP,
    drug VARCHAR(255),
    dose_val_rx NUMERIC
);

CREATE TABLE ecmo_test_fixtures.d_items (
    itemid INTEGER PRIMARY KEY,
    label VARCHAR(255),
    category VARCHAR(100)
);

CREATE TABLE ecmo_test_fixtures.chartevents (
    subject_id INTEGER,
    hadm_id INTEGER,
    stay_id INTEGER,
    charttime TIMESTAMP,
    itemid INTEGER,
    value VARCHAR(255),
    valuenum NUMERIC,
    valueuom VARCHAR(50)
);

CREATE TABLE ecmo_test_fixtures.noteevents (
    subject_id INTEGER,
    hadm_id INTEGER,
    chartdate DATE,
    category VARCHAR(50),
    description VARCHAR(255),
    text TEXT
);

-- ============================================================================
-- FIXTURE DATA: Populate Test Data
-- ============================================================================

-- Test Case 1: Classic VV-ECMO for ARDS (multi-method identification)
INSERT INTO ecmo_test_fixtures.patients VALUES
(10001, 'M', 45);

INSERT INTO ecmo_test_fixtures.admissions VALUES
(10001, 20001, '2023-01-15 08:00:00', '2023-02-20 14:30:00', NULL,
 'URGENT', 'EMERGENCY ROOM', 'HOME');

INSERT INTO ecmo_test_fixtures.procedures_icd VALUES
(10001, 20001, 1, '5A1532F', 10);  -- ECMO continuous >96 hours

INSERT INTO ecmo_test_fixtures.prescriptions VALUES
(10001, 20001, '2023-01-15 10:00:00', '2023-02-15 10:00:00', 'Heparin (Porcine) in 0.45% Sodium Chloride', NULL),
(10001, 20001, '2023-01-15 10:00:00', '2023-02-15 10:00:00', 'Norepinephrine', 0.3);

INSERT INTO ecmo_test_fixtures.noteevents VALUES
(10001, 20001, '2023-01-15', 'Physician', 'Progress Note',
 'Patient placed on VV-ECMO for severe ARDS. Cannulated via right IJ and femoral veins. ECMO flow 4.5 L/min, sweep gas 4 L/min.');

-- Test Case 2: VA-ECMO for cardiogenic shock (procedure + medication + chart)
INSERT INTO ecmo_test_fixtures.patients VALUES
(10002, 'F', 62);

INSERT INTO ecmo_test_fixtures.admissions VALUES
(10002, 20002, '2023-03-10 12:30:00', '2023-03-25 09:00:00', '2023-03-24 15:45:00',
 'EMERGENCY', 'EMERGENCY ROOM', 'DIED');

INSERT INTO ecmo_test_fixtures.procedures_icd VALUES
(10002, 20002, 1, '5A1522F', 10),  -- ECMO continuous 24-96 hours
(10002, 20002, 2, '5A15223', 10);  -- Extracorporeal oxygenation, membrane

INSERT INTO ecmo_test_fixtures.prescriptions VALUES
(10002, 20002, '2023-03-10 14:00:00', '2023-03-24 14:00:00', 'Bivalirudin', NULL),
(10002, 20002, '2023-03-10 14:00:00', '2023-03-24 14:00:00', 'Epinephrine', 0.5),
(10002, 20002, '2023-03-10 14:00:00', '2023-03-24 14:00:00', 'Norepinephrine', 0.8);

INSERT INTO ecmo_test_fixtures.noteevents VALUES
(10002, 20002, '2023-03-10', 'Physician', 'Procedure Note',
 'VA-ECMO initiated for cardiogenic shock post-MI. Arterial cannula placed in femoral artery, venous cannula in femoral vein. Patient on maximal vasopressor support.');

-- Test Case 3: ECMO identified by ICD-9 code (legacy data)
INSERT INTO ecmo_test_fixtures.patients VALUES
(10003, 'M', 28);

INSERT INTO ecmo_test_fixtures.admissions VALUES
(10003, 20003, '2022-06-05 18:00:00', '2022-07-10 12:00:00', NULL,
 'URGENT', 'TRANSFER FROM HOSPITAL', 'REHAB');

INSERT INTO ecmo_test_fixtures.procedures_icd VALUES
(10003, 20003, 1, '3965', 9);  -- ICD-9: Extracorporeal membrane oxygenation

INSERT INTO ecmo_test_fixtures.prescriptions VALUES
(10003, 20003, '2022-06-05 20:00:00', '2022-07-05 20:00:00', 'Argatroban', NULL);

-- Test Case 4: ECMO identified only by chartevents (no procedure code)
INSERT INTO ecmo_test_fixtures.patients VALUES
(10004, 'F', 55);

INSERT INTO ecmo_test_fixtures.admissions VALUES
(10004, 20004, '2023-08-12 09:00:00', '2023-09-15 16:00:00', NULL,
 'ELECTIVE', 'CLINIC REFERRAL', 'HOME');

INSERT INTO ecmo_test_fixtures.d_items VALUES
(227287, 'ECMO Flow', 'Hemodynamics'),
(227288, 'ECMO Sweep Gas Flow', 'Ventilation'),
(227289, 'ECMO Circuit Pressure', 'Hemodynamics'),
(227290, 'Temperature Blood (C)', 'Temperature'),
(227291, 'Heart Rate', 'Vital Signs');

INSERT INTO ecmo_test_fixtures.chartevents VALUES
(10004, 20004, 30004, '2023-08-12 10:00:00', 227287, '4.5', 4.5, 'L/min'),
(10004, 20004, 30004, '2023-08-12 10:00:00', 227288, '3.5', 3.5, 'L/min'),
(10004, 20004, 30004, '2023-08-12 10:00:00', 227289, '150', 150, 'mmHg');

INSERT INTO ecmo_test_fixtures.prescriptions VALUES
(10004, 20004, '2023-08-12 10:00:00', '2023-09-10 10:00:00', 'Heparin (Porcine)', NULL);

-- Test Case 5: FALSE POSITIVE - Heparin without ECMO
INSERT INTO ecmo_test_fixtures.patients VALUES
(10005, 'M', 70);

INSERT INTO ecmo_test_fixtures.admissions VALUES
(10005, 20005, '2023-04-01 11:00:00', '2023-04-10 13:00:00', NULL,
 'URGENT', 'EMERGENCY ROOM', 'HOME');

INSERT INTO ecmo_test_fixtures.prescriptions VALUES
(10005, 20005, '2023-04-01 12:00:00', '2023-04-08 12:00:00', 'Heparin (Porcine)', NULL);  -- DVT prophylaxis, NOT ECMO

-- NOTE: No procedure code, no chartevents, no clinical notes mentioning ECMO
-- This should be identified by medication method ONLY

-- Test Case 6: Multiple ECMO episodes for same patient
INSERT INTO ecmo_test_fixtures.patients VALUES
(10006, 'F', 38);

INSERT INTO ecmo_test_fixtures.admissions VALUES
(10006, 20006, '2023-02-01 14:00:00', '2023-03-05 10:00:00', NULL,
 'EMERGENCY', 'EMERGENCY ROOM', 'HOME'),
(10006, 20007, '2023-11-15 08:00:00', '2023-12-20 15:00:00', NULL,
 'URGENT', 'EMERGENCY ROOM', 'REHAB');

INSERT INTO ecmo_test_fixtures.procedures_icd VALUES
(10006, 20006, 1, '5A1532F', 10),  -- First ECMO episode
(10006, 20007, 1, '5A1522F', 10);  -- Second ECMO episode

INSERT INTO ecmo_test_fixtures.prescriptions VALUES
(10006, 20006, '2023-02-01 16:00:00', '2023-03-01 16:00:00', 'Heparin (Porcine)', NULL),
(10006, 20007, '2023-11-15 10:00:00', '2023-12-15 10:00:00', 'Bivalirudin', NULL);

-- Test Case 7: ECMO decannulation mentioned in notes
INSERT INTO ecmo_test_fixtures.patients VALUES
(10007, 'M', 52);

INSERT INTO ecmo_test_fixtures.admissions VALUES
(10007, 20008, '2023-05-20 07:00:00', '2023-06-30 11:00:00', NULL,
 'EMERGENCY', 'TRANSFER FROM HOSPITAL', 'HOME');

INSERT INTO ecmo_test_fixtures.noteevents VALUES
(10007, 20008, '2023-06-10', 'Physician', 'Progress Note',
 'Patient successfully weaned from ECMO after 15 days. Decannulation performed at bedside without complications. Transitioned to conventional mechanical ventilation.');

INSERT INTO ecmo_test_fixtures.prescriptions VALUES
(10007, 20008, '2023-05-20 09:00:00', '2023-06-10 09:00:00', 'Heparin (Porcine)', NULL);

-- Test Case 8: Edge case - Missing demographic data
INSERT INTO ecmo_test_fixtures.patients VALUES
(10008, NULL, NULL);  -- Missing gender and age

INSERT INTO ecmo_test_fixtures.admissions VALUES
(10008, 20009, '2023-07-01 10:00:00', '2023-07-25 14:00:00', NULL,
 'URGENT', 'EMERGENCY ROOM', 'HOME');

INSERT INTO ecmo_test_fixtures.procedures_icd VALUES
(10008, 20009, 1, '5A1522F', 10);

-- Test Case 9: Edge case - Overlapping ECMO indicators
INSERT INTO ecmo_test_fixtures.patients VALUES
(10009, 'M', 41);

INSERT INTO ecmo_test_fixtures.admissions VALUES
(10009, 20010, '2023-09-01 13:00:00', '2023-10-05 09:00:00', NULL,
 'EMERGENCY', 'EMERGENCY ROOM', 'REHAB');

INSERT INTO ecmo_test_fixtures.procedures_icd VALUES
(10009, 20010, 1, '5A1532F', 10),
(10009, 20010, 2, '5A1522F', 10),
(10009, 20010, 3, '5A1522G', 10);  -- Multiple overlapping ECMO codes

INSERT INTO ecmo_test_fixtures.prescriptions VALUES
(10009, 20010, '2023-09-01 15:00:00', '2023-10-01 15:00:00', 'Heparin (Porcine)', NULL),
(10009, 20010, '2023-09-01 15:00:00', '2023-10-01 15:00:00', 'Bivalirudin', NULL);  -- Switched anticoagulants

INSERT INTO ecmo_test_fixtures.chartevents VALUES
(10009, 20010, 30009, '2023-09-01 14:00:00', 227287, '5.0', 5.0, 'L/min'),
(10009, 20010, 30009, '2023-09-01 14:00:00', 227288, '4.0', 4.0, 'L/min');

INSERT INTO ecmo_test_fixtures.noteevents VALUES
(10009, 20010, '2023-09-01', 'Physician', 'Procedure Note',
 'Patient on VV-ECMO with excellent gas exchange. Multiple configuration changes throughout ICU stay.');

-- Test Case 10: Edge case - Very long LOS (>365 days)
INSERT INTO ecmo_test_fixtures.patients VALUES
(10010, 'F', 33);

INSERT INTO ecmo_test_fixtures.admissions VALUES
(10010, 20011, '2022-01-01 08:00:00', '2023-03-01 10:00:00', NULL,
 'EMERGENCY', 'EMERGENCY ROOM', 'LONG TERM CARE');  -- 424 days

INSERT INTO ecmo_test_fixtures.procedures_icd VALUES
(10010, 20011, 1, '5A1532F', 10);

-- ============================================================================
-- FIXTURE VALIDATION: Expected Results
-- ============================================================================

-- Expected episode counts by identification method
CREATE TABLE ecmo_test_fixtures.expected_results (
    test_case VARCHAR(100),
    subject_id INTEGER,
    hadm_id INTEGER,
    expected_identification_methods TEXT,
    expected_num_methods INTEGER,
    expected_probable_ecmo_type VARCHAR(20),
    notes TEXT
);

INSERT INTO ecmo_test_fixtures.expected_results VALUES
('TC1: Classic VV-ECMO', 10001, 20001, 'procedure_code, ecmo_medication, clinical_notes', 3, 'VV_likely', 'Multi-method identification'),
('TC2: VA-ECMO fatal', 10002, 20002, 'procedure_code, ecmo_medication, clinical_notes', 3, 'VA_likely', 'Died during admission'),
('TC3: ICD-9 code', 10003, 20003, 'procedure_code, ecmo_medication', 2, 'unknown', 'Legacy ICD-9 code'),
('TC4: Chart-only ECMO', 10004, 20004, 'chart_events, ecmo_medication', 2, 'unknown', 'No procedure code recorded'),
('TC5: FALSE POSITIVE', 10005, 20005, 'ecmo_medication', 1, 'unknown', 'Heparin for DVT prophylaxis, NOT ECMO'),
('TC6a: First episode', 10006, 20006, 'procedure_code, ecmo_medication', 2, 'unknown', 'Patient with 2 separate episodes'),
('TC6b: Second episode', 10006, 20007, 'procedure_code, ecmo_medication', 2, 'unknown', 'Patient with 2 separate episodes'),
('TC7: Decannulation note', 10007, 20008, 'clinical_notes, ecmo_medication', 2, 'unknown', 'ECMO weaning mentioned'),
('TC8: Missing demographics', 10008, 20009, 'procedure_code', 1, 'unknown', 'NULL gender and age'),
('TC9: Overlapping indicators', 10009, 20010, 'procedure_code, ecmo_medication, chart_events, clinical_notes', 4, 'unknown', 'All 4 identification methods'),
('TC10: Very long LOS', 10010, 20011, 'procedure_code', 1, 'unknown', 'LOS >365 days (424 days)');

-- Summary of expected results
SELECT
    COUNT(*) as total_test_cases,
    SUM(expected_num_methods) as total_identification_events,
    COUNT(DISTINCT subject_id) as unique_patients,
    COUNT(DISTINCT hadm_id) as unique_episodes,
    SUM(CASE WHEN expected_num_methods >= 3 THEN 1 ELSE 0 END) as high_confidence_cases
FROM ecmo_test_fixtures.expected_results;

-- Display expected results
SELECT * FROM ecmo_test_fixtures.expected_results ORDER BY subject_id, hadm_id;