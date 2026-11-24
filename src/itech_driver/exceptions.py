"""Driver-specific errors compatible with the common core hierarchy."""
from scpi_driver_core.exceptions import (
    ScpiDriverError, ScpiTimeoutError, TransportError, ConfigurationError,
)

PowerSupplyError = ScpiDriverError


class InstrumentNotFoundError(TransportError):
    """Instrument connection failed."""


class CommandError(TransportError):
    """SCPI transport operation failed."""


class TimeoutError(ScpiTimeoutError):
    """A bounded driver operation timed out."""


class ProtectionTripError(PowerSupplyError):
    """Instrument protection circuit tripped."""


class ValidationError(ConfigurationError):
    """Input validation failed."""
