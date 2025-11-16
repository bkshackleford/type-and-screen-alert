import json
import uuid
from datetime import datetime, timedelta
from collections import defaultdict

PATIENT_FILE = "MimicPatient.ndjson"
TNS_FILE = "synthetic_type_and_screen_observations.ndjson"
OUTPUT_FILE = "synthetic_surgery_requests.ndjson"

# How far before surgery a T&S is considered valid (e.g., 72 hours)
TNS_VALID_HOURS = 72

# Define a few synthetic surgery types
SURGERY_TYPES = [
    {
        "code": "80146002",
        "display": "Coronary artery bypass graft",
    },
    {
        "code": "52734007",
        "display": "Total hip replacement",
    },
    {
        "code": "180325003",
        "display": "Laparoscopic cholecystectomy",
    },
]


def iso(dt):
    return dt.isoformat(timespec="seconds") + "Z"


def load_latest_tns_per_patient():
    """Return dict[patient_id] -> latest T&S datetime (or None)."""
    tns_times = defaultdict(lambda: None)

    with open(TNS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obs = json.loads(line)
            except json.JSONDecodeError:
                continue

            if obs.get("resourceType") != "Observation":
                continue

            subject = obs.get("subject", {})
            ref = subject.get("reference")
            if not ref or not ref.startswith("Patient/"):
                continue

            patient_id = ref.split("/", 1)[1]

            eff = obs.get("effectiveDateTime")
            if not eff:
                continue

            try:
                dt = datetime.fromisoformat(eff.replace("Z", "+00:00"))
            except ValueError:
                continue

            current = tns_times[patient_id]
            if current is None or dt > current:
                tns_times[patient_id] = dt

    return tns_times


def load_patient_ids(max_patients=10):
    patient_ids = []
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
                if len(patient_ids) >= max_patients:
                    break
    return patient_ids


def main():
    patient_ids = load_patient_ids(max_patients=10)
    if not patient_ids:
        print("❌ No patients found in MimicPatient.ndjson")
        return

    tns_latest = load_latest_tns_per_patient()
    print(f"Loaded latest T&S times for {len(tns_latest)} patients.")

    now = datetime.utcnow()
    records = []

    for i, pid in enumerate(patient_ids, start=1):
        # Rotate through surgery types
        stype = SURGERY_TYPES[(i - 1) % len(SURGERY_TYPES)]

        # Decide scenario:
        #  - 1,4,7,...: Good T&S (within 72h)
        #  - 2,5,8,...: Old T&S (>72h)
        #  - 3,6,9,...: No T&S on file
        scenario = i % 3

        base_time = now + timedelta(days=1 + i)  # surgery scheduled in future
        occurrence_time = base_time

        # Attach T&S scenario notes
        if scenario == 1:  # good T&S
            note = f"T&S expected to be valid (within {TNS_VALID_HOURS}h)."
        elif scenario == 2:  # old T&S
            note = f"T&S may be outdated (> {TNS_VALID_HOURS}h before surgery)."
        else:  # scenario == 0: no T&S
            note = "No T&S on file for this patient."

        sr = {
            "resourceType": "ServiceRequest",
            "id": str(uuid.uuid4()),
            "status": "active",
            "intent": "order",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "387713003",
                            "display": "Surgical procedure"
                        }
                    ],
                    "text": "Surgical procedure"
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": stype["code"],
                        "display": stype["display"]
                    }
                ],
                "text": stype["display"]
            },
            "subject": {
                "reference": f"Patient/{pid}"
            },
            "authoredOn": iso(now),
            "occurrenceDateTime": iso(occurrence_time),
            "note": [
                {
                    "text": note
                }
            ]
        }

        records.append(sr)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"✅ Wrote {len(records)} synthetic surgery ServiceRequests to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
