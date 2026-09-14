"""EORI: validate a customs registration number with the European Commission.

An EORI number (Economic Operators Registration and Identification) is what a
business needs to move goods across the EU customs border. For a Romanian
company it is normally the letters ``RO`` followed by the CUI.

Why it is interesting commercially: an EORI registration is a declaration of
intent to trade across a customs border. It is one of the few genuinely
binary, officially published signals that a small company is an importer or
exporter. Companies do not register for one speculatively.

Why it needs care: the register tells you the number is valid, not that the
company is actively shipping, and the name and address are only published
when the operator has consented. A missing name is a consent choice, not an
error, and you must not treat the absence as a data quality problem to be
"fixed" from another source without a lawful basis.

The endpoint is a SOAP service. It is parsed here with the standard library
so the module has no dependencies.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from xml.etree import ElementTree

from .throttle import Backoff, RateLimiter

ENDPOINT = ("https://ec.europa.eu/taxation_customs/dds2/eos/validation/"
            "services/validation")
SOURCE_URL = "https://ec.europa.eu/taxation_customs/dds2/eos/eori_home.jsp"

_ENVELOPE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
    "<soap:Body>"
    '<ns:validateEORI xmlns:ns="http://eori.ws.eos.dds.s/">'
    "<ns:eori>{eori}</ns:eori>"
    "</ns:validateEORI>"
    "</soap:Body></soap:Envelope>"
)

_limiter = RateLimiter(min_interval=1.5)
_backoff = Backoff()


@dataclass(frozen=True)
class EoriCheck:
    """One EORI validation result with the provenance you must keep."""

    eori: str
    valid: bool | None           # None means the service could not tell us
    status_code: int | None
    status_text: str | None
    name: str | None             # only when the operator consented to publish
    street: str | None
    postal_code: str | None
    city: str | None
    country: str | None
    checked_at: str
    source_url: str
    error: str | None = None

    @property
    def publishes_details(self) -> bool:
        """True when the operator consented to publication of their details."""
        return self.name is not None


def build_eori(cui: str | int, country: str = "RO") -> str:
    """Compose the usual EORI form for a national fiscal code."""
    digits = "".join(c for c in str(cui) if c.isdigit())
    return f"{country.upper()}{digits}"


def _text(node, tag: str) -> str | None:
    found = node.find(f".//{tag}")
    if found is None or found.text is None:
        return None
    value = " ".join(found.text.split())
    return value or None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def check(eori: str, timeout: float = 30.0,
          user_agent: str = "rocompany/1.0 (+https://github.com/)") -> EoriCheck:
    """Validate one EORI number. Blocks to respect the rate limit.

    Never call this in a tight loop over a whole database. Cache the result
    and re validate on a TTL: valid registrations change rarely, so a
    quarterly refresh is usually plenty, with a shorter TTL for the ones that
    came back invalid.
    """
    eori = "".join(str(eori).split()).upper()
    body = _ENVELOPE.format(eori=eori).encode("utf-8")
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": '""',
        "User-Agent": user_agent,
    }

    attempt = 0
    while True:
        attempt += 1
        _limiter.wait()
        request = urllib.request.Request(ENDPOINT, data=body, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
            break
        except urllib.error.HTTPError as exc:
            retryable = exc.code == 429 or 500 <= exc.code < 600
            if retryable and _backoff.should_retry(attempt):
                import time
                time.sleep(_backoff.delay(attempt))
                continue
            return _failure(eori, f"http {exc.code}")
        except Exception as exc:
            if _backoff.should_retry(attempt):
                import time
                time.sleep(_backoff.delay(attempt))
                continue
            return _failure(eori, type(exc).__name__)

    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError:
        return _failure(eori, "unparseable response")

    status_raw = _text(root, "status")
    status_code = int(status_raw) if status_raw and status_raw.isdigit() else None
    status_text = _text(root, "statusDescr")

    return EoriCheck(
        eori=_text(root, "eori") or eori,
        valid=(status_code == 0) if status_code is not None else None,
        status_code=status_code,
        status_text=status_text,
        name=_text(root, "name"),
        street=_text(root, "street"),
        postal_code=_text(root, "postalCode"),
        city=_text(root, "city"),
        country=_text(root, "country"),
        checked_at=_now(),
        source_url=SOURCE_URL,
    )


def _failure(eori: str, error: str) -> EoriCheck:
    return EoriCheck(eori, None, None, None, None, None, None, None, None,
                     _now(), SOURCE_URL, error=error)
