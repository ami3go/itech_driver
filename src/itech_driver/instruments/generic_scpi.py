"""Generic SCPI instrument for unknown or basic power supplies."""

from typing import Dict, Any, Optional
from ..base import BaseInstrument
from ..subsystems.SourceSubsystem import SourceSubsystem
from ..subsystems.OutputSubsystem import OutputSubsystem
from ..subsystems.SystemSubsystem import SystemSubsystem
# from ..subsystems.measurement import MeasurementSubsystem

class GenericSCPIInstrument(BaseInstrument):
    """Generic SCPI instrument for basic control of power supplies.

    This class provides a generic interface that should work with most
    SCPI-compliant power supplies, even if they're not specifically supported.
    """

    def __init__(self, resource_name: str, **kwargs):
        super().__init__(resource_name, **kwargs)

        # Add basic subsystems that work with most instruments
        self.source = SourceSubsystem(self)
        self.output = OutputSubsystem(self)
        self.system = SystemSubsystem(self)
        # self.measurement = MeasurementSubsystem(self)

        self._instrument_info = None

    def detect_capabilities(self) -> Dict[str, bool]:
        """Attempt to detect instrument capabilities.

        Returns:
            Dictionary indicating which SCPI commands are supported
        """
        capabilities = {
            'voltage_set': self._test_command('SOUR:VOLT?'),
            'current_set': self._test_command('SOUR:CURR?'),
            'voltage_measure': self._test_command('MEAS:VOLT?'),
            'current_measure': self._test_command('MEAS:CURR?'),
            'output_control': self._test_command('OUTP:STAT?'),
            'ovp': self._test_command('SOUR:VOLT:PROT?'),
            'ocp': self._test_command('SOUR:CURR:PROT?'),
        }

        return capabilities

    def _test_command(self, command: str) -> bool:
        """Test if a SCPI command is supported."""
        try:
            self.query_scpi(command)
            return True
        except:
            return False

    def get_instrument_info(self) -> Dict[str, Any]:
        """Get information about the connected instrument."""
        if self._instrument_info is None:
            try:
                idn = self.identify()
                parts = idn.split(',')

                self._instrument_info = {
                    'manufacturer': parts[0] if len(parts) > 0 else 'Unknown',
                    'model': parts[1] if len(parts) > 1 else 'Unknown',
                    'serial': parts[2] if len(parts) > 2 else 'Unknown',
                    'firmware': parts[3] if len(parts) > 3 else 'Unknown',
                    'capabilities': self.detect_capabilities(),
                    'is_identified': True
                }
            except:
                self._instrument_info = {
                    'manufacturer': 'Unknown',
                    'model': 'Generic SCPI',
                    'serial': 'Unknown',
                    'firmware': 'Unknown',
                    'capabilities': {},
                    'is_identified': False
                }

        return self._instrument_info

    def is_command_supported(self, command: str) -> bool:
        """Check if a specific SCPI command is supported."""
        return self._test_command(command)