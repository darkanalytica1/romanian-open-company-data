"""IBAN validation, with the Romanian specifics.

A Romanian IBAN is 24 characters: ``RO`` + 2 check digits + 4 letter bank
code + 16 alphanumeric account characters. The check digits are the standard
ISO 13616 mod 97 construction, so a typo is caught locally.

Two warnings that matter commercially.

A valid IBAN is **not** proof that an account exists, that it belongs to the
company you think it does, or that it is still open. It proves only that the
string is well formed. Payment fraud very often uses a structurally perfect
IBAN.

Bank account numbers are business confidential. If you collect them, treat
them as sensitive: restrict access, never publish them on a public profile
or in an export, and log every read.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

RO_LENGTH = 24

#: Length of a valid IBAN per country, for the countries you meet most often
#: in Romanian trade. The full table is published by SWIFT and changes when
#: new countries join, so load it from source in production.
IBAN_LENGTHS = {
    "AT": 20, "BE": 16, "BG": 22, "CH": 21, "CY": 28, "CZ": 24, "DE": 22,
    "DK": 18, "EE": 20, "ES": 24, "FI": 18, "FR": 27, "GB": 22, "GR": 27,
    "HR": 21, "HU": 28, "IE": 22, "IT": 27, "LT": 20, "LU": 20, "LV": 21,
    "MT": 31, "NL": 18, "PL": 28, "PT": 25, "RO": 24, "SE": 24, "SI": 19,
    "SK": 24, "TR": 26,
}

_CLEAN = re.compile(r"[^A-Z0-9]")


@dataclass(frozen=True)
class IBAN:
    """A structurally valid IBAN."""

    value: str

    @property
    def country(self) -> str:
        return self.value[:2]

    @property
    def bank_code(self) -> str:
        """The four letter bank identifier. Romanian IBANs only."""
        if self.country != "RO":
            raise ValueError("bank_code is defined here for Romanian IBANs only")
        return self.value[4:8]

    def formatted(self) -> str:
        """Grouped into fours, the way humans read and check them."""
        return " ".join(self.value[i : i + 4] for i in range(0, len(self.value), 4))


def normalise(raw: str) -> str:
    """Upper case and remove spaces, dots and dashes."""
    return _CLEAN.sub("", str(raw).upper())


def _mod97(value: str) -> int:
    rearranged = value[4:] + value[:4]
    digits = "".join(
        str(ord(c) - 55) if c.isalpha() else c for c in rearranged
    )
    # Chunked to avoid building one enormous integer.
    remainder = 0
    for i in range(0, len(digits), 7):
        remainder = int(str(remainder) + digits[i : i + 7]) % 97
    return remainder


def is_valid(raw: str) -> bool:
    """True when ``raw`` is a well formed IBAN with correct check digits."""
    value = normalise(raw)
    if len(value) < 5 or not value[:2].isalpha() or not value[2:4].isdigit():
        return False
    expected = IBAN_LENGTHS.get(value[:2])
    if expected is not None and len(value) != expected:
        return False
    if not value.isalnum():
        return False
    return _mod97(value) == 1


def is_romanian(raw: str) -> bool:
    value = normalise(raw)
    return is_valid(value) and value.startswith("RO")


def parse(raw: str) -> IBAN:
    value = normalise(raw)
    if not is_valid(value):
        raise ValueError(f"not a valid IBAN: {raw!r}")
    return IBAN(value)
