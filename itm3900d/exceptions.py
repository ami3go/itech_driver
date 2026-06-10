"""Exception hierarchy for the IT-M3900D driver."""

from __future__ import annotations


class ITM3900DError(Exception):
    """Base exception for this package."""


class VisaConnectionError(ITM3900DError):
    """Raised when a VISA resource cannot be opened or used."""


class InstrumentError(ITM3900DError):
    """Raised for instrument-reported SCPI errors."""


class InstrumentCommandError(InstrumentError):
    """Raised when a SCPI command is rejected or unsupported."""


class UnsupportedCommandError(InstrumentCommandError):
    """Raised when a command key is not present in the catalog."""


class OutputProtectionError(InstrumentError):
    """Raised when output protection is tripped or cannot be cleared safely."""


class QueryInterruptedError(InstrumentError):
    """Raised for SCPI query-interrupted conditions."""


class InstrumentTimeoutError(ITM3900DError):
    """Raised for VISA/read/write timeout errors."""


class SafetyLimitError(ITM3900DError):
    """Raised when a requested output setting violates SafetyPolicy."""


class OutputEnableNotAllowedError(SafetyLimitError):
    """Raised when output enable is not permitted by policy or constructor options."""


class OutputEnableConfirmationRequired(OutputEnableNotAllowedError):
    """Raised when output_on(confirm=True) was not explicitly requested."""


class OutputNotSafeError(SafetyLimitError):
    """Raised when output cannot be verified as safe/off."""
