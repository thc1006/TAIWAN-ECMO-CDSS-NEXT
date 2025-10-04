-- MIMIC-IV ECMO Item ID Identification
-- Purpose: Identify all chart event item IDs related to ECMO support
-- Schema: MIMIC-IV 3.1 (icu.d_items)
-- Output: Item IDs for ECMO parameters, settings, and monitoring

-- =====================================================================
-- Part 1: Identify all ECMO-related items from d_items dictionary
-- =====================================================================
WITH ecmo_keywords AS (
  -- Define comprehensive search patterns for ECMO-related items
  SELECT pattern_name, pattern FROM (VALUES
    ('ECMO General', 'ecmo'),
    ('Oxygenator', 'oxygenator|membrane'),
    ('Circuit Flow', 'ecmo.*flow|circuit.*flow'),
    ('Pump', 'ecmo.*pump|circuit.*pump|rpm'),
    ('Sweep Gas', 'sweep|sweep.*gas'),
    ('Cannula', 'cannula|cannulation'),
    ('ECMO FiO2', 'ecmo.*fio2|circuit.*fio2'),
    ('ECMO Pressure', 'ecmo.*pressure|circuit.*pressure|pre.*oxy|post.*oxy'),
    ('ECMO Temperature', 'ecmo.*temp|circuit.*temp'),
    ('ECMO Anticoagulation', 'ecmo.*heparin|circuit.*heparin|act'),
    ('ECMO Mode', 'ecmo.*mode|va.*ecmo|vv.*ecmo'),
    ('ECMO Blood Gas', 'ecmo.*ph|ecmo.*po2|ecmo.*pco2')
  ) AS t(pattern_name, pattern)
),

-- Search d_items for matching labels and categories
ecmo_items_raw AS (
  SELECT DISTINCT
    d.itemid,
    d.label,
    d.category,
    d.unitname,
    d.param_type,
    k.pattern_name AS matched_pattern
  FROM mimiciv_icu.d_items d
  CROSS JOIN ecmo_keywords k
  WHERE
    LOWER(d.label) ~ k.pattern
    OR LOWER(d.category) ~ k.pattern
),

-- Manually add known ECMO-related itemids (based on MIMIC-IV documentation)
-- Note: These are example itemids - actual itemids may vary by MIMIC-IV version
known_ecmo_items AS (
  SELECT itemid, label, category, unitname, param_type, 'Known ECMO Item' AS matched_pattern
  FROM mimiciv_icu.d_items
  WHERE itemid IN (
    -- Add specific itemids here based on your MIMIC-IV instance
    -- Example format (these are placeholders - verify against your database):
    -- 227287, -- ECMO Flow
    -- 227288, -- ECMO RPM
    -- 227289  -- Sweep Gas Flow
  )
),

-- Combine regex matches and known items
all_ecmo_items AS (
  SELECT * FROM ecmo_items_raw
  UNION
  SELECT * FROM known_ecmo_items
)

-- =====================================================================
-- Final output: All ECMO-related items with categorization
-- =====================================================================
SELECT
  itemid,
  label,
  category,
  unitname,
  param_type,
  matched_pattern,
  -- Categorize by ELSO data dictionary mapping
  CASE
    WHEN LOWER(label) ~ 'flow|rpm' THEN 'support_params.flow'
    WHEN LOWER(label) ~ 'sweep' THEN 'support_params.sweep_gas'
    WHEN LOWER(label) ~ 'fio2' THEN 'support_params.fio2_ecmo'
    WHEN LOWER(label) ~ 'pressure' THEN 'support_params.pressure'
    WHEN LOWER(label) ~ 'temp' THEN 'support_params.temperature'
    WHEN LOWER(label) ~ 'mode' THEN 'ecmo_episode.mode'
    WHEN LOWER(label) ~ 'oxygenator' THEN 'circuit.oxygenator'
    WHEN LOWER(label) ~ 'cannula' THEN 'cannulation'
    WHEN LOWER(label) ~ 'heparin|anticoag|act' THEN 'circuit.anticoagulation'
    ELSE 'other'
  END AS elso_category
FROM all_ecmo_items
ORDER BY elso_category, category, label;

-- =====================================================================
-- Part 2: Create a reference view for ECMO item lookups
-- =====================================================================
CREATE OR REPLACE VIEW ecmo_item_reference AS
SELECT
  itemid,
  label,
  category,
  unitname,
  param_type,
  CASE
    WHEN LOWER(label) ~ 'flow|rpm' THEN 'support_params.flow'
    WHEN LOWER(label) ~ 'sweep' THEN 'support_params.sweep_gas'
    WHEN LOWER(label) ~ 'fio2' THEN 'support_params.fio2_ecmo'
    WHEN LOWER(label) ~ 'pressure' THEN 'support_params.pressure'
    WHEN LOWER(label) ~ 'temp' THEN 'support_params.temperature'
    WHEN LOWER(label) ~ 'mode' THEN 'ecmo_episode.mode'
    WHEN LOWER(label) ~ 'oxygenator' THEN 'circuit.oxygenator'
    WHEN LOWER(label) ~ 'cannula' THEN 'cannulation'
    WHEN LOWER(label) ~ 'heparin|anticoag|act' THEN 'circuit.anticoagulation'
    ELSE 'other'
  END AS elso_category
FROM mimiciv_icu.d_items
WHERE
  LOWER(label) ~ '(ecmo|oxygenator|circuit|sweep|cannula)'
  OR LOWER(category) ~ 'ecmo';

-- =====================================================================
-- Part 3: Export results for validation
-- =====================================================================
COMMENT ON VIEW ecmo_item_reference IS
'Reference view mapping MIMIC-IV chart event itemids to ELSO data dictionary categories for ECMO support parameters';