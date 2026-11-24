# Retry migration

The old utils.retry.retry decorator is disabled; arbitrary callable replay is
not safe. All ordinary driver writes and queries remain no-replay, including
destructive event/error-register reads. Existing exact-once fault regression
tests are retained. Only the explicit query_identity_with_retry helper permits
replay, for the non-destructive common *IDN? command, with a core RetryPolicy
and a finite elapsed budget. It refreshes the shared identity cache and never returns an authorization. Recovery is handled by ScpiSession.recover_if_faulted;
revalidate model and mode before subsequent control. No physical tests.
