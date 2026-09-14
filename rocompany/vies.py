"""VIES: check an EU VAT number against the European Commission's service.

VIES (VAT Information Exchange System) is the official EU service that tells
you whether a VAT number is currently valid, and, where the member state
publishes it, the registered name and address.

What VIES actually tells you, and what it does not:

* A ``valid`` answer means the number is registered for intra community
  trade **right now**. It says nothing about creditworthiness, solvency, or
  whether the company is trading.
* An ``invalid`` answer is frequently a false alarm. Many perfectly real
  companies are simply not VAT registered, and Romanian companies can be
  removed from the VAT register and later reinstated.
* Member states choose whether to disclose name and address. Some return
  ``---``. Do not build a pipeline that assumes the name will be present.
* The service goes down. Member state registries are queried live, so one
  country can be unavailable while the rest work. Treat an error as
  "unknown", never as "invalid".

Legally, a VIES check is the evidence you keep to justify zero rating an
intra community supply. Store the response and the timestamp.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

from .throttle import Backoff, RateLimiter

REST_ENDPOINT = "https://ec.europa.eu/taxation_customs/vies/rest-api/ms/{ms}/vat/{number}"
SOURCE_URL = "https://ec.europa.eu/taxation_customs/vies/"

_limiter = RateLimiter(min_interval=1.0)
_backoff = Backoff()


@dataclass(frozen=True)
class VatCheck:
    """The outcome of one VIES lookup, ready to store with its provenance."""

    country: str
    number: str
    valid: bool | None          # None means "the service could not tell us"
    name: str | None
    address: str | None
    checked_at: str
    source_url: str
    error: str | None = None

    @property
    def conclusive(self) -> bool:
        return self.valid is not None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return None if text in ("", "---") else text


def check(country: str, number: str, timeout: float = 20.0,
          user_agent: str = "rocompany/1.0 (+https://github.com/)") -> VatCheck:
    """Look up one VAT number. Blocks to respect the rate limit.

    ``country`` is the two letter member state code, ``number`` the VAT
    number without that prefix.
    """
    country = country.strip().upper()
    number = "".join(c for c in str(number) if c.isalnum()).upper()
    if number.startswith(country):
        number = number[len(country):]

    url = REST_ENDPOINT.format(ms=country, number=number)
    attempt = 0
    while True:
        attempt += 1
        _limiter.wait()
        request = urllib.request.Request(url, headers={"User-Agent": user_agent,
                                                       "Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            retryable = exc.code == 429 or 500 <= exc.code < 600
            if retryable and _backoff.should_retry(attempt):
                import time
                time.sleep(_backoff.delay(attempt))
                continue
            return VatCheck(country, number, None, None, None, _now(),
                            SOURCE_URL, error=f"http {exc.code}")
        except Exception as exc:  # network, timeout, malformed payload
            if _backoff.should_retry(attempt):
                import time
                time.sleep(_backoff.delay(attempt))
                continue
            return VatCheck(country, number, None, None, None, _now(),
                            SOURCE_URL, error=type(exc).__name__)

    return VatCheck(
        country=country,
        number=number,
        valid=bool(payload.get("isValid")),
        name=_clean(payload.get("name")),
        address=_clean(payload.get("address")),
        checked_at=_now(),
        source_url=SOURCE_URL,
        error=_clean(payload.get("userError")) if not payload.get("isValid") else None,
    )
