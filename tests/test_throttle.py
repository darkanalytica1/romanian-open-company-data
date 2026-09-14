import time

from rocompany.throttle import Backoff, RateLimiter


def test_rate_limiter_enforces_a_gap():
    limiter = RateLimiter(min_interval=0.05, jitter=0.0)
    limiter.wait()
    start = time.monotonic()
    limiter.wait()
    assert time.monotonic() - start >= 0.05


def test_backoff_grows_and_is_capped():
    backoff = Backoff(base=2.0, cap=10.0, max_attempts=4)
    assert backoff.delay(1) == 2.0
    assert backoff.delay(2) == 4.0
    assert backoff.delay(9) == 10.0
    assert backoff.should_retry(3)
    assert not backoff.should_retry(4)
