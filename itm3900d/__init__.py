"""PyVISA driver for ITECH IT-M3900D high-power programmable DC supplies."""

from __future__ import annotations

from .exceptions import (
    InstrumentCommandError,
    InstrumentError,
    InstrumentTimeoutError,
    ITM3900DError,
    OutputEnableConfirmationRequired,
    OutputEnableNotAllowedError,
    OutputNotSafeError,
    OutputProtectionError,
    QueryInterruptedError,
    SafetyLimitError,
    UnsupportedCommandError,
    VisaConnectionError,
)
from .instrument import ArbStep, ITM3900D
from .safety import SafetyPolicy
from .types import InstrumentErrorRecord, ScpiCommand, ScpiLogRecord, ScpiParameter, ScpiReturn

__all__ = [
    "ArbStep",
    "ITM3900D",
    "SafetyPolicy",
    "InstrumentErrorRecord",
    "ScpiCommand",
    "ScpiLogRecord",
    "ScpiParameter",
    "ScpiReturn",
    "ITM3900DError",
    "VisaConnectionError",
    "InstrumentError",
    "InstrumentCommandError",
    "UnsupportedCommandError",
    "OutputProtectionError",
    "QueryInterruptedError",
    "InstrumentTimeoutError",
    "SafetyLimitError",
    "OutputEnableNotAllowedError",
    "OutputEnableConfirmationRequired",
    "OutputNotSafeError",
]

__version__ = "0.1.0"
