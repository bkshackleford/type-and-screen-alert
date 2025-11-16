import json
import requests
import subprocess
from pathlib import Path

# 🔐 FHIR server URL (adjust if needed)
FHIR_URL = "https://fhirserver33-fhirservice333.fhir.azurehealthcareapis.com/Observation"

# 🔑 Get token using Azure CLI
def get_access_token():
    az_path = r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
    result = subprocess.run(
        [az_path, "account", "get-access-token",
         "--resource", FHIR_URL.replace("/Observation", ""),
         "--output", "json"],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print("❌ Failed to get access token")
        print(result.stderr)
        raise SystemExit(1)

    token_info = json.loads(result.stdout)
    return token_info["accessToken"]

# 🧾 File to upload  🔁 UPDATED NAME
ndjson_file = "synthetic_type_and_screen_observations.ndjson"

path = Path(ndjson_file)
if not path.exists():
    print(f"❌ NDJSON file not found: {path.resolve()}")
    raise SystemExit(1)

# 📤 Upload loop
access_token = get_access_token()
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/fhir+json"
}

with open(ndjson_file, "r", encoding="utf-8") as f:
    for line_number, line in enumerate(f, start=1):
        if not line.strip():
            continue
        try:
            observation = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"⚠️ Line {line_number}: Invalid JSON - {e}")
            continue

        response = requests.post(FHIR_URL, headers=headers, json=observation)

        if response.status_code in [200, 201]:
            print(f"✅ Line {line_number}: Uploaded")
        else:
            print(f"❌ Line {line_number}: Failed ({response.status_code})")
            print(response.text)
