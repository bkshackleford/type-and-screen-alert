import json
import uuid
from datetime import datetime, timedelta

PATIENT_FILE = "MimicPatient.ndjson"
OUTPUT_FILE = "synthetic_type_and_screen_observations.ndjson"

# We'll create T&S data for the first N patients we find
NUM_PATIENTS = 5

# Simple pool of blood types to make things look realistic
ABO_TYPES = ["A", "B", "AB", "O"]
RH_TYPES = ["POS", "NEG"]


def iso(dt):
    return dt.isoformat(timespec="seconds") + "Z"


def main():
    patient_ids = []

    # 1) Grab some patient IDs from MimicPatient.ndjson
    with open(PATIENT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                patient = json.loads(line)
            except json.JSONDecodeError:
                continue

            if patient.get("resourceType") != "Patient":
                continue

            pid = patient.get("id")
            if pid:
                patient_ids.append(pid)
                if len(patient_ids) >= NUM_PATIENTS:
                    break

    if not patient_ids:
        print("❌ No patients found in MimicPatient.ndjson")
        return

    print(f"Using {len(patient_ids)} patients for synthetic Type & Screen data.")

    # 2) Create synthetic Observations
    now = datetime.utcnow()
    records = []

    for i, pid in enumerate(patient_ids, start=1):
        # Use different times for each patient, some in the past few days
        base_time = now - timedelta(days=i)

        abo = ABO_TYPES[i % len(ABO_TYPES)]
        rh = RH_TYPES[i % len(RH_TYPES)]
        ab_screen_positive = (i % 3 == 0)  # every 3rd patient has a positive screen

        # ABO
        records.append({
            "resourceType": "Observation",
            "id": str(uuid.uuid4()),
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "883-9",
                    "display": "ABO group [Type] in Blood"
                }],
                "text": "ABO group"
            },
            "subject": {"reference": f"Patient/{pid}"},
            "effectiveDateTime": iso(base_time),
            "valueCodeableConcept": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0201",
                    "code": abo,
                    "display": abo
                }],
                "text": abo
            }
        })

        # Rh
        records.append({
            "resourceType": "Observation",
            "id": str(uuid.uuid4()),
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "10331-7",
                    "display": "Rh [Type] in Blood"
                }],
                "text": "Rh type"
            },
            "subject": {"reference": f"Patient/{pid}"},
            "effectiveDateTime": iso(base_time),
            "valueCodeableConcept": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                    "code": rh,
                    "display": rh
                }],
                "text": rh
            }
        })

        # Antibody Screen
        ab_screen_text = "POSITIVE" if ab_screen_positive else "NEGATIVE"
        ab_screen_code = "POS" if ab_screen_positive else "NEG"

        records.append({
            "resourceType": "Observation",
            "id": str(uuid.uuid4()),
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "890-4",
                    "display": "Blood group antibody screen [Presence] in Serum or Plasma"
                }],
                "text": "Antibody screen (transfusion)"
            },
            "subject": {"reference": f"Patient/{pid}"},
            "effectiveDateTime": iso(base_time),
            "valueCodeableConcept": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0078",
                    "code": ab_screen_code,
                    "display": ab_screen_text
                }],
                "text": ab_screen_text
            }
        })

    # 3) Write NDJSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"✅ Wrote {len(records)} synthetic Type & Screen observations to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
