# Legacy query delay
The optional delay is a finite nonnegative number strictly shorter than
the configured communication timeout. The delay and transaction are
serialized under the core operation lock. The deadline starts when the
lock is acquired; lock contention is not included or preempted. Remaining
time is passed to the core query, and an expired deadline before transmission
raises TimeoutError without sending the query. Ordinary zero-delay queries
retain their original behavior. This is pacing, not instrument completion;
use the documented bounded completion API when appropriate. No replay.
