\# Type \& Screen Readiness Alert (FHIR + Synthetic Data)



\## Overview



This project demonstrates how a pre–operative \*\*Type \& Screen readiness alert\*\* could work using:



\- 🧪 \*\*Synthetic lab data\*\* for:

&nbsp; - ABO group (LOINC \*\*883-9\*\*)

&nbsp; - Rh type (LOINC \*\*10331-7\*\*)

&nbsp; - Antibody screen (LOINC \*\*890-4\*\*)

\- 🏥 \*\*Synthetic surgery orders\*\* modeled as FHIR `ServiceRequest`

\- ☁️ An \*\*Azure Health Data Services FHIR\*\* server

\- 🧾 Simple Python scripts to:

&nbsp; - Generate FHIR resources (NDJSON)

&nbsp; - Upload them to FHIR

&nbsp; - Evaluate an alert rule:  

&nbsp;   > “Does this patient have a valid Type \& Screen within 72 hours of surgery?”



The clinical idea:  

Before surgery, patients should have a \*\*current Type \& Screen\*\* so blood is available if needed. This project shows how that logic could be implemented on FHIR data as a decision-support style alert.



---



\## Architecture



High level:



1\. \*\*Data generation\*\*

&nbsp;  - `make\_synthetic\_type\_and\_screen.py`  

&nbsp;    → creates synthetic FHIR `Observation` resources (ABO, Rh, Ab screen)  

&nbsp;  - `make\_synthetic\_surgery\_requests.py`  

&nbsp;    → creates FHIR `ServiceRequest` resources for upcoming surgeries



2\. \*\*Data upload\*\*

&nbsp;  - `upload\_synthetic\_type\_and\_screen.py`  

&nbsp;  - `upload\_synthetic\_surgery\_requests.py`  

&nbsp;  These use Azure CLI to get a token and POST resources to the FHIR server.



3\. \*\*Alert evaluation\*\*

&nbsp;  - `evaluate\_tns\_alerts.py` queries:

&nbsp;    - surgeries (`ServiceRequest`)

&nbsp;    - recent Type \& Screen observations (`Observation` with LOINC 883-9, 10331-7, 890-4)

&nbsp;  - It flags surgeries where:

&nbsp;    - ❌ No T\&S exists before surgery, or  

&nbsp;    - ❌ Latest T\&S is older than \*\*72 hours\*\* before the scheduled surgery time



---



\## Prerequisites



\- Python 3.10+  

\- Azure subscription with \*\*Azure Health Data Services – FHIR\*\* service

\- Azure CLI installed and logged in (`az login`)

\- Access to a FHIR server URL, e.g.:

## 📺 Demo Output

Example run of the alert evaluator:

```text
🚀 evaluate_tns_alerts.py starting up...
🔐 Getting Azure FHIR token...
📥 Fetching synthetic surgeries (ServiceRequest)...
🔎 Found 20 surgeries.

==============================
  🩸 Surgeries Needing T&S
==============================

⚠️ Patient 74a2fd87-885b-5eca-9f8b-9141915dba51 | Surgery be6f0bc0-781b-4079-816b-2484902e6a34
   Reason: Latest Type & Screen is older than 72 hours.

⚠️ Patient a3a12d01-dc21-565b-89e2-da60e7fc80dc | Surgery 8d8d2566-5259-45b1-ade5-0f9c378835c2
   Reason: No Type & Screen on file before surgery.

... (additional cases omitted for brevity) ...



&nbsp; ```text

&nbsp; https://fhirserver33-fhirservice333.fhir.azurehealthcareapis.com



