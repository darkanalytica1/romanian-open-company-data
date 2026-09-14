"""Normalising and matching Romanian company names.

Joining two Romanian datasets on company name is where most integration
projects quietly fail. The same company appears as::

    S.C. ALFA COM S.R.L.
    ALFA COM SRL
    Alfa Com S.R.L.
    ALFA-COM SOCIETATE COMERCIALA CU RASPUNDERE LIMITATA
    ALFA COM S.R.L. (in insolventa)

These are one company. A naive string comparison says they are five.

Two Romanian specific traps are handled here.

**The diacritic trap.** Romanian uses s and t with a comma below
(U+0219, U+021B). For years, software shipped the Turkish cedilla forms
instead (U+015F, U+0163), because early code pages did not separate them.
Public registers contain both, sometimes in the same file. Any matcher that
folds only one of the two pairs will silently miss matches.

**The legal form trap.** The legal form is not part of the company's identity
for matching purposes, but it is also not safely ignorable: SRL and SA are
different entities that may share a trading name. Strip the form for
comparison, but keep it as a separate field and treat a form mismatch as a
warning rather than a match.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

#: Romanian comma below characters and the Turkish cedilla look alikes that
#: legacy systems used in their place. Both must fold to plain ASCII.
DIACRITIC_MAP = str.maketrans(
    {
        "ă": "a", "â": "a", "î": "i", "ș": "s", "ț": "t",
        "ş": "s", "ţ": "t",  # cedilla variants, very common in older exports
        "Ă": "A", "Â": "A", "Î": "I", "Ș": "S", "Ț": "T",
        "Ş": "S", "Ţ": "T",
    }
)

#: Legal forms, longest first so that the expanded wording is stripped before
#: the abbreviation it expands to.
LEGAL_FORMS = (
    "SOCIETATE COMERCIALA CU RASPUNDERE LIMITATA",
    "SOCIETATE PE ACTIUNI",
    "SOCIETATE IN NUME COLECTIV",
    "SOCIETATE IN COMANDITA SIMPLA",
    "SOCIETATE IN COMANDITA PE ACTIUNI",
    "INTREPRINDERE INDIVIDUALA",
    "INTREPRINDERE FAMILIALA",
    "PERSOANA FIZICA AUTORIZATA",
    "REGIE AUTONOMA",
    "SRL D", "SRL", "SA", "SNC", "SCS", "SCA", "PFA", "RA", "II", "IF",
)

#: Status suffixes that registers append to the name. They describe the
#: company's situation, not its identity, so they are stripped for matching
#: but are worth capturing separately: they are a strong commercial signal.
STATUS_MARKERS = (
    "IN INSOLVENTA", "IN REORGANIZARE JUDICIARA", "IN FALIMENT",
    "IN LICHIDARE", "IN DIZOLVARE", "RADIATA",
)

#: Dotted abbreviations such as ``S.R.L.`` must be collapsed to ``SRL``
#: BEFORE punctuation is stripped, otherwise the legal form disintegrates
#: into the three separate tokens S, R and L and can no longer be matched.
_DOTTED = re.compile(r"\b(?:[A-Z]\.){2,}")
_PREFIX = re.compile(r"^\s*S\s*C\s+")                   # the ornamental "S.C."
_PUNCT = re.compile(r"[^A-Z0-9 ]+")
_SPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class ParsedName:
    """A company name split into the parts that matter for matching."""

    raw: str
    core: str
    legal_form: str | None
    status: str | None

    @property
    def is_distressed(self) -> bool:
        """True when the register flags insolvency, liquidation or similar."""
        return self.status is not None


def fold_diacritics(text: str) -> str:
    """Fold Romanian diacritics, including the cedilla look alikes, to ASCII."""
    text = text.translate(DIACRITIC_MAP)
    # Catch anything else (accented imports, stray combining marks).
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def parse(raw: str) -> ParsedName:
    """Split a raw register name into core name, legal form and status."""
    text = fold_diacritics(str(raw)).upper()
    text = text.replace("&", " AND ")
    text = _DOTTED.sub(lambda m: m.group(0).replace(".", ""), text)
    text = _PREFIX.sub("", text)

    status = None
    for marker in STATUS_MARKERS:
        pattern = re.compile(rf"\(?\b{re.escape(marker)}\b\)?")
        if pattern.search(text):
            status = marker
            text = pattern.sub(" ", text)
            break

    text = _PUNCT.sub(" ", text)
    text = _SPACE.sub(" ", text).strip()

    legal_form = None
    for form in LEGAL_FORMS:
        if text == form:
            continue  # a name that is only a legal form is not a name
        if text.endswith(" " + form):
            legal_form = form
            text = text[: -(len(form) + 1)].strip()
            break
        if text.startswith(form + " "):
            legal_form = form
            text = text[len(form) + 1 :].strip()
            break

    return ParsedName(raw=str(raw), core=_SPACE.sub(" ", text).strip(),
                      legal_form=legal_form, status=status)


def normalise(raw: str) -> str:
    """Return the comparable core of a company name."""
    return parse(raw).core


def match_key(raw: str) -> str:
    """A blocking key for candidate generation.

    Sorting the tokens makes ``ALFA COM`` and ``COM ALFA`` share a key, which
    is what you want when generating candidate pairs cheaply over millions of
    rows. Use it to narrow the field, never to decide a match on its own.
    """
    return " ".join(sorted(normalise(raw).split()))


def similarity(a: str, b: str) -> float:
    """Token overlap between two company names, from 0.0 to 1.0.

    Deliberately simple and dependency free. It is a screening score. For a
    decision you want a second, independent piece of evidence: a shared CUI,
    a shared registration number, the name present on the website, or a
    matching address. Name similarity alone will marry two unrelated firms
    that both happen to be called "TRANS EURO".
    """
    left, right = set(normalise(a).split()), set(normalise(b).split())
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def same_company(a: str, b: str, threshold: float = 0.75) -> bool:
    """Screening helper.

    A legal form mismatch costs 0.30, which is enough to push an otherwise
    identical name below the default threshold. ALFA COM SRL and ALFA COM SA
    are two different legal entities and must not be merged on name alone.
    """
    pa, pb = parse(a), parse(b)
    score = similarity(a, b)
    if pa.legal_form and pb.legal_form and pa.legal_form != pb.legal_form:
        score -= 0.30
    return score >= threshold
