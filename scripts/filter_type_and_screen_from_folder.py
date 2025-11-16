import json
import sys
import glob
from pathlib import Path
TARGET_LOINC_CODES = ["883-9", "10331-7", "890-4"]


# ---- CONFIG ----
# Output file name that your upload script was expecting:
OUTPUT_FILE = "filtered_type_and_screen_observations.ndjson"

# Keywords we’ll look for in the observation code text/display
TYPE_SCREEN_KEYWORDS = [
    "TYPE AND SCREEN",
    "TYPE & SCREEN",
    "TYPE&SCREEN",
    "T&S",
    "T AND S",
    "ABO/RH",
    "ABO RH",
    "ABORH",
    "ANTIBODY SCREEN",
    "ABO GROUP",
    "RH TYPE"
]


def is_type_and_screen(obs: dict) -> bool:
    if obs.get("resourceType") != "Observation":
        return False

    code = obs.get("code", {})
    for coding in code.get("coding", []):
        if coding.get("system") == "http://loinc.org" and coding.get("code") in TARGET_LOINC_CODES:
            return True

    return False


    code = obs.get("code", {})
    strings_to_check = []

    # code.text
    text = code.get("text")
    if isinstance(text, str):
        strings_to_check.append(text)

    # code.coding[*].display / code / text
    for coding in code.get("coding", []):
        for key in ["display", "code", "text"]:
            val = coding.get(key)
            if isinstance(val, str):
                strings_to_check.append(val)

    # Optional: also check category text/display if present
    for cat in obs.get("category", []):
        if isinstance(cat, dict):
            if isinstance(cat.get("text"), str):
                strings_to_check.append(cat["text"])
            for coding in cat.get("coding", []):
                for key in ["display", "code", "text"]:
                    val = coding.get(key)
                    if isinstance(val, str):
                        strings_to_check.append(val)

    # Normalize and match
    upper_keywords = [k.upper() for k in TYPE_SCREEN_KEYWORDS]

    for s in strings_to_check:
        s_up = s.upper()
        if any(kw in s_up for kw in upper_keywords):
            return True

    return False


def main():
    # If no files are passed, default to all .ndjson files in the folder
    if len(sys.argv) > 1:
        input_patterns = sys.argv[1:]
    else:
        input_patterns = ["*.ndjson"]

    # Expand globs (e.g. observations-*.ndjson)
    input_files = []
    for pattern in input_patterns:
        input_files.extend(glob.glob(pattern))

    if not input_files:
        print("No NDJSON files found. Pass file names, e.g.:")
        print("  python filter_type_and_screen_observations.py observations-*.ndjson")
        return
    # Don't use our own filtered output file as input
    input_files = [f for f in input_files if f != OUTPUT_FILE]

    print("Input files:")
    for f in input_files:
        print("  -", f)

    out_path = Path(OUTPUT_FILE)
    if out_path.exists():
        print(f"WARNING: Overwriting existing file: {OUTPUT_FILE}")
        out_path.unlink()

    total_in = 0
    total_out = 0

    with open(out_path, "w", encoding="utf-8") as out_f:
        for file in input_files:
            print(f"Processing {file} ...")
            with open(file, "r", encoding="utf-8") as in_f:
                for line in in_f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        # Skip bad lines
                        continue

                    total_in += 1
                    if is_type_and_screen(obj):
                        out_f.write(json.dumps(obj) + "\n")
                        total_out += 1

    print(f"\nDone.")
    print(f"Total observations checked: {total_in}")
    print(f"Type & Screen-like observations found: {total_out}")
    print(f"Filtered file written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
