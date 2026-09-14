"""Working with Romania's open company data.

A small, dependency free toolkit for the things you need in the first hour of
any project that touches Romanian company records: validating identifiers,
normalising company names so they can be joined, classifying activity codes,
and querying the official EU verification services politely.

See the README for the register by register guide to what is published,
where, and what each source is actually good for.
"""

from . import caen, cui, eori, iban, names, vies  # noqa: F401

__version__ = "1.0.0"
__all__ = ["caen", "cui", "eori", "iban", "names", "vies"]
