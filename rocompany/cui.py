"""Romanian fiscal identification code (CUI / CIF) validation and normalisation.

Every company registered in Romania has a CUI (Cod Unic de Inregistrare), also
written CIF when the company is registered for VAT. It is the primary key you
will join on when working with any Romanian public register.

The code carries a check digit, so roughly 9 out of 10 random numbers can be
rejected without touching the network. Validating locally before you query an
API is the difference between a pipeline that finishes and one that spends its
day being rate limited.

Know the limit of that check. Passing the checksum is necessary, not
sufficient: about one arbitrary number in ten passes by coincidence, and
the Romanian postcode 010101 is a real example of a value that validates
cleanly and is not a company. Use this module to throw away obvious rubbish
cheaply, then confirm the survivors against an actual register.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# The official control key, applied right aligned against the digits that
# precede the check digit. Published by ANAF and unchanged for decades.
CONTROL_KEY = (7, 5, 3, 2, 1, 7, 5, 3, 2)

MIN_LENGTH = 2
MAX_LENGTH = 10

_NON_DIGIT = re.compile(r"[^0-9]")


class InvalidCUI(ValueError):
    """Raised by :func:`parse` when a value cannot be a Romanian CUI."""


@dataclass(frozen=True)
class CUI:
    """A validated Romanian fiscal code."""

    value: int

    def __str__(self) -> str:
        return str(self.value)

    @property
    def vat(self) -> str:
        """The VAT form used on invoices and in VIES, e.g. ``RO43825150``.

        Note that the RO prefix means "registered for VAT", which is a
        different fact from "exists as a company". Plenty of real companies
        are not VAT registered. Never infer one from the other.
        """
        return f"RO{self.value}"


def normalise(raw: str | int) -> str:
    """Strip everything that is not a digit.

    Real world inputs arrive as ``RO 4382 5150``, ``CIF: 43825150``,
    ``43825150.0`` from a spreadsheet, and worse. Strip first, judge later.
    """
    text = str(raw).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return _NON_DIGIT.sub("", text)


def check_digit(body: str) -> int:
    """Return the expected check digit for the leading part of a CUI."""
    padded = body.rjust(len(CONTROL_KEY), "0")
    total = sum(int(d) * w for d, w in zip(padded, CONTROL_KEY))
    remainder = (total * 10) % 11
    return 0 if remainder == 10 else remainder


def is_valid(raw: str | int) -> bool:
    """True when ``raw`` is a structurally valid Romanian CUI."""
    digits = normalise(raw)
    if not digits or not MIN_LENGTH <= len(digits) <= MAX_LENGTH:
        return False
    if digits.lstrip("0") == "":
        return False
    return check_digit(digits[:-1]) == int(digits[-1])


def parse(raw: str | int) -> CUI:
    """Validate and return a :class:`CUI`, or raise :class:`InvalidCUI`."""
    digits = normalise(raw)
    if not is_valid(digits):
        raise InvalidCUI(f"not a valid Romanian CUI: {raw!r}")
    return CUI(int(digits))


def filter_valid(values) -> list[CUI]:
    """Keep only the parseable codes from a messy iterable.

    Useful as the first stage of any ingest: a supplier list of 40k "company
    IDs" routinely contains phone numbers, postcodes and order references.
    Some of those survive the checksum by chance, so this is a filter, not a
    guarantee. See the module docstring.
    """
    out: list[CUI] = []
    for value in values:
        try:
            out.append(parse(value))
        except InvalidCUI:
            continue
    return out
