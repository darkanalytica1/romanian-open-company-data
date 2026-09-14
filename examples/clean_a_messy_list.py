"""Clean a realistic, messy supplier list. No network required.

This is the shape of nearly every real ingest: a spreadsheet from a partner,
exported by someone who had no idea what you were going to do with it.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rocompany import caen, cui, names  # noqa: E402

# Entirely fictional rows, written to contain every problem you will meet.
MESSY_ROWS = [
    {"id": "RO 4382 5150", "name": "S.C. ALFA COM S.R.L.", "caen": "4941"},
    {"id": "43825150.0", "name": "ALFA COM SRL", "caen": "4941.0"},
    {"id": "  14162177", "name": "Ţesătoria Şerban S.A.", "caen": "1310"},
    {"id": "14162177", "name": "Țesătoria Șerban SA", "caen": "1310"},
    {"id": "0722 123 456", "name": "BETA TRANS SRL", "caen": "4941"},
    {"id": "", "name": "GAMMA PROD S.R.L. (IN INSOLVENTA)", "caen": "111"},
    {"id": "5661836", "name": "GAMMA PROD SRL", "caen": "3400"},
]


def main() -> None:
    print(f"{'input id':>14}  {'valid':<5}  {'name core':<22}  {'form':<5}  "
          f"{'caen':<5}  section")
    print("-" * 78)

    seen: dict[str, list[str]] = {}
    for row in MESSY_ROWS:
        valid = cui.is_valid(row["id"])
        parsed = names.parse(row["name"])
        code = caen.normalise(row["caen"])
        section = caen.section_of(code) if code else None

        print(f"{row['id']:>14}  {str(valid):<5}  {parsed.core:<22}  "
              f"{str(parsed.legal_form or ''):<5}  {str(code or ''):<5}  "
              f"{section or '-'}")

        if valid:
            seen.setdefault(str(cui.parse(row['id'])), []).append(parsed.core)

    print()
    print("What the cleaning bought us")
    print("-" * 78)
    duplicates = {k: v for k, v in seen.items() if len(v) > 1}
    for code, variants in duplicates.items():
        collapsed = set(variants)
        print(f"  CUI {code}: {len(variants)} rows, {len(collapsed)} distinct "
              f"name(s) after normalisation -> {collapsed}")

    distressed = [names.parse(r['name']) for r in MESSY_ROWS]
    flagged = [p.raw for p in distressed if p.is_distressed]
    print(f"  insolvency flagged on: {flagged}")

    bad_codes = [r['caen'] for r in MESSY_ROWS if not caen.normalise(r['caen'])]
    print(f"  activity codes rejected as impossible: {bad_codes}")
    print("    (3400 is rejected because division 34 does not exist in NACE)")

    dropped = [r['id'] for r in MESSY_ROWS if not cui.is_valid(r['id'])]
    print(f"  rows with no usable identifier: {dropped}")


if __name__ == "__main__":
    main()
