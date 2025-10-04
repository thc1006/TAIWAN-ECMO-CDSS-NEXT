-- =====================================================================
-- MIMIC-IV ECMO Feature Extraction for ML Models
-- =====================================================================
-- Purpose: Extract comprehensive features for ECMO outcome prediction
-- Schema: MIMIC-IV 3.1 (mimiciv_icu, mimiciv_hosp)
-- Output: Patient-level features aligned with ELSO data dictionary
-- Usage: Run after identify_ecmo.sql to get ECMO episodes
-- ELSO Alignment: All sections of data_dictionary.yaml
-- =====================================================================

-- =====================================================================
-- Step 1: Get identified ECMO episodes (from identify_ecmo.sql)
-- =====================================================================
WITH ecmo_episodes_base AS (
  -- This assumes you've created the materialized view from identify_ecmo.sql
  -- Otherwise, you would need to include the entire query from that file here
  SELECT * FROM ecmo_episodes_identified
),

-- =====================================================================
-- Step 2: Extract Patient Demographics (ELSO: patient section)
-- =====================================================================
patient_demographics AS (
  SELECT
    e.subject_id,
    e.hadm_id,
    e.episode_num,
    -- Age at ECMO initiation
    CASE
      WHEN p.anchor_age >= 89 THEN 90  -- De-identified as 90+
      ELSE p.anchor_age
    END AS age_years,
    -- ELSO age category
    CASE
      WHEN p.anchor_age < 1 THEN 'neonate'
      WHEN p.anchor_age < 18 THEN 'pediatric'
      ELSE 'adult'
    END AS age_group,
    p.gender AS sex,
    -- Race/ethnicity (limited in MIMIC-IV)
    a.race,
    -- Weight and height (from first ICU stay measurement)
    (SELECT valuenum
     FROM mimiciv_icu.chartevents ce
     WHERE ce.subject_id = e.subject_id
       AND ce.stay_id = e.stay_id
       AND ce.itemid IN (
         SELECT itemid FROM mimiciv_icu.d_items
         WHERE LOWER(label) LIKE '%weight%' AND LOWER(label) LIKE '%admission%'
       )
     ORDER BY ce.charttime LIMIT 1
    ) AS weight_kg,
    (SELECT valuenum
     FROM mimiciv_icu.chartevents ce
     WHERE ce.subject_id = e.subject_id
       AND ce.stay_id = e.stay_id
       AND ce.itemid IN (
         SELECT itemid FROM mimiciv_icu.d_items
         WHERE LOWER(label) LIKE '%height%'
       )
     ORDER BY ce.charttime LIMIT 1
    ) AS height_cm
  FROM ecmo_episodes_base e
  INNER JOIN mimiciv_hosp.patients p ON e.subject_id = p.subject_id
  INNER JOIN mimiciv_hosp.admissions a ON e.subject_id = a.subject_id AND e.hadm_id = a.hadm_id
),

-- Calculate BMI and BSA
patient_anthropometrics AS (
  SELECT
    *,
    -- BMI calculation
    CASE
      WHEN weight_kg IS NOT NULL AND height_cm IS NOT NULL AND height_cm > 0
      THEN ROUND(weight_kg / POWER(height_cm / 100.0, 2), 2)
      ELSE NULL
    END AS bmi,
    -- BSA using Mosteller formula: SQRT(height_cm * weight_kg / 3600)
    CASE
      WHEN weight_kg IS NOT NULL AND height_cm IS NOT NULL
      THEN ROUND(SQRT(height_cm * weight_kg / 3600.0), 2)
      ELSE NULL
    END AS bsa_m2
  FROM patient_demographics
),

-- =====================================================================
-- Step 3: Extract Primary Diagnoses (ELSO: pre_ecmo section)
-- =====================================================================
primary_diagnoses AS (
  SELECT
    e.subject_id,
    e.hadm_id,
    e.episode_num,
    d.icd_code AS primary_icd10,
    di.long_title AS primary_diagnosis_desc,
    -- Categorize by ELSO diagnosis categories
    CASE
      WHEN d.icd_code IN ('I46.9', 'I46.2', 'I46.8', 'R57.0') THEN 'ecpr'
      WHEN d.icd_code LIKE 'I%' OR d.icd_code IN ('R57.0') THEN 'cardiac'
      WHEN d.icd_code LIKE 'J%' THEN 'respiratory'
      WHEN d.icd_code IN ('R65.21', 'A41.9') THEN 'septic_shock'
      ELSE 'other'
    END AS diagnosis_category
  FROM ecmo_episodes_base e
  INNER JOIN mimiciv_hosp.diagnoses_icd d
    ON e.subject_id = d.subject_id AND e.hadm_id = d.hadm_id
  INNER JOIN mimiciv_hosp.d_icd_diagnoses di
    ON d.icd_code = di.icd_code AND d.icd_version = di.icd_version
  WHERE d.seq_num = 1  -- Primary diagnosis only
    AND d.icd_version = 10
),

-- =====================================================================
-- Step 4: Extract Pre-ECMO Severity Scores (ELSO: pre_ecmo section)
-- =====================================================================
-- SOFA score (if available in MIMIC-IV)
sofa_scores AS (
  SELECT
    e.subject_id,
    e.hadm_id,
    e.episode_num,
    -- Get SOFA score closest to but before ECMO start
    (SELECT valuenum
     FROM mimiciv_icu.chartevents ce
     WHERE ce.subject_id = e.subject_id
       AND ce.stay_id = e.stay_id
       AND ce.charttime <= e.ecmo_start_time
       AND ce.charttime >= e.ecmo_start_time - INTERVAL '24 hours'
       AND ce.itemid IN (
         SELECT itemid FROM mimiciv_icu.d_items WHERE LOWER(label) LIKE '%sofa%'
       )
     ORDER BY ABS(EXTRACT(EPOCH FROM (ce.charttime - e.ecmo_start_time)))
     LIMIT 1
    ) AS sofa_score
  FROM ecmo_episodes_base e
),

-- =====================================================================
-- Step 5: Extract Pre-ECMO Labs (within 24h before ECMO)
-- =====================================================================
pre_ecmo_labs AS (
  SELECT
    e.subject_id,
    e.hadm_id,
    e.episode_num,
    -- Arterial Blood Gas
    MAX(CASE WHEN di.label = 'pH' THEN le.valuenum END) AS ph_pre_ecmo,
    MAX(CASE WHEN di.label LIKE 'PaO2%' THEN le.valuenum END) AS pao2_pre_ecmo,
    MAX(CASE WHEN di.label LIKE 'PaCO2%' THEN le.valuenum END) AS paco2_pre_ecmo,
    MAX(CASE WHEN di.label LIKE '%Lactate%' THEN le.valuenum END) AS lactate_pre_ecmo,
    MAX(CASE WHEN di.label LIKE 'Base Excess%' THEN le.valuenum END) AS base_excess_pre_ecmo,
    -- Chemistry
    MAX(CASE WHEN di.label LIKE '%Sodium%' THEN le.valuenum END) AS sodium_mmol_l,
    MAX(CASE WHEN di.label LIKE '%Potassium%' THEN le.valuenum END) AS potassium_mmol_l,
    MAX(CASE WHEN di.label LIKE '%Creatinine%' THEN le.valuenum END) AS creatinine_mg_dl,
    MAX(CASE WHEN di.label LIKE '%Urea Nitrogen%' OR di.label LIKE '%BUN%' THEN le.valuenum END) AS bun_mg_dl,
    MAX(CASE WHEN di.label LIKE '%Bilirubin%Total%' THEN le.valuenum END) AS bilirubin_mg_dl,
    MAX(CASE WHEN di.label LIKE '%Glucose%' THEN le.valuenum END) AS glucose_mg_dl,
    -- Hematology
    MAX(CASE WHEN di.label LIKE '%Hemoglobin%' THEN le.valuenum END) AS hemoglobin_g_dl,
    MAX(CASE WHEN di.label LIKE '%Hematocrit%' THEN le.valuenum END) AS hematocrit_pct,
    MAX(CASE WHEN di.label LIKE '%Platelet%' THEN le.valuenum END) AS platelets_k_ul,
    MAX(CASE WHEN di.label LIKE '%WBC%' OR di.label LIKE '%White Blood%' THEN le.valuenum END) AS wbc_k_ul,
    -- Coagulation
    MAX(CASE WHEN di.label LIKE '%PT%' AND di.label NOT LIKE '%PTT%' THEN le.valuenum END) AS pt_sec,
    MAX(CASE WHEN di.label LIKE '%PTT%' OR di.label LIKE '%aPTT%' THEN le.valuenum END) AS ptt_sec,
    MAX(CASE WHEN di.label LIKE '%INR%' THEN le.valuenum END) AS inr,
    MAX(CASE WHEN di.label LIKE '%Fibrinogen%' THEN le.valuenum END) AS fibrinogen_mg_dl
  FROM ecmo_episodes_base e
  INNER JOIN mimiciv_hosp.labevents le
    ON e.subject_id = le.subject_id
    AND e.hadm_id = le.hadm_id
    AND le.charttime <= e.ecmo_start_time
    AND le.charttime >= e.ecmo_start_time - INTERVAL '24 hours'
  INNER JOIN mimiciv_hosp.d_labitems di ON le.itemid = di.itemid
  WHERE le.valuenum IS NOT NULL
  GROUP BY e.subject_id, e.hadm_id, e.episode_num
),

-- Calculate PF ratio and oxygenation index
pre_ecmo_respiratory AS (
  SELECT
    l.*,
    -- PF ratio (PaO2/FiO2)
    CASE
      WHEN l.pao2_pre_ecmo IS NOT NULL AND v.fio2_pre_ecmo IS NOT NULL AND v.fio2_pre_ecmo > 0
      THEN ROUND(l.pao2_pre_ecmo / v.fio2_pre_ecmo, 2)
      ELSE NULL
    END AS pf_ratio,
    -- Oxygenation Index = (MAP × FiO2 × 100) / PaO2
    CASE
      WHEN l.pao2_pre_ecmo IS NOT NULL AND v.fio2_pre_ecmo IS NOT NULL AND v.map_pre_ecmo IS NOT NULL
           AND l.pao2_pre_ecmo > 0
      THEN ROUND((v.map_pre_ecmo * v.fio2_pre_ecmo * 100.0) / l.pao2_pre_ecmo, 2)
      ELSE NULL
    END AS oxy_index,
    v.fio2_pre_ecmo,
    v.peep_pre_ecmo,
    v.map_pre_ecmo
  FROM pre_ecmo_labs l
  LEFT JOIN LATERAL (
    SELECT
      e.subject_id,
      e.hadm_id,
      MAX(CASE WHEN di.label LIKE '%FiO2%' THEN ce.valuenum END) AS fio2_pre_ecmo,
      MAX(CASE WHEN di.label LIKE '%PEEP%' THEN ce.valuenum END) AS peep_pre_ecmo,
      MAX(CASE WHEN di.label LIKE 'Arterial Blood Pressure mean%' OR di.label LIKE '%MAP%' THEN ce.valuenum END) AS map_pre_ecmo
    FROM ecmo_episodes_base e
    INNER JOIN mimiciv_icu.chartevents ce
      ON e.subject_id = ce.subject_id
      AND ce.stay_id = e.stay_id
      AND ce.charttime <= e.ecmo_start_time
      AND ce.charttime >= e.ecmo_start_time - INTERVAL '24 hours'
    INNER JOIN mimiciv_icu.d_items di ON ce.itemid = di.itemid
    WHERE ce.valuenum IS NOT NULL
      AND (l.subject_id = e.subject_id AND l.hadm_id = e.hadm_id)
    GROUP BY e.subject_id, e.hadm_id
  ) v ON l.subject_id = v.subject_id AND l.hadm_id = v.hadm_id
),

-- =====================================================================
-- Step 6: Extract Pre-ECMO Vital Signs (closest to ECMO start)
-- =====================================================================
pre_ecmo_vitals AS (
  SELECT DISTINCT ON (e.subject_id, e.hadm_id, e.episode_num)
    e.subject_id,
    e.hadm_id,
    e.episode_num,
    ce.charttime AS vitals_time,
    MAX(CASE WHEN di.label LIKE '%Heart Rate%' THEN ce.valuenum END) AS hr_bpm,
    MAX(CASE WHEN di.label LIKE '%Arterial%Systolic%' OR di.label LIKE '%NBP Systolic%' THEN ce.valuenum END) AS sbp_mmhg,
    MAX(CASE WHEN di.label LIKE '%Arterial%Diastolic%' OR di.label LIKE '%NBP Diastolic%' THEN ce.valuenum END) AS dbp_mmhg,
    MAX(CASE WHEN di.label LIKE '%Arterial%Mean%' OR di.label LIKE '%MAP%' THEN ce.valuenum END) AS map_mmhg,
    MAX(CASE WHEN di.label LIKE '%Respiratory Rate%' THEN ce.valuenum END) AS resp_rate,
    MAX(CASE WHEN di.label LIKE '%SpO2%' OR di.label LIKE '%O2 saturation%' THEN ce.valuenum END) AS spo2_pct,
    MAX(CASE WHEN di.label LIKE '%Temperature%' THEN ce.valuenum END) AS temp_c
  FROM ecmo_episodes_base e
  INNER JOIN mimiciv_icu.chartevents ce
    ON e.subject_id = ce.subject_id
    AND ce.stay_id = e.stay_id
    AND ce.charttime <= e.ecmo_start_time
    AND ce.charttime >= e.ecmo_start_time - INTERVAL '6 hours'
  INNER JOIN mimiciv_icu.d_items di ON ce.itemid = di.itemid
  WHERE ce.valuenum IS NOT NULL
  GROUP BY e.subject_id, e.hadm_id, e.episode_num, ce.charttime
  ORDER BY e.subject_id, e.hadm_id, e.episode_num, ABS(EXTRACT(EPOCH FROM (ce.charttime - e.ecmo_start_time)))
),

-- =====================================================================
-- Step 7: Extract Pre-ECMO Mechanical Ventilation Duration
-- =====================================================================
pre_ecmo_vent AS (
  SELECT
    e.subject_id,
    e.hadm_id,
    e.episode_num,
    MIN(ce.charttime) AS first_vent_time,
    ROUND(EXTRACT(EPOCH FROM (e.ecmo_start_time - MIN(ce.charttime))) / 3600.0, 2) AS mechanical_vent_hours
  FROM ecmo_episodes_base e
  INNER JOIN mimiciv_icu.chartevents ce
    ON e.subject_id = ce.subject_id
    AND ce.stay_id = e.stay_id
    AND ce.charttime < e.ecmo_start_time
  INNER JOIN mimiciv_icu.d_items di ON ce.itemid = di.itemid
  WHERE di.label LIKE '%Ventilator Mode%'
    OR di.label LIKE '%Vent Mode%'
  GROUP BY e.subject_id, e.hadm_id, e.episode_num, e.ecmo_start_time
),

-- =====================================================================
-- Step 8: Extract ECMO Support Parameters (during ECMO run)
-- =====================================================================
ecmo_support_params AS (
  SELECT
    e.subject_id,
    e.hadm_id,
    e.episode_num,
    -- Flow parameters
    ROUND(AVG(CASE WHEN di.label LIKE '%ECMO%Flow%' OR di.label LIKE '%Circuit%Flow%' THEN ce.valuenum END), 2) AS avg_flow_l_min,
    ROUND(MAX(CASE WHEN di.label LIKE '%ECMO%Flow%' OR di.label LIKE '%Circuit%Flow%' THEN ce.valuenum END), 2) AS max_flow_l_min,
    ROUND(MIN(CASE WHEN di.label LIKE '%ECMO%Flow%' OR di.label LIKE '%Circuit%Flow%' THEN ce.valuenum END), 2) AS min_flow_l_min,
    -- Pump speed
    ROUND(AVG(CASE WHEN di.label LIKE '%ECMO%RPM%' OR di.label LIKE '%Pump%RPM%' THEN ce.valuenum END), 2) AS avg_pump_rpm,
    -- Sweep gas
    ROUND(AVG(CASE WHEN di.label LIKE '%Sweep%Gas%' THEN ce.valuenum END), 2) AS avg_sweep_gas_l_min,
    -- FiO2
    ROUND(AVG(CASE WHEN di.label LIKE '%ECMO%FiO2%' THEN ce.valuenum END), 3) AS avg_ecmo_fio2,
    -- Temperature
    ROUND(AVG(CASE WHEN di.label LIKE '%ECMO%Temp%' OR di.label LIKE '%Circuit%Temp%' THEN ce.valuenum END), 2) AS avg_temp_c,
    -- Count of parameter measurements
    COUNT(DISTINCT ce.charttime) AS num_ecmo_measurements
  FROM ecmo_episodes_base e
  INNER JOIN mimiciv_icu.chartevents ce
    ON e.subject_id = ce.subject_id
    AND ce.stay_id = e.stay_id
    AND ce.charttime BETWEEN e.ecmo_start_time AND e.ecmo_end_time
  INNER JOIN mimiciv_icu.d_items di ON ce.itemid = di.itemid
  WHERE ce.valuenum IS NOT NULL
    AND (di.label LIKE '%ECMO%' OR di.label LIKE '%Circuit%' OR di.label LIKE '%Sweep%')
  GROUP BY e.subject_id, e.hadm_id, e.episode_num
),

-- Calculate flow index (flow/BSA)
ecmo_support_indexed AS (
  SELECT
    s.*,
    CASE
      WHEN s.avg_flow_l_min IS NOT NULL AND pa.bsa_m2 IS NOT NULL AND pa.bsa_m2 > 0
      THEN ROUND(s.avg_flow_l_min / pa.bsa_m2, 2)
      ELSE NULL
    END AS avg_flow_index
  FROM ecmo_support_params s
  LEFT JOIN patient_anthropometrics pa USING (subject_id, hadm_id, episode_num)
),

-- =====================================================================
-- Step 9: Extract ECMO Complications
-- =====================================================================
ecmo_complications AS (
  SELECT
    e.subject_id,
    e.hadm_id,
    e.episode_num,
    -- Hemorrhagic complications
    MAX(CASE WHEN d.icd_code IN ('I62.9', 'I61.9') THEN 1 ELSE 0 END) AS cns_hemorrhage,
    MAX(CASE WHEN d.icd_code = 'R04.89' THEN 1 ELSE 0 END) AS pulmonary_hemorrhage,
    MAX(CASE WHEN d.icd_code = 'K92.2' THEN 1 ELSE 0 END) AS gi_hemorrhage,
    MAX(CASE WHEN d.icd_code IN ('I31.4') THEN 1 ELSE 0 END) AS cardiac_tamponade,
    MAX(CASE WHEN d.icd_code = 'J94.2' THEN 1 ELSE 0 END) AS hemothorax,
    -- Neurological complications
    MAX(CASE WHEN d.icd_code = 'I63.9' THEN 1 ELSE 0 END) AS ischemic_stroke,
    MAX(CASE WHEN d.icd_code IN ('R56.9', 'G40.9') THEN 1 ELSE 0 END) AS seizures,
    MAX(CASE WHEN d.icd_code = 'G93.82' THEN 1 ELSE 0 END) AS brain_death,
    -- Cardiovascular complications
    MAX(CASE WHEN d.icd_code = 'I21.4' THEN 1 ELSE 0 END) AS myocardial_infarction,
    MAX(CASE WHEN d.icd_code IN ('I49.9', 'I47.2', 'I49.01') THEN 1 ELSE 0 END) AS arrhythmia,
    MAX(CASE WHEN d.icd_code IN ('I74.3', 'I74.2') THEN 1 ELSE 0 END) AS limb_ischemia,
    MAX(CASE WHEN d.icd_code LIKE 'T79.A%' THEN 1 ELSE 0 END) AS compartment_syndrome,
    -- Renal complications
    MAX(CASE WHEN d.icd_code = 'N17.9' THEN 1 ELSE 0 END) AS acute_kidney_injury,
    -- Infectious complications
    MAX(CASE WHEN d.icd_code IN ('A41.9', 'R65.21') THEN 1 ELSE 0 END) AS sepsis,
    MAX(CASE WHEN d.icd_code = 'J18.9' THEN 1 ELSE 0 END) AS pneumonia,
    -- Metabolic complications
    MAX(CASE WHEN d.icd_code = 'D65' THEN 1 ELSE 0 END) AS dic,
    MAX(CASE WHEN d.icd_code = 'D75.82' THEN 1 ELSE 0 END) AS hit
  FROM ecmo_episodes_base e
  LEFT JOIN mimiciv_hosp.diagnoses_icd d
    ON e.subject_id = d.subject_id
    AND e.hadm_id = d.hadm_id
  WHERE d.icd_version = 10
  GROUP BY e.subject_id, e.hadm_id, e.episode_num
),

-- =====================================================================
-- Step 10: Extract Interventions During ECMO
-- =====================================================================
ecmo_interventions AS (
  SELECT
    e.subject_id,
    e.hadm_id,
    e.episode_num,
    -- Transfusions (from procedures)
    MAX(CASE WHEN p.icd_code = '30233N1' THEN 1 ELSE 0 END) AS prbc_transfusion,
    MAX(CASE WHEN p.icd_code = '30233R1' THEN 1 ELSE 0 END) AS platelet_transfusion,
    MAX(CASE WHEN p.icd_code = '30233L1' THEN 1 ELSE 0 END) AS ffp_transfusion,
    -- CRRT
    MAX(CASE WHEN p.icd_code IN ('5A1D60Z', '5A1D70Z') THEN 1 ELSE 0 END) AS renal_replacement_therapy,
    -- Surgical procedures
    MAX(CASE WHEN p.icd_code LIKE '0JB%' THEN 1 ELSE 0 END) AS fasciotomy,
    MAX(CASE WHEN p.icd_code LIKE '0Y6%' THEN 1 ELSE 0 END) AS amputation,
    MAX(CASE WHEN p.icd_code = '0B113F4' THEN 1 ELSE 0 END) AS tracheostomy
  FROM ecmo_episodes_base e
  LEFT JOIN mimiciv_hosp.procedures_icd p
    ON e.subject_id = p.subject_id
    AND e.hadm_id = p.hadm_id
  WHERE p.icd_version = 10
  GROUP BY e.subject_id, e.hadm_id, e.episode_num
),

-- =====================================================================
-- Step 11: Extract Outcomes
-- =====================================================================
outcomes AS (
  SELECT
    e.subject_id,
    e.hadm_id,
    e.episode_num,
    -- Primary outcome: survival to hospital discharge
    CASE WHEN a.deathtime IS NULL THEN 1 ELSE 0 END AS survival_to_discharge,
    -- Death during ECMO
    CASE
      WHEN a.deathtime BETWEEN e.ecmo_start_time AND e.ecmo_end_time THEN 1
      ELSE 0
    END AS death_on_ecmo,
    -- Death within 24h post-ECMO
    CASE
      WHEN a.deathtime BETWEEN e.ecmo_end_time AND e.ecmo_end_time + INTERVAL '24 hours' THEN 1
      ELSE 0
    END AS death_24h_post_ecmo,
    -- Length of stay
    ROUND(EXTRACT(EPOCH FROM (i.outtime - i.intime)) / 86400.0, 2) AS icu_los_days,
    ROUND(EXTRACT(EPOCH FROM (a.dischtime - a.admittime)) / 86400.0, 2) AS hosp_los_days,
    -- Discharge disposition
    a.discharge_location,
    a.hospital_expire_flag
  FROM ecmo_episodes_base e
  INNER JOIN mimiciv_hosp.admissions a
    ON e.subject_id = a.subject_id AND e.hadm_id = a.hadm_id
  LEFT JOIN mimiciv_icu.icustays i
    ON e.subject_id = i.subject_id AND e.hadm_id = i.hadm_id AND e.stay_id = i.stay_id
)

-- =====================================================================
-- Final Output: Complete ECMO Feature Set for ML
-- =====================================================================
SELECT
  -- Identifiers
  e.subject_id,
  e.hadm_id,
  e.stay_id,
  e.episode_num,
  -- ECMO episode details
  e.ecmo_start_time,
  e.ecmo_end_time,
  e.ecmo_duration_hours,
  e.ecmo_mode,
  -- Patient demographics (ELSO: patient section)
  pd.age_years,
  pd.age_group,
  pd.sex,
  pd.race,
  pd.weight_kg,
  pd.height_cm,
  pa.bmi,
  pa.bsa_m2,
  -- Primary diagnosis (ELSO: pre_ecmo section)
  dx.primary_icd10,
  dx.primary_diagnosis_desc,
  dx.diagnosis_category,
  -- Pre-ECMO severity
  ss.sofa_score,
  -- Pre-ECMO labs and respiratory metrics
  pl.ph_pre_ecmo,
  pl.pao2_pre_ecmo,
  pl.paco2_pre_ecmo,
  pl.lactate_pre_ecmo,
  pl.base_excess_pre_ecmo,
  pr.pf_ratio,
  pr.oxy_index,
  pr.fio2_pre_ecmo,
  pr.peep_pre_ecmo,
  -- Pre-ECMO chemistry
  pl.sodium_mmol_l,
  pl.potassium_mmol_l,
  pl.creatinine_mg_dl,
  pl.bun_mg_dl,
  pl.bilirubin_mg_dl,
  pl.glucose_mg_dl,
  -- Pre-ECMO hematology
  pl.hemoglobin_g_dl,
  pl.hematocrit_pct,
  pl.platelets_k_ul,
  pl.wbc_k_ul,
  -- Pre-ECMO coagulation
  pl.pt_sec,
  pl.ptt_sec,
  pl.inr,
  pl.fibrinogen_mg_dl,
  -- Pre-ECMO vitals
  pv.hr_bpm AS hr_pre_ecmo,
  pv.sbp_mmhg AS sbp_pre_ecmo,
  pv.dbp_mmhg AS dbp_pre_ecmo,
  pv.map_mmhg AS map_pre_ecmo,
  pv.resp_rate AS resp_rate_pre_ecmo,
  pv.spo2_pct AS spo2_pre_ecmo,
  pv.temp_c AS temp_pre_ecmo,
  -- Pre-ECMO mechanical ventilation
  pvent.mechanical_vent_hours,
  -- ECMO support parameters (ELSO: support_params section)
  esp.avg_flow_l_min,
  esp.min_flow_l_min,
  esp.max_flow_l_min,
  esi.avg_flow_index,
  esp.avg_pump_rpm,
  esp.avg_sweep_gas_l_min,
  esp.avg_ecmo_fio2,
  esp.avg_temp_c,
  esp.num_ecmo_measurements,
  -- Complications (ELSO: complications section)
  comp.cns_hemorrhage,
  comp.pulmonary_hemorrhage,
  comp.gi_hemorrhage,
  comp.cardiac_tamponade,
  comp.hemothorax,
  comp.ischemic_stroke,
  comp.seizures,
  comp.brain_death,
  comp.myocardial_infarction,
  comp.arrhythmia,
  comp.limb_ischemia,
  comp.compartment_syndrome,
  comp.acute_kidney_injury,
  comp.sepsis,
  comp.pneumonia,
  comp.dic,
  comp.hit,
  -- Interventions (ELSO: interventions section)
  int.prbc_transfusion,
  int.platelet_transfusion,
  int.ffp_transfusion,
  int.renal_replacement_therapy,
  int.fasciotomy,
  int.amputation,
  int.tracheostomy,
  -- Outcomes (ELSO: outcomes section)
  out.survival_to_discharge,
  out.death_on_ecmo,
  out.death_24h_post_ecmo,
  out.icu_los_days,
  out.hosp_los_days,
  out.discharge_location,
  out.hospital_expire_flag
FROM ecmo_episodes_base e
LEFT JOIN patient_demographics pd USING (subject_id, hadm_id, episode_num)
LEFT JOIN patient_anthropometrics pa USING (subject_id, hadm_id, episode_num)
LEFT JOIN primary_diagnoses dx USING (subject_id, hadm_id, episode_num)
LEFT JOIN sofa_scores ss USING (subject_id, hadm_id, episode_num)
LEFT JOIN pre_ecmo_labs pl USING (subject_id, hadm_id, episode_num)
LEFT JOIN pre_ecmo_respiratory pr USING (subject_id, hadm_id, episode_num)
LEFT JOIN pre_ecmo_vitals pv USING (subject_id, hadm_id, episode_num)
LEFT JOIN pre_ecmo_vent pvent USING (subject_id, hadm_id, episode_num)
LEFT JOIN ecmo_support_params esp USING (subject_id, hadm_id, episode_num)
LEFT JOIN ecmo_support_indexed esi USING (subject_id, hadm_id, episode_num)
LEFT JOIN ecmo_complications comp USING (subject_id, hadm_id, episode_num)
LEFT JOIN ecmo_interventions int USING (subject_id, hadm_id, episode_num)
LEFT JOIN outcomes out USING (subject_id, hadm_id, episode_num)
ORDER BY e.subject_id, e.hadm_id, e.episode_num;

-- =====================================================================
-- Optional: Create materialized view for performance
-- =====================================================================
-- CREATE MATERIALIZED VIEW ecmo_features_ml AS
-- <insert the above query>
-- CREATE INDEX idx_ecmo_features_subject ON ecmo_features_ml(subject_id);
-- CREATE INDEX idx_ecmo_features_outcome ON ecmo_features_ml(survival_to_discharge);
-- CREATE INDEX idx_ecmo_features_mode ON ecmo_features_ml(ecmo_mode);
