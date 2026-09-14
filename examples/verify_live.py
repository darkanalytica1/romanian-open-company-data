"""Call the official EU services. This example DOES use the network.

It makes a small number of requests, spaced by the library's rate limiter.
Please keep it that way. These endpoints are a public good maintained for one
at a time verification, not a bulk feed.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rocompany import eori, vies  # noqa: E402

# A real, public Romanian fiscal code, used here so the example is verifiable.
SAMPLE_CUI = 43825150


def main() -> None:
    print("VIES: is this VAT number valid right now?")
    result = vies.check("RO", SAMPLE_CUI)
    print(f"  valid   : {result.valid}")
    print(f"  name    : {result.name}")
    print(f"  checked : {result.checked_at}")
    print(f"  source  : {result.source_url}")
    if not result.conclusive:
        print(f"  NOTE    : inconclusive ({result.error}). Store as unknown, "
              f"never as invalid.")

    print()
    print("EORI: is this operator registered for customs?")
    check = eori.check(eori.build_eori(SAMPLE_CUI))
    print(f"  valid   : {check.valid}  (status {check.status_code}, "
          f"{check.status_text})")
    print(f"  name    : {check.name}")
    print(f"  city    : {check.city}")
    print(f"  publishes details: {check.publishes_details}")
    print(f"  checked : {check.checked_at}")

    print()
    print("EORI: a number that is not registered")
    missing = eori.check("RO00000000")
    print(f"  valid   : {missing.valid}  (status {missing.status_code}, "
          f"{missing.status_text})")
    print()
    print("Store every one of these with its checked_at and source_url.")


if __name__ == "__main__":
    main()
