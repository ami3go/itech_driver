# Typed parameterized wire fields
All 65 parameterized runtime command specs now declare ordered,
named field types (integer, finite number, nonnegative number, discrete token,
Boolean 0/1 or ON/OFF). The internal executor renders comma-separated arguments
from those values, not from caller-formatted program messages. Type, arity,
finite number and token errors fail before I/O. Existing subsystem validators
continue to enforce hardware/application bounds, qualification and compound
preconditions. No new manufacturer limit or feature claims are made.
