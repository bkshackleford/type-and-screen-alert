import json
import requests
import subprocess

# ⚙️ Adjust if needed for your server:
FHIR_BASE = "https://fhirserver33-fhirservice333.fhir.azurehealthcareapis.com"
RESOURCE_URL = f"{FHIR_BASE}/ServiceRequest"

# 📄 This is the file created by make_synthetic_surgery_requests.py
NDJSON_FILE = "synthetic_surgery_requests.ndjson"


def get_access_token():
    # Path to Azure CLI
    az_path = r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"

    result = subprocess.run(
        [
            az_path,
            "account",
            "get-access-token",
            "--resource",
            FHIR_BASE,
            "--output",
            "json",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("❌ Failed to get access token")
        print(result.stderr)
        raise SystemExit(1)

    token_json = json.loads(result.stdout)
    return token_json["accessToken"]


def main():
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/fhir+json",
    }

    print(f"Uploading records from {NDJSON_FILE} to ServiceRequest endpoint...\n")

    with open(NDJSON_FILE, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                resource = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"⚠️ Line {line_number}: Invalid JSON - {e}")
                continue

            response = requests.post(RESOURCE_URL, headers=headers, json=resource)

            if response.status_code in (200, 201):
                print(f"✅ Line {line_number}: Uploaded")
            else:
                print(f"❌ Line {line_number}: Failed ({response.status_code})")
                print(response.text)
                break


if __name__ == "__main__":
    main()
