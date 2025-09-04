"""Custom exceptions for the power supply driver."""

class PowerSupplyError(Exception):
    """Base exception for power supply errors."""
    pass

class InstrumentNotFoundError(PowerSupplyError):
    """Raised when an instrument cannot be found or connected."""
    pass

class CommandError(PowerSupplyError):
    """Raised when a SCPI command fails."""
    pass

class TimeoutError(PowerSupplyError):
    """Raised when a operation times out."""
    pass

class ProtectionTripError(PowerSupplyError):
    """Raised when protection circuits trip."""
    pass

class ValidationError(PowerSupplyError):
    """Raised when input validation fails."""
    pass