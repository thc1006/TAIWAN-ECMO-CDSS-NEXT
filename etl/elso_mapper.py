
from typing import Dict, Any

LOCAL_TO_ELSO = {
    "subject_id": "patient.id",
    "age": "patient.age_years",
    "sex": "patient.sex",
    "mode": "ecmo.mode",
    "start_time": "ecmo.start_time",
    "end_time": "ecmo.end_time",
    "lactate_mmol_l": "labs.lactate",
    "survival_to_discharge": "outcomes.survival_to_discharge",
}

def map_record(row: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in row.items():
        key = LOCAL_TO_ELSO.get(k)
        if key:
            out[key] = v
    return out
