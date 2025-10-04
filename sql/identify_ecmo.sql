-- =====================================================================
-- MIMIC-IV ECMO Episode Identification
-- =====================================================================
-- Purpose: Identify ECMO episodes with start/end times, mode, and parameters
-- Schema: MIMIC-IV 3.1 (mimiciv_icu, mimiciv_hosp)
-- Output: ECMO episodes with temporal boundaries and mode classification
-- ELSO Alignment: ecmo_episode section of data_dictionary.yaml
-- =====================================================================

-- =====================================================================
-- Step 1: Identify ECMO-related chart event items
-- =====================================================================
WITH ecmo_items AS (
  SELECT itemid, label, category
  FROM mimiciv_icu.d_items
  WHERE
    LOWER(label) ~ '(ecmo|oxygenator|circuit|sweep|cannula)'
    OR LOWER(category) ~ 'ecmo'
),

-- =====================================================================
-- Step 2: Identify ECMO from procedure events (ICD-10-PCS codes)
-- =====================================================================
ecmo_procedures AS (
  SELECT DISTINCT
    p.subject_id,
    p.hadm_id,
    p.chartdate,
    p.icd_code,
    p.icd_version,
    -- Determine ECMO mode from procedure code
    CASE
      -- ICD-10-PCS: 5A1522F = ECMO, Continuous
      WHEN p.icd_code IN ('5A1522F', '5A1522G') THEN 'ECMO'
      -- Try to infer VA vs VV from other codes
      WHEN p.icd_code LIKE '02H%' THEN 'VA' -- Cardiovascular device insertion
      WHEN p.icd_code LIKE '5A19%' THEN 'VV' -- Respiratory assistance
      ELSE 'ECMO'
    END AS mode_hint
  FROM mimiciv_hosp.procedures_icd p
  WHERE
    (p.icd_version = 10 AND p.icd_code IN ('5A1522F', '5A1522G'))
    OR LOWER((SELECT long_title FROM mimiciv_hosp.d_icd_procedures WHERE icd_code = p.icd_code LIMIT 1)) ~ 'ecmo|extracorporeal'
),

-- =====================================================================
-- Step 3: Collect all ECMO chart events with timestamps
-- =====================================================================
ecmo_chart_events AS (
  SELECT
    ce.subject_id,
    ce.hadm_id,
    ce.stay_id,
    ce.charttime,
    ce.itemid,
    ei.label,
    ei.category,
    ce.value,
    ce.valuenum,
    ce.valueuom
  FROM mimiciv_icu.chartevents ce
  INNER JOIN ecmo_items ei USING (itemid)
  WHERE
    ce.value IS NOT NULL
    -- Filter out obvious errors
    AND ce.charttime IS NOT NULL
),

-- =====================================================================
-- Step 4: Identify ECMO episodes by grouping temporal clusters
-- =====================================================================
-- First, identify all distinct patients with ECMO events
ecmo_patients AS (
  SELECT DISTINCT subject_id, hadm_id, stay_id
  FROM ecmo_chart_events
  UNION
  SELECT DISTINCT subject_id, hadm_id, NULL AS stay_id
  FROM ecmo_procedures
),

-- Create temporal windows for each patient (gap > 48 hours = new episode)
ecmo_events_ordered AS (
  SELECT
    subject_id,
    hadm_id,
    stay_id,
    charttime,
    LAG(charttime) OVER (PARTITION BY subject_id, hadm_id ORDER BY charttime) AS prev_charttime
  FROM ecmo_chart_events
),

ecmo_episodes_raw AS (
  SELECT
    subject_id,
    hadm_id,
    stay_id,
    charttime,
    -- New episode if gap > 48 hours or first event
    CASE
      WHEN prev_charttime IS NULL THEN 1
      WHEN charttime - prev_charttime > INTERVAL '48 hours' THEN 1
      ELSE 0
    END AS new_episode_flag
  FROM ecmo_events_ordered
),

ecmo_episodes_numbered AS (
  SELECT
    subject_id,
    hadm_id,
    stay_id,
    charttime,
    SUM(new_episode_flag) OVER (PARTITION BY subject_id, hadm_id ORDER BY charttime) AS episode_num
  FROM ecmo_episodes_raw
),

ecmo_episodes AS (
  SELECT
    subject_id,
    hadm_id,
    stay_id,
    episode_num,
    MIN(charttime) AS start_time,
    MAX(charttime) AS end_time,
    COUNT(*) AS num_chart_events,
    ROUND(EXTRACT(EPOCH FROM (MAX(charttime) - MIN(charttime))) / 3600.0, 2) AS duration_hours
  FROM ecmo_episodes_numbered
  GROUP BY subject_id, hadm_id, stay_id, episode_num
),

-- =====================================================================
-- Step 5: Determine ECMO mode (VA vs VV) from multiple sources
-- =====================================================================
-- Try to infer mode from diagnoses (cardiac = VA, respiratory = VV)
mode_from_diagnosis AS (
  SELECT DISTINCT
    e.subject_id,
    e.hadm_id,
    e.episode_num,
    CASE
      -- Cardiac diagnoses suggest VA ECMO
      WHEN d.icd_code IN ('I46.9', 'I46.2', 'I46.8', 'R57.0', 'I21.0', 'I21.1', 'I21.2', 'I21.3', 'I21.4', 'I21.9',
                          'I40.0', 'I40.1', 'I40.8', 'I40.9', 'I50.1', 'I50.2', 'I50.3', 'I50.4', 'I50.9')
           THEN 'VA'
      -- Respiratory diagnoses suggest VV ECMO
      WHEN d.icd_code IN ('J80', 'J12.9', 'J13', 'J14', 'J15.9', 'J18.9', 'J69.0', 'J46',
                          'I27.0', 'I27.2', 'J93.0', 'J93.1', 'U07.1')
           THEN 'VV'
      -- ECPR = VA mode
      WHEN d.icd_code IN ('I46.9', 'I46.2') AND d.seq_num = 1 THEN 'VA'
      ELSE NULL
    END AS mode_hint,
    d.seq_num
  FROM ecmo_episodes e
  INNER JOIN mimiciv_hosp.diagnoses_icd d
    ON e.subject_id = d.subject_id AND e.hadm_id = d.hadm_id
  WHERE d.icd_version = 10
),

-- Aggregate mode hints by episode
mode_inference AS (
  SELECT
    subject_id,
    hadm_id,
    episode_num,
    -- Pick the most common mode hint, prioritizing primary diagnosis
    MODE() WITHIN GROUP (ORDER BY mode_hint) FILTER (WHERE mode_hint IS NOT NULL) AS inferred_mode
  FROM mode_from_diagnosis
  GROUP BY subject_id, hadm_id, episode_num
),

-- =====================================================================
-- Step 6: Extract key ECMO parameters during each episode
-- =====================================================================
ecmo_flow_summary AS (
  SELECT
    en.subject_id,
    en.hadm_id,
    en.episode_num,
    ROUND(AVG(ce.valuenum), 2) AS avg_flow_l_min,
    ROUND(MIN(ce.valuenum), 2) AS min_flow_l_min,
    ROUND(MAX(ce.valuenum), 2) AS max_flow_l_min
  FROM ecmo_episodes_numbered en
  INNER JOIN ecmo_chart_events ce
    ON en.subject_id = ce.subject_id
    AND en.hadm_id = ce.hadm_id
    AND en.charttime = ce.charttime
  WHERE LOWER(ce.label) ~ '(flow|rpm)'
    AND ce.valuenum IS NOT NULL
    AND ce.valuenum > 0
    AND ce.valuenum < 10  -- Reasonable flow range in L/min
  GROUP BY en.subject_id, en.hadm_id, en.episode_num
),

sweep_gas_summary AS (
  SELECT
    en.subject_id,
    en.hadm_id,
    en.episode_num,
    ROUND(AVG(ce.valuenum), 2) AS avg_sweep_l_min
  FROM ecmo_episodes_numbered en
  INNER JOIN ecmo_chart_events ce
    ON en.subject_id = ce.subject_id
    AND en.hadm_id = ce.hadm_id
    AND en.charttime = ce.charttime
  WHERE LOWER(ce.label) ~ 'sweep'
    AND ce.valuenum IS NOT NULL
    AND ce.valuenum > 0
    AND ce.valuenum < 20
  GROUP BY en.subject_id, en.hadm_id, en.episode_num
)

-- =====================================================================
-- Final output: ECMO episodes with mode and parameters
-- =====================================================================
SELECT
  e.subject_id,
  e.hadm_id,
  e.stay_id,
  e.episode_num,
  e.start_time AS ecmo_start_time,
  e.end_time AS ecmo_end_time,
  e.duration_hours AS ecmo_duration_hours,
  e.num_chart_events,
  -- ECMO mode determination (VA/VV/VAV/unknown)
  COALESCE(mi.inferred_mode, 'Unknown') AS ecmo_mode,
  -- ECMO parameters summary
  f.avg_flow_l_min,
  f.min_flow_l_min,
  f.max_flow_l_min,
  s.avg_sweep_l_min,
  -- Link to patient demographics
  p.anchor_age,
  p.anchor_year,
  p.gender,
  -- Link to admission
  a.admittime,
  a.dischtime,
  a.deathtime,
  a.admission_type,
  a.admission_location,
  a.discharge_location,
  a.insurance,
  a.hospital_expire_flag,
  -- ICU details
  i.intime AS icu_intime,
  i.outtime AS icu_outtime,
  ROUND(EXTRACT(EPOCH FROM (i.outtime - i.intime)) / 3600.0, 2) AS icu_los_hours,
  -- Survival outcome
  CASE
    WHEN a.deathtime IS NOT NULL THEN 0
    ELSE 1
  END AS survived_to_discharge,
  -- ECMO initiated during ICU stay?
  CASE
    WHEN e.start_time BETWEEN i.intime AND i.outtime THEN 1
    ELSE 0
  END AS ecmo_during_icu
FROM ecmo_episodes e
LEFT JOIN mode_inference mi
  ON e.subject_id = mi.subject_id
  AND e.hadm_id = mi.hadm_id
  AND e.episode_num = mi.episode_num
LEFT JOIN ecmo_flow_summary f
  ON e.subject_id = f.subject_id
  AND e.hadm_id = f.hadm_id
  AND e.episode_num = f.episode_num
LEFT JOIN sweep_gas_summary s
  ON e.subject_id = s.subject_id
  AND e.hadm_id = s.hadm_id
  AND e.episode_num = s.episode_num
LEFT JOIN mimiciv_hosp.patients p
  ON e.subject_id = p.subject_id
LEFT JOIN mimiciv_hosp.admissions a
  ON e.subject_id = a.subject_id
  AND e.hadm_id = a.hadm_id
LEFT JOIN mimiciv_icu.icustays i
  ON e.subject_id = i.subject_id
  AND e.hadm_id = i.hadm_id
  AND e.stay_id = i.stay_id
WHERE
  -- Filter out spurious episodes (< 1 hour or very few events)
  e.duration_hours >= 1
  AND e.num_chart_events >= 5
ORDER BY e.subject_id, e.hadm_id, e.start_time;

-- =====================================================================
-- Create materialized view for performance
-- =====================================================================
-- Uncomment to create a materialized view:
-- CREATE MATERIALIZED VIEW ecmo_episodes_identified AS
-- <insert the above query>
-- CREATE INDEX idx_ecmo_episodes_subject ON ecmo_episodes_identified(subject_id);
-- CREATE INDEX idx_ecmo_episodes_hadm ON ecmo_episodes_identified(hadm_id);
