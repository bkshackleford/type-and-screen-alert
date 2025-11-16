import json
import requests
import subprocess
from datetime import datetime, timedelta

# ------------------------------------------
# CONFIGURATION
# ------------------------------------------

FHIR_BASE = "https://fhirserver33-fhirservice333.fhir.azurehealthcareapis.com"

# LOINC codes for Type & Screen components
TNS_CODES = [
    "883-9",     # ABO group
    "10331-7",   # Rh type
    "890-4"      # Antibody screen
]

# How long a Type & Screen is valid before surgery
TNS_VALID_HOURS = 72


# ------------------------------------------
# HELPERS
# ------------------------------------------

def get_access_token():
    """
    Uses Azure CLI to get a Bearer token for authenticating
    to the Azure FHIR server.
    """

    az_path = r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"

    result = subprocess.run(
        [
            az_path,
            "account", "get-access-token",
            "--resource", FHIR_BASE,
            "--output", "json"
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("❌ Failed to get access token.")
        print(result.stderr)
        raise SystemExit(1)

    token_info = json.loads(result.stdout)
    return token_info["accessToken"]


def parse_iso(dt_str):
    """Convert ISO 8601 into datetime object."""
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


# ------------------------------------------
# FETCH FHIR DATA
# ------------------------------------------

def fetch_all_surgery_requests(token):
    """
    Fetch all ServiceRequests from the FHIR server.
    These are our synthetic surgeries.
    """

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{FHIR_BASE}/ServiceRequest?_count=200"

    surgeries = []

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to fetch ServiceRequests: {response.status_code}")
            print(response.text)
            break

        bundle = response.json()

        for entry in bundle.get("entry", []):
            res = entry.get("resource", {})
            if res.get("resourceType") == "ServiceRequest":
                surgeries.append(res)

        # Pagination
        next_url = None
        for link in bundle.get("link", []):
            if link.get("relation") == "next":
                next_url = link.get("url")
                break

        url = next_url

    return surgeries


def fetch_latest_tns_for_patient(token, patient_id):
    """
    Fetch Observations with T&S LOINC codes for a specific patient.
    Sort newest → oldest via _sort=-date
    """

    headers = {"Authorization": f"Bearer {token}"}

    # Build the multi-code query parameter
    code_param = ",".join([f"http://loinc.org|{c}" for c in TNS_CODES])

    url = (
        f"{FHIR_BASE}/Observation"
        f"?subject=Patient/{patient_id}"
        f"&code={code_param}"
        f"&_sort=-date"
        f"&_count=50"
    )

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"⚠️ Error fetching Observations for patient {patient_id}: {response.status_code}")
        return []

    bundle = response.json()
    observations = []

    for entry in bundle.get("entry", []):
        obs = entry.get("resource", {})
        if obs.get("resourceType") == "Observation":
            observations.append(obs)

    return observations


# ------------------------------------------
# ALERT LOGIC
# ------------------------------------------

def evaluate_surgery(token, sr):
    """
    Main logic:
    - Identify the patient and surgery time
    - Find latest T&S before the surgery
    - Determine if T&S is missing or too old
    """

    subject = sr.get("subject", {})
    ref = subject.get("reference")

    if not ref or not ref.startswith("Patient/"):
        return None

    patient_id = ref.split("/")[1]

    # Surgery date/time
    surgery_time_str = sr.get("occurrenceDateTime")
    if not surgery_time_str:
        return None

    surgery_time = parse_iso(surgery_time_str)
    window_start = surgery_time - timedelta(hours=TNS_VALID_HOURS)

    # Get patient’s T&S Observations
    observations = fetch_latest_tns_for_patient(token, patient_id)

    latest_tns_time = None

    for obs in observations:
        eff = obs.get("effectiveDateTime")
        if not eff:
            continue

        try:
            eff_dt = parse_iso(eff)
        except:
            continue

        # Only count T&S BEFORE surgery
        if eff_dt > surgery_time:
            continue

        if latest_tns_time is None or eff_dt > latest_tns_time:
            latest_tns_time = eff_dt

    # ----------------------------------
    # Alert Conditions
    # ----------------------------------

    if latest_tns_time is None:
        return {
            "patient_id": patient_id,
            "surgery_id": sr.get("id"),
            "surgery_time": surgery_time.isoformat(),
            "alert": True,
            "reason": "No Type & Screen on file before surgery."
        }

    if latest_tns_time < window_start:
        return {
            "patient_id": patient_id,
            "surgery_id": sr.get("id"),
            "surgery_time": surgery_time.isoformat(),
            "latest_tns_time": latest_tns_time.isoformat(),
            "alert": True,
            "reason": f"Latest Type & Screen is older than {TNS_VALID_HOURS} hours."
        }

    # If we reach here → T&S is valid
    return {
        "patient_id": patient_id,
        "surgery_id": sr.get("id"),
        "surgery_time": surgery_time.isoformat(),
        "latest_tns_time": latest_tns_time.isoformat(),
        "alert": False,
        "reason": "Type & Screen is up to date."
    }


# ------------------------------------------
# MAIN ENTRY POINT
# ------------------------------------------

def main():
    prin
