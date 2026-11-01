"""Bounded retry and degradation primitives."""

import time
from collections.abc import Callable


class RetryExhausted(RuntimeError):
    pass


def retry_idempotent[T](
    operation: Callable[[], T],
    *,
    attempts: int = 3,
    backoff_seconds: float = 0.05,
    transient: tuple[type[Exception], ...] = (TimeoutError, OSError),
) -> T:
    """Retry only caller-declared idempotent work with bounded backoff."""

    if attempts < 1 or attempts > 5:
        raise ValueError("attempts must be between 1 and 5")
    for attempt in range(attempts):
        try:
            return operation()
        except transient as error:
            if attempt + 1 == attempts:
                raise RetryExhausted(
                    "Transient operation exhausted retry budget"
                ) from error
            time.sleep(backoff_seconds * (2**attempt))
    raise AssertionError("unreachable")
