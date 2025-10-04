# MIMIC-IV ECMO Identification and Feature Extraction

This directory contains PostgreSQL queries for identifying ECMO episodes and extracting features from MIMIC-IV 3.1 data, aligned with the ELSO (Extracorporeal Life Support Organization) Registry data dictionary.

## Files Overview

| File | Purpose | Dependencies | Output |
|------|---------|--------------|--------|
| `mimic_ecmo_itemids.sql` | Identify ECMO-related chart event item IDs | `mimiciv_icu.d_items` | List of itemids and ELSO categories |
| `identify_ecmo.sql` | Identify ECMO episodes with temporal boundaries | `mimiciv_icu.*`, `mimiciv_hosp.*` | ECMO episodes with mode and duration |
| `extract_ecmo_features.sql` | Extract comprehensive features for ML models | Output from `identify_ecmo.sql` | Complete feature set for prediction |

## Schema Assumptions

### MIMIC-IV Database Structure

These queries assume the standard MIMIC-IV 3.1 schema with two main schemas:

#### `mimiciv_hosp` (Hospital-level data)
- `patients` - Demographics
- `admissions` - Hospital admissions
- `diagnoses_icd` - ICD-10-CM diagnosis codes
- `d_icd_diagnoses` - Diagnosis code dictionary
- `procedures_icd` - ICD-10-PCS procedure codes
- `d_icd_procedures` - Procedure code dictionary
- `labevents` - Laboratory measurements
- `d_labitems` - Lab test dictionary

#### `mimiciv_icu` (ICU-level data)
- `icustays` - ICU stays
- `chartevents` - Time-series vital signs and parameters
- `d_items` - Chart event item dictionary

### Required Database Setup

```sql
-- Ensure schemas exist
CREATE SCHEMA IF NOT EXISTS mimiciv_hosp;
CREATE SCHEMA IF NOT EXISTS mimiciv_icu;

-- Grant permissions (adjust as needed)
GRANT USAGE ON SCHEMA mimiciv_hosp, mimiciv_icu TO your_user;
GRANT SELECT ON ALL TABLES IN SCHEMA mimiciv_hosp, mimiciv_icu TO your_user;
```

## Usage Guide

### Step 1: Identify ECMO-Related Item IDs

First, run `mimic_ecmo_itemids.sql` to identify which chart event item IDs correspond to ECMO parameters:

```bash
psql -d mimic4 -f sql/mimic_ecmo_itemids.sql -o ecmo_itemids_output.csv
```

**Expected Output:**
- List of `itemid` values from `d_items` table
- Categorized by ELSO data dictionary section (e.g., `support_params.flow`, `circuit.oxygenator`)
- Creates view `ecmo_item_reference` for future lookups

**Customization Required:**
Edit lines 48-54 to add known ECMO itemids specific to your MIMIC-IV instance:

```sql
WHERE itemid IN (
  227287, -- Example: ECMO Flow
  227288, -- Example: ECMO RPM
  227289  -- Example: Sweep Gas Flow
)
```

### Step 2: Identify ECMO Episodes

Run `identify_ecmo.sql` to identify all ECMO episodes with start/end times and mode:

```bash
psql -d mimic4 -f sql/identify_ecmo.sql -o ecmo_episodes.csv
```

**Logic:**
1. Searches for ECMO-related chart events (from keywords: ecmo, oxygenator, circuit, sweep, cannula)
2. Identifies procedure codes for ECMO (ICD-10-PCS: `5A1522F`, `5A1522G`)
3. Groups events into episodes using 48-hour gap threshold
4. Infers ECMO mode (VA/VV) from:
   - Primary diagnosis (cardiac → VA, respiratory → VV)
   - Procedure codes
   - Clinical context
5. Filters spurious episodes (< 1 hour duration or < 5 events)

**Key Output Columns:**
- `subject_id`, `hadm_id`, `stay_id` - Patient/admission/ICU identifiers
- `episode_num` - Sequential episode number per patient
- `ecmo_start_time`, `ecmo_end_time` - ECMO temporal boundaries
- `ecmo_duration_hours` - Total ECMO duration
- `ecmo_mode` - VA, VV, or Unknown
- `avg_flow_l_min`, `avg_sweep_l_min` - ECMO parameter summaries
- `survival_to_discharge` - Primary outcome (0/1)

**Performance Optimization:**
To improve query performance, create a materialized view (uncomment lines 291-294):

```sql
CREATE MATERIALIZED VIEW ecmo_episodes_identified AS
-- <paste the full query>

CREATE INDEX idx_ecmo_episodes_subject ON ecmo_episodes_identified(subject_id);
CREATE INDEX idx_ecmo_episodes_hadm ON ecmo_episodes_identified(hadm_id);
CREATE INDEX idx_ecmo_episodes_mode ON ecmo_episodes_identified(ecmo_mode);
```

### Step 3: Extract Features for ML Models

Run `extract_ecmo_features.sql` to extract comprehensive features aligned with ELSO:

```bash
psql -d mimic4 -f sql/extract_ecmo_features.sql -o ecmo_features_ml.csv
```

**Prerequisites:**
This query assumes you've created the `ecmo_episodes_identified` materialized view from Step 2. If not, you'll need to modify line 13 to include the full query from `identify_ecmo.sql`.

**Feature Categories Extracted:**

| ELSO Section | Features | Examples |
|--------------|----------|----------|
| **patient** | Demographics, anthropometrics | Age, sex, weight, height, BMI, BSA |
| **pre_ecmo** | Severity scores, diagnoses | SOFA, primary diagnosis, diagnosis category |
| **pre_ecmo** | Pre-ECMO labs (24h window) | pH, lactate, PaO2, creatinine, hemoglobin, platelets, INR |
| **pre_ecmo** | Respiratory metrics | PF ratio, oxygenation index, FiO2, PEEP |
| **pre_ecmo** | Pre-ECMO vitals (6h window) | HR, BP, MAP, SpO2, temperature |
| **pre_ecmo** | Mechanical ventilation | Hours on vent pre-ECMO |
| **support_params** | ECMO parameters | Flow, pump RPM, sweep gas, FiO2, temperature |
| **complications** | Binary flags | CNS hemorrhage, stroke, limb ischemia, AKI, sepsis, DIC |
| **interventions** | Procedures during ECMO | Transfusions, CRRT, fasciotomy, amputation |
| **outcomes** | Survival and LOS | Discharge survival, ICU/hospital LOS, discharge location |

**Total Features:** ~80+ variables for machine learning

## ELSO Data Dictionary Alignment

All extracted features map to the ELSO Registry v5.x data definitions specified in `data_dictionary.yaml`:

```yaml
# Example mapping
patient.age_years → age_years (SQL output column)
pre_ecmo.sofa_score → sofa_score
support_params.flow_l_min → avg_flow_l_min
outcomes.survival_to_hospital_discharge → survival_to_discharge
```

### ICD-10 Code Mappings

ECMO-relevant ICD codes are defined in `etl/codes/`:

- **Diagnoses:** `ecmo_diagnoses.yaml`
  - Cardiac: I46.9 (cardiac arrest), R57.0 (cardiogenic shock), I21.x (MI)
  - Respiratory: J80 (ARDS), J18.9 (pneumonia), U07.1 (COVID-19)
  - ECPR: I46.9 + primary diagnosis

- **Procedures:** `ecmo_procedures.yaml`
  - ECMO initiation: 5A1522F (ICD-10-PCS)
  - VA-ECMO: CPT 33946, 33947
  - VV-ECMO: CPT 33948, 33949

- **Complications:** `ecmo_complications.yaml`
  - Hemorrhage: I62.9 (CNS), R04.89 (pulmonary), K92.2 (GI)
  - Neurological: I63.9 (ischemic stroke), G93.82 (brain death)
  - Cardiovascular: I74.3 (limb ischemia), T79.A0XA (compartment syndrome)

## Data Quality Considerations

### Missing Data Handling

MIMIC-IV ECMO data has inherent limitations:

1. **ECMO Mode Detection:** Mode inference relies on diagnoses and procedures. In MIMIC-IV Demo, many episodes may be flagged as "Unknown" due to limited documentation.

2. **Chart Event Item IDs:** ECMO-specific itemids vary by hospital and MIMIC-IV version. **You MUST validate** itemids against your specific database instance.

3. **Temporal Gaps:** Chart events may be sparse. The query uses:
   - 24-hour window for pre-ECMO labs
   - 6-hour window for pre-ECMO vitals
   - 48-hour gap to separate ECMO episodes

4. **NULL Values:** Many features will have NULL values. Consider imputation strategies:
   - Median/mean for continuous variables
   - Mode for categorical variables
   - Carry-forward/carry-backward for time-series
   - Multiple imputation for ML models

### Validation Steps

Before using for analysis, validate:

```sql
-- 1. Check ECMO episode counts
SELECT COUNT(*) FROM ecmo_episodes_identified;
-- Expected: Small number in Demo dataset, hundreds in full MIMIC-IV

-- 2. Check mode distribution
SELECT ecmo_mode, COUNT(*) FROM ecmo_episodes_identified GROUP BY ecmo_mode;
-- Expected: VA > VV for cardiac patients

-- 3. Check feature completeness
SELECT
  COUNT(*) AS total_episodes,
  COUNT(sofa_score) AS has_sofa,
  COUNT(pf_ratio) AS has_pf_ratio,
  COUNT(avg_flow_l_min) AS has_flow
FROM ecmo_features_ml;

-- 4. Check outcome distribution
SELECT
  survival_to_discharge,
  COUNT(*) AS n,
  ROUND(AVG(icu_los_days), 2) AS avg_icu_los
FROM ecmo_features_ml
GROUP BY survival_to_discharge;
```

## Example: Running Complete Pipeline

```bash
# 1. Set up database connection
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=mimic4
export PGUSER=your_username

# 2. Identify ECMO item IDs
psql -f sql/mimic_ecmo_itemids.sql > output/ecmo_itemids.txt

# 3. Review and customize itemids (edit mimic_ecmo_itemids.sql lines 48-54)

# 4. Identify ECMO episodes (with materialized view)
psql -f sql/identify_ecmo.sql

# 5. Extract features for ML
psql -f sql/extract_ecmo_features.sql -o output/ecmo_features.csv

# 6. Validate output
psql -c "SELECT COUNT(*), AVG(ecmo_duration_hours), AVG(survival_to_discharge) FROM ecmo_features_ml;"
```

## Expected Output Schema

### `ecmo_episodes_identified` (from identify_ecmo.sql)

| Column | Type | Description |
|--------|------|-------------|
| subject_id | INTEGER | Patient ID |
| hadm_id | INTEGER | Hospital admission ID |
| stay_id | INTEGER | ICU stay ID |
| episode_num | INTEGER | Sequential ECMO episode number |
| ecmo_start_time | TIMESTAMP | ECMO cannulation time |
| ecmo_end_time | TIMESTAMP | ECMO decannulation time |
| ecmo_duration_hours | NUMERIC | Total ECMO duration |
| ecmo_mode | TEXT | VA, VV, or Unknown |
| avg_flow_l_min | NUMERIC | Average ECMO flow |
| survived_to_discharge | INTEGER | 0 = died, 1 = survived |

### `ecmo_features_ml` (from extract_ecmo_features.sql)

**80+ columns organized by ELSO sections:**

- **Identifiers (4):** subject_id, hadm_id, stay_id, episode_num
- **Episode (3):** start_time, end_time, duration, mode
- **Demographics (7):** age, sex, race, weight, height, BMI, BSA
- **Diagnosis (3):** ICD code, description, category
- **Pre-ECMO Labs (17):** pH, gases, electrolytes, hematology, coagulation
- **Pre-ECMO Vitals (7):** HR, BP, SpO2, temperature, respiratory rate
- **Pre-ECMO Respiratory (4):** PF ratio, oxygenation index, FiO2, PEEP
- **ECMO Support (9):** Flow, RPM, sweep gas, FiO2, temperature
- **Complications (17):** Hemorrhage, stroke, ischemia, infection, etc.
- **Interventions (7):** Transfusions, CRRT, surgeries
- **Outcomes (6):** Survival, LOS, discharge location

## Troubleshooting

### Common Issues

**1. No ECMO episodes found**
```sql
-- Check if ECMO itemids exist
SELECT COUNT(*) FROM mimiciv_icu.d_items
WHERE LOWER(label) LIKE '%ecmo%';
```
If zero, your MIMIC-IV instance may not have ECMO patients or uses different terminology.

**2. All modes are "Unknown"**
- This is expected in MIMIC-IV Demo due to limited data
- Full MIMIC-IV has better mode documentation
- Manually verify mode using chart review if needed

**3. Query timeout**
- Create indexes on join columns:
```sql
CREATE INDEX idx_chartevents_itemid ON mimiciv_icu.chartevents(itemid);
CREATE INDEX idx_chartevents_subject ON mimiciv_icu.chartevents(subject_id);
CREATE INDEX idx_chartevents_time ON mimiciv_icu.chartevents(charttime);
```

**4. Different schema names**
If your MIMIC-IV uses different schema names (e.g., `mimic_icu` instead of `mimiciv_icu`), use find-replace:
```bash
sed 's/mimiciv_icu/mimic_icu/g' sql/identify_ecmo.sql > sql/identify_ecmo_fixed.sql
sed 's/mimiciv_hosp/mimic_hosp/g' sql/identify_ecmo_fixed.sql -i
```

## Citation

If you use these queries in published research, please cite:

- **MIMIC-IV:** Johnson, A., Bulgarelli, L., Pollard, T., Horng, S., Celi, L. A., & Mark, R. (2023). MIMIC-IV (version 2.2). PhysioNet. https://doi.org/10.13026/6mm1-ek67

- **ELSO Registry:** Extracorporeal Life Support Organization. ELSO Registry Data Definitions. https://www.elso.org/Registry/DataDefinitions.aspx

## Contributing

To improve these queries:

1. Add missing ECMO itemids specific to your institution
2. Improve mode detection logic with additional heuristics
3. Add NIRS (near-infrared spectroscopy) features if available
4. Incorporate additional ELSO fields (e.g., cannulation details, circuit changes)

## License

See project LICENSE file. MIMIC-IV data requires PhysioNet credentialing and DUA.
