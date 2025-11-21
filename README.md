# 🩸 Type & Screen + Transfusion Readiness Agent  
### *FHIR-Based Clinical Decision Support Prototype*

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/<USER>/<REPO>/<BRANCH>/images/readiness_banner_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/<USER>/<REPO>/<BRANCH>/images/readiness_banner.svg">
  <img alt="Type & Screen + Transfusion Readiness Agent" src="https://raw.githubusercontent.com/<USER>/<REPO>/<BRANCH>/images/readiness_banner.svg">
</picture>



![FHIR](https://img.shields.io/badge/FHIR-R4-orange?logo=fhir)
![Azure](https://img.shields.io/badge/Cloud-Azure-blue?logo=microsoftazure)
![Streamlit](https://img.shields.io/badge/App-Streamlit-red?logo=streamlit)
![Python](https://img.shields.io/badge/Language-Python-yellow?logo=python)
![LOINC](https://img.shields.io/badge/Terminology-LOINC-green)
![SNOMEDCT](https://img.shields.io/badge/Terminology-SNOMEDCT-lightgrey)

---

## 🧭 Overview
This project demonstrates how **FHIR resources**, **synthetic lab data**, and **Python-based analytics** can enable a *pre-operative Type & Screen readiness alert* and *transfusion readiness dashboard*.

It models how **EHR/LIS integration** (e.g., Cerner + WellSky) could automatically surface **blood-readiness alerts** to clinicians before surgery—supporting safer, faster, and more efficient perioperative workflows.

---

## 🎯 Goals
- Integrate **Type & Screen status**, **specimen validity**, and **blood product readiness** in one FHIR-driven view.  
- Enable **Clinical Decision Support (CDS)** by analyzing `Observation`, `Specimen`, and `ServiceRequest` resources.  
- Improve **Patient Blood Management (PBM)** by preventing same-day transfusion delays.

---

## ⚙️ Architecture
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="images/readiness_banner_dark_test.svg">
  <source media="(prefers-color-scheme: light)" srcset="images/readiness_banner.svg">
  <img alt="Type & Screen + Transfusion Readiness Agent" src="images/readiness_banner.svg">
</picture>


### Workflow Summary
1. **Data generation**  
   - `make_synthetic_type_and_screen.py` → Creates synthetic FHIR Observations (ABO, Rh, Antibody Screen).  
   - `make_synthetic_surgery_requests.py` → Creates FHIR `ServiceRequest` resources for upcoming surgeries.  
2. **Data upload**  
   - `upload_synthetic_type_and_screen.py` and `upload_synthetic_surgery_requests.py` use Azure CLI tokens to POST resources to the FHIR server.  
3. **Alert evaluation**  
   - `evaluate_tns_alerts.py` queries the FHIR endpoint to detect:  
     - ❌ No T&S before surgery  
     - ❌ Latest T&S older than 72 hours pre-op  
4. **Visualization**  
   - Displays results in a Streamlit dashboard for OR or Blood Bank teams.

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-------------|
| **Language** | Python 3.11 |
| **Frameworks** | Streamlit • Pandas • FHIR-Client |
| **FHIR Server** | Azure Health Data Services FHIR / HAPI-FHIR (local testing) |
| **Data Source** | Synthetic MIMIC-IV FHIR exports (`Observation`, `Specimen`, `ServiceRequest`) |
| **Terminologies** | LOINC (883-9, 10331-7, 890-4) • SNOMED CT (Blood Products) |

---

## 🧪 Example FHIR Resources

**Observation (ABO Group)**  
```json
{
  "resourceType": "Observation",
  "code": { "coding": [{ "system": "http://loinc.org", "code": "883-9", "display": "ABO group" }] },
  "valueString": "O",
  "effectiveDateTime": "2025-11-19T08:00:00Z"
}


