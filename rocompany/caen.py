"""CAEN activity codes: sections, and how to load the official nomenclature.

CAEN is the Romanian implementation of the EU NACE classification. Every
company declares one principal code, and it is the single most useful field
for segmentation you get for free from the public register.

Section boundaries are stable and are hardcoded here. The full list of
division, group and class labels is published by the National Institute of
Statistics and by Eurostat, and it is revised. Hardcoding several hundred
labels into a library guarantees they will be wrong within a few years, so
this module ships the stable part and gives you a loader for the rest. That
is the general rule with public nomenclatures: pin the structure, load the
labels.

A practical warning. The declared principal code describes what the company
registered to do, not necessarily what it does today, and companies rarely
update it. Treat it as a strong prior, never as ground truth. Check it
against revenue, employee count and the company website before you build a
campaign on it.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass

#: NACE / CAEN Rev. 2 sections. ``(first_division, last_division, label)``.
SECTIONS: dict[str, tuple[int, int, str]] = {
    "A": (1, 3, "Agriculture, forestry and fishing"),
    "B": (5, 9, "Mining and quarrying"),
    "C": (10, 33, "Manufacturing"),
    "D": (35, 35, "Electricity, gas, steam and air conditioning supply"),
    "E": (36, 39, "Water supply, sewerage, waste management and remediation"),
    "F": (41, 43, "Construction"),
    "G": (45, 47, "Wholesale and retail trade, repair of motor vehicles"),
    "H": (49, 53, "Transportation and storage"),
    "I": (55, 56, "Accommodation and food service activities"),
    "J": (58, 63, "Information and communication"),
    "K": (64, 66, "Financial and insurance activities"),
    "L": (68, 68, "Real estate activities"),
    "M": (69, 75, "Professional, scientific and technical activities"),
    "N": (77, 82, "Administrative and support service activities"),
    "O": (84, 84, "Public administration and defence, compulsory social security"),
    "P": (85, 85, "Education"),
    "Q": (86, 88, "Human health and social work activities"),
    "R": (90, 93, "Arts, entertainment and recreation"),
    "S": (94, 96, "Other service activities"),
    "T": (97, 98, "Activities of households as employers"),
    "U": (99, 99, "Activities of extraterritorial organisations and bodies"),
}


@dataclass(frozen=True)
class Code:
    """A parsed CAEN class code such as ``4941``."""

    value: str

    @property
    def division(self) -> int:
        return int(self.value[:2])

    @property
    def group(self) -> str:
        return self.value[:3]

    @property
    def section(self) -> str | None:
        return section_of(self.value)

    @property
    def section_label(self) -> str | None:
        sec = self.section
        return SECTIONS[sec][2] if sec else None


def normalise(raw: str | int) -> str | None:
    """Return a 4 digit CAEN class, or None if the value cannot be one.

    Accepts ``4941``, ``"4941"``, ``"4941.0"`` and ``"CAEN 4941"``. Codes
    shorter than four digits are zero padded on the left, which is how
    divisions such as 01 arrive from spreadsheets that stripped the zero.
    """
    text = str(raw).strip()
    if text.endswith(".0"):  # spreadsheets love turning 4941 into 4941.0
        text = text[:-2]
    digits = "".join(c for c in text if c.isdigit())
    if not digits or len(digits) > 4:
        return None
    padded = digits.rjust(4, "0")
    return padded if section_of(padded) else None


def section_of(code: str | int) -> str | None:
    """Return the section letter for a CAEN code, or None if out of range."""
    digits = "".join(c for c in str(code) if c.isdigit())
    if not digits:
        return None
    division = int(digits[:2].rjust(2, "0")) if len(digits) >= 2 else int(digits)
    for letter, (low, high, _) in SECTIONS.items():
        if low <= division <= high:
            return letter
    return None


def parse(raw: str | int) -> Code:
    value = normalise(raw)
    if value is None:
        raise ValueError(f"not a CAEN code: {raw!r}")
    return Code(value)


def load_labels(path: str, code_column: str = "code",
                label_column: str = "label") -> dict[str, str]:
    """Load official CAEN labels from a CSV you downloaded from the source.

    Keeping the labels in a file rather than in code means you can refresh
    them without a release, and it makes the provenance of the nomenclature
    explicit to anyone reviewing your pipeline.
    """
    labels: dict[str, str] = {}
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            code = normalise(row[code_column])
            if code:
                labels[code] = row[label_column].strip()
    return labels
