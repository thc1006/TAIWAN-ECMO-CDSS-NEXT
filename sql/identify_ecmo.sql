/*
MIMIC-IV Demo SQL: Identify ECMO Episodes
Taiwan ECMO CDSS - ECMO Episode Identification Query

This query identifies ECMO episodes from MIMIC-IV database using:
1. Procedure codes (ICD-10-PCS, CPT)  
2. Medication administration (ECMO-related drugs)
3. Chartevents (ECMO parameters)
4. Device-related documentation

Author: Taiwan ECMO CDSS Team
Version: 1.0
Date: 2024-01-01
*/

-- Main ECMO Episodes Query
WITH ecmo_procedures AS (
    -- Identify ECMO from procedure codes
    SELECT 
        p.subject_id,
        p.hadm_id,
        p.seq_num,
        p.icd_code,
        p.icd_version,
        d.long_title as procedure_description,
        'procedure_code' as identification_method
    FROM mimiciv_hosp.procedures_icd p
    LEFT JOIN mimiciv_hosp.d_icd_procedures d 
        ON p.icd_code = d.icd_code AND p.icd_version = d.icd_version
    WHERE 
        -- ICD-10-PCS ECMO codes
        (p.icd_version = 10 AND p.icd_code IN (
            '5A1522F',  -- ECMO continuous 24-96 hours
            '5A1532F',  -- ECMO continuous >96 hours  
            '5A1522G',  -- ECMO intermittent <6 hours/day
            '5A15223',  -- Extracorporeal oxygenation, membrane
            '5A1935Z'   -- Respiratory ventilation, less than 24 consecutive hours
        ))
        -- ICD-9 ECMO codes (if present)
        OR (p.icd_version = 9 AND p.icd_code IN (
            '3965',     -- Extracorporeal membrane oxygenation
            '3966'      -- Percutaneous cardiopulmonary bypass
        ))
),

ecmo_medications AS (
    -- Identify ECMO-related medications
    SELECT DISTINCT
        p.subject_id,
        p.hadm_id,
        p.starttime,
        p.endtime,
        p.drug as medication_name,
        'ecmo_medication' as identification_method
    FROM mimiciv_icu.prescriptions p
    WHERE 
        LOWER(p.drug) LIKE '%heparin%'
        OR LOWER(p.drug) LIKE '%bivalirudin%'
        OR LOWER(p.drug) LIKE '%argatroban%'
        -- High-dose vasopressor combinations suggesting ECMO support
        OR (LOWER(p.drug) LIKE '%norepinephrine%' AND p.dose_val_rx > 0.5)
        OR (LOWER(p.drug) LIKE '%epinephrine%' AND p.dose_val_rx > 0.3)
),

ecmo_chartevents AS (
    -- Identify ECMO from chartevents/monitoring data
    SELECT DISTINCT
        c.subject_id,
        c.hadm_id,
        c.stay_id,
        c.charttime,
        c.itemid,
        d.label,
        c.value,
        c.valuenum,
        'chart_events' as identification_method
    FROM mimiciv_icu.chartevents c
    LEFT JOIN mimiciv_icu.d_items d ON c.itemid = d.itemid
    WHERE 
        -- ECMO flow rates
        (d.label ILIKE '%ecmo%flow%' OR d.label ILIKE '%extracorporeal%flow%')
        -- ECMO pressures  
        OR (d.label ILIKE '%ecmo%pressure%')
        -- ECMO oxygenator parameters
        OR (d.label ILIKE '%sweep%gas%' OR d.label ILIKE '%oxygenator%')
        -- ECMO cannula documentation
        OR (d.label ILIKE '%cannula%' AND d.label ILIKE '%ecmo%')
        -- ECMO circuit parameters
        OR (d.label ILIKE '%ecmo%circuit%' OR d.label ILIKE '%membrane%oxygenator%')
        -- Look for specific ECMO-related itemids (these would need to be validated)
        OR c.itemid IN (
            -- These are example itemids - actual MIMIC-IV itemids would need verification
            227287, -- ECMO Flow
            227288, -- ECMO Sweep Gas
            227289  -- ECMO Pressure
        )
),

ecmo_notes AS (
    -- Identify ECMO from clinical notes
    SELECT DISTINCT
        n.subject_id,
        n.hadm_id,
        n.chartdate,
        n.category,
        n.description,
        'clinical_notes' as identification_method
    FROM mimiciv_note.noteevents n
    WHERE 
        -- Search for ECMO mentions in notes
        LOWER(n.text) LIKE '%ecmo%'
        OR LOWER(n.text) LIKE '%extracorporeal membrane oxygenation%'
        OR LOWER(n.text) LIKE '%extracorporeal life support%'
        OR LOWER(n.text) LIKE '%ecls%'
        -- Cannulation mentions
        OR (LOWER(n.text) LIKE '%cannul%' AND LOWER(n.text) LIKE '%extracorporeal%')
        -- ECMO weaning/decannulation
        OR LOWER(n.text) LIKE '%decannul%'
        OR (LOWER(n.text) LIKE '%wean%' AND LOWER(n.text) LIKE '%ecmo%')
),

-- Combine all identification methods
all_ecmo_episodes AS (
    SELECT subject_id, hadm_id, identification_method FROM ecmo_procedures
    UNION
    SELECT subject_id, hadm_id, identification_method FROM ecmo_medications  
    UNION
    SELECT subject_id, hadm_id, identification_method FROM ecmo_chartevents
    UNION
    SELECT subject_id, hadm_id, identification_method FROM ecmo_notes
),

-- Aggregate by patient and admission
ecmo_episodes_summary AS (
    SELECT 
        e.subject_id,
        e.hadm_id,
        STRING_AGG(DISTINCT e.identification_method, ', ') as identification_methods,
        COUNT(DISTINCT e.identification_method) as num_identification_methods
    FROM all_ecmo_episodes e
    GROUP BY e.subject_id, e.hadm_id
)

-- Main query with patient details
SELECT 
    p.subject_id,
    p.gender,
    p.anchor_age as age_at_admission,
    a.hadm_id,
    a.admittime,
    a.dischtime,
    a.deathtime,
    a.admission_type,
    a.admission_location,
    a.discharge_location,
    -- ECMO identification
    es.identification_methods,
    es.num_identification_methods,
    
    -- Clinical characteristics
    CASE WHEN a.deathtime IS NOT NULL THEN 1 ELSE 0 END as died_during_admission,
    DATE_PART('day', a.dischtime - a.admittime) as length_of_stay_days,
    
    -- Try to determine ECMO type from procedures
    CASE 
        WHEN ep.icd_code IN ('5A1522F', '5A1532F', '5A1522G') THEN 
            CASE 
                WHEN a.admission_type = 'URGENT' OR a.admission_type = 'EMERGENCY' 
                     OR a.admission_location LIKE '%EMERGENCY%' THEN 'VA_likely'
                ELSE 'VV_likely' 
            END
        ELSE 'unknown'
    END as probable_ecmo_type,
    
    -- Additional context
    ep.procedure_description as primary_ecmo_procedure

FROM ecmo_episodes_summary es
LEFT JOIN mimiciv_hosp.patients p ON es.subject_id = p.subject_id
LEFT JOIN mimiciv_hosp.admissions a ON es.hadm_id = a.hadm_id
LEFT JOIN ecmo_procedures ep ON es.subject_id = ep.subject_id AND es.hadm_id = ep.hadm_id
    AND ep.seq_num = (
        SELECT MIN(seq_num) 
        FROM ecmo_procedures ep2 
        WHERE ep2.subject_id = ep.subject_id AND ep2.hadm_id = ep.hadm_id
    )

ORDER BY es.num_identification_methods DESC, p.subject_id, a.admittime;

-- Additional queries for ECMO episode details

-- Query 2: ECMO Timeline and Parameters
SELECT 
    c.subject_id,
    c.hadm_id,
    c.stay_id,
    c.charttime,
    d.label as parameter_name,
    c.value,
    c.valuenum,
    c.valueuom as unit_of_measure,
    -- Categorize ECMO parameters
    CASE 
        WHEN d.label ILIKE '%flow%' THEN 'flow'
        WHEN d.label ILIKE '%pressure%' THEN 'pressure'  
        WHEN d.label ILIKE '%sweep%' THEN 'ventilator'
        WHEN d.label ILIKE '%temperature%' THEN 'temperature'
        ELSE 'other'
    END as parameter_category
FROM mimiciv_icu.chartevents c
LEFT JOIN mimiciv_icu.d_items d ON c.itemid = d.itemid
WHERE (c.subject_id, c.hadm_id) IN (
    SELECT DISTINCT subject_id, hadm_id FROM ecmo_episodes_summary
)
AND (
    d.label ILIKE '%ecmo%'
    OR d.label ILIKE '%extracorporeal%'
    OR d.label ILIKE '%sweep%gas%'
    OR d.label ILIKE '%oxygenator%'
)
ORDER BY c.subject_id, c.hadm_id, c.charttime;

-- Query 3: ECMO Outcomes and Complications
SELECT 
    es.subject_id,
    es.hadm_id,
    -- Complications during ECMO (based on diagnosis codes)
    STRING_AGG(
        CASE 
            WHEN d.icd_code LIKE 'T82.%' THEN 'Device_complication'
            WHEN d.icd_code IN ('D65', 'D68.%') THEN 'Coagulopathy' 
            WHEN d.icd_code LIKE 'N17.%' THEN 'Acute_kidney_injury'
            WHEN d.icd_code LIKE 'G93.%' THEN 'Brain_injury'
            ELSE NULL
        END, ', '
    ) as complications,
    
    -- Survival outcomes
    CASE WHEN a.deathtime IS NOT NULL THEN 0 ELSE 1 END as survived_to_discharge,
    CASE 
        WHEN a.discharge_location LIKE '%HOME%' THEN 'home'
        WHEN a.discharge_location LIKE '%REHAB%' THEN 'rehabilitation'  
        WHEN a.discharge_location LIKE '%SNF%' OR a.discharge_location LIKE '%SKILLED%' THEN 'skilled_nursing'
        WHEN a.discharge_location LIKE '%HOSPICE%' THEN 'hospice'
        ELSE a.discharge_location
    END as discharge_disposition

FROM ecmo_episodes_summary es
LEFT JOIN mimiciv_hosp.admissions a ON es.hadm_id = a.hadm_id
LEFT JOIN mimiciv_hosp.diagnoses_icd d ON es.hadm_id = d.hadm_id
GROUP BY es.subject_id, es.hadm_id, a.deathtime, a.discharge_location
ORDER BY es.subject_id;

/*
Usage Notes:
1. This query identifies potential ECMO episodes in MIMIC-IV
2. Multiple identification methods increase confidence 
3. Manual review recommended for clinical validation
4. ECMO type determination is probabilistic - clinical review needed
5. Itemids for ECMO parameters may need adjustment based on actual MIMIC-IV data dictionary

Validation Steps:
1. Review identified episodes manually
2. Cross-reference with procedure notes
3. Validate ECMO parameters and timelines  
4. Confirm ECMO type (VA vs VV) from clinical context
*/