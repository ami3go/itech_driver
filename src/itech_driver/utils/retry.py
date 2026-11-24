"""Explicitly bounded replay of a known non-destructive common query.

The former arbitrary callable decorator cannot establish replay safety and
is no longer supported. Use normal driver methods for all other commands.
"""
from scpi_driver_core import ConfigurationError, UnsupportedOperationError, ScpiTimeoutError, TransportError
from scpi_driver_core.execution.retry import RetryPolicy, run_with_retry


def retry(*args, **kwargs):
    """Migration trap: never decorate an arbitrary callable with replay."""
    raise UnsupportedOperationError(
        "generic retry removed; use query_identity_with_retry for explicit *IDN? reads"
    )


def query_identity_with_retry(driver, *, policy: RetryPolicy):
    """Opt-in *IDN? only, using the core retry/recovery implementation.

    Return the fresh parsed identity's raw text. The shared session invalidates
    stale identity on every refresh and the driver invalidates remote state on
    failure. The caller must still validate model before control.
    """
    if not isinstance(policy, RetryPolicy) or type(policy.attempts) is not int or policy.attempts < 1:
        raise ConfigurationError("positive integral core RetryPolicy attempts required")
    if policy.retries and policy.max_elapsed_s is None:
        raise ConfigurationError("retry requires a finite elapsed-time budget")
    # Fixed read-only IDN refresh is the only callable classified as replayable.
    return run_with_retry(
        lambda: driver.identity_snapshot(refresh=True),
        policy=policy, retry_on=(TransportError, ScpiTimeoutError),
        before_retry=driver.session.recover_if_faulted,
    ).raw
