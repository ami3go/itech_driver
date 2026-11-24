# Explicit validation bounds

The legacy utility functions retain their names and positional arguments, but
`validate_voltage(value)`, `validate_current(value)`, and
`validate_channel(channel)` now raise ValidationError without explicit bounds
or channel count. The previous arbitrary 60 V, 10 A and two-channel defaults
were not instrument capabilities. Pass a verified model/command range and
model channel count, or use the typed driver setters with effective live
bounds. ValidationError remains a ConfigurationError subclass. Nonfinite,
overflowing, boolean numeric, fractional channel and unknown bounds are
rejected before I/O. No new SCPI commands.
