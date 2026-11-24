"""Explicitly bounded replay of a known non-destructive common query.

The former arbitrary callable decorator cannot establish replay safety and
is no longer supported. Use normal driver methods for all other commands.
"""
from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from scpi_driver_core.execution.retry import RetryPolicy
from scpi_driver_core.transport import ReplayPolicy


def retry(*args, **kwargs):
    """Migration trap: never decorate an arbitrary callable with replay."""
    raise UnsupportedOperationError(
        "generic retry removed; use query_identity_with_retry for explicit *IDN? reads"
    )


def query_identity_with_retry(driver, *, policy: RetryPolicy):
    """Opt-in *IDN? only, using the core retry/recovery implementation.

    This returns raw identity text, not a validated model or cached identity.
    Callers must revalidate identity and remote authorization after recovery.
    """
    if not isinstance(policy, RetryPolicy) or type(policy.attempts) is not int or policy.attempts < 1:
        raise ConfigurationError("positive integral core RetryPolicy attempts required")
    if policy.retries and policy.max_elapsed_s is None:
        raise ConfigurationError("retry requires a finite elapsed-time budget")
    # The core owns bounded retry and transport recovery. A raw IDN reply
    # never authorizes a setting write or an output operation.
    return driver.session.client.query(
        "*IDN?", replay_policy=ReplayPolicy.SAFE, retry_policy=policy,
        before_retry=driver.session.recover_if_faulted,
    )
