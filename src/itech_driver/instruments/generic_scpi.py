"""Generic SCPI identification; unknown instruments have no qualified controls."""
from typing import Dict, Any
from ..base import BaseInstrument
from ..capabilities import unknown_feature_states
from scpi_driver_core.scpi.parsers import parse_identity
from ..subsystems.IEEE488 import IEEE488


class GenericSCPIInstrument(BaseInstrument):
    """Unknown model: IEEE common commands only, no device-specific capability claims."""

    def __init__(self, resource_name: str, **kwargs):
        super().__init__(resource_name, **kwargs)
        self.ieee = IEEE488(self)

    def capability_states(self):
        """Explicit immutable unknown states; performs no speculative I/O."""
        return unknown_feature_states()

    def detect_capabilities(self) -> Dict[str, bool | None]:
        """None denotes unknown, not proof of support or lack of support.

        A syntactically valid query response alone cannot establish support
        for the associated setter, particularly on an unidentified model.
        No speculative probes or error queue consumption.
        """
        return dict.fromkeys(("voltage_set", "current_set", "voltage_measure",
                              "current_measure", "output_control", "ovp", "ocp"))

    def get_instrument_info(self) -> Dict[str, Any]:
        """Read fresh identity; never reuse evidence from a previous session."""
        identity = parse_identity(self.identify())
        return {
            "manufacturer": identity.manufacturer,
            "model": identity.model,
            "serial": identity.serial_number,
            "firmware": identity.firmware_version,
            "capabilities": self.detect_capabilities(),
            "is_identified": True,
        }

    def is_command_supported(self, command: str) -> bool | None:
        """Unknown capability; do not test arbitrary commands against hardware."""
        if not isinstance(command,str) or not command.strip().endswith("?") or ";" in command:
            raise ValueError("capability checks require a single query")
        return None
