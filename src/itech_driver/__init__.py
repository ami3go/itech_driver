"""Python driver for ITECH and other power supplies."""

from .base import BaseInstrument
from .instruments import (
    create_instrument,
    auto_detect_instrument,
    create_instrument_from_idn,
    list_available_instruments,
    register_instrument,
    INSTRUMENT_REGISTRY,
    ITM3900D,
    GenericSCPIInstrument
)

# Export common subsystems
from .subsystems.SourceSubsystem import SourceSubsystem
from .subsystems.OutputSubsystem import OutputSubsystem
from .subsystems.SystemSubsystem import SystemSubsystem
from .subsystems.IEEE488 import IEEE488
from .subsystems.StatusSubsystem import StatusSubsystem
from .subsystems.TriggerSubsystem import TriggerSubsystem
from .subsystems.ArbSubsystem import ArbSubsystem
from .subsystems.BatterySubsystem import BatterySubsystem
from .subsystems.IOConfigSubsystem import IOConfigSubsystem
from .subsystems.InitiateSubsystem import InitiateSubsystem
from .subsystems.AbortSubsystem import AbortSubsystem


from importlib.metadata import PackageNotFoundError, version as _distribution_version

try:
    __version__ = _distribution_version("itech-itm3900d-driver")
except PackageNotFoundError:
    # A bare source tree has no authoritative installed release metadata.
    __version__ = "0+unknown"
__all__ = [
    # Base classes
    'BaseInstrument',
    # Factory functions
    'create_instrument',
    'auto_detect_instrument',
    'create_instrument_from_idn',
    'list_available_instruments',
    'register_instrument',
    'INSTRUMENT_REGISTRY',

    # Instrument classes
    'ITM3900D',
    'GenericSCPIInstrument',

    # Subsystems
    'SourceSubsystem',
    'OutputSubsystem',
    'SystemSubsystem',
    'StatusSubsystem',
    'TriggerSubsystem',
    'ArbSubsystem',
    'BatterySubsystem',
    'InitiateSubsystem',
    'AbortSubsystem',
    'IOConfigSubsystem',
    'IEEE488',
]

from .tcp import connect_tcp
__all__.append('connect_tcp')

from .vcp import connect_vcp
__all__.append('connect_vcp')

from .discovery import discover_instruments
__all__.append('discover_instruments')

from .connection import ConnectionConfig
__all__.append("ConnectionConfig")

from .method_qualification import MethodQualification, MethodEvidence
__all__.extend(["MethodQualification", "MethodEvidence"])

from .arb_integer_qualification import ArbIntegerBounds, ArbIntegerQualification
__all__.extend(["ArbIntegerBounds", "ArbIntegerQualification"])
