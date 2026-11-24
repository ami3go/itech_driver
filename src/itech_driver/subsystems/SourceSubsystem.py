import math
from scpi_driver_core import ConfigurationError
from scpi_driver_core.scpi.parsers import parse_bool, parse_float
from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# Source Subsystem (SOURce)
# -------------------------
class SourceSubsystem:
    """Source controls: mode, voltage/current setpoints, protections, etc."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def function_set(self, mode: str):
        """SOUR:FUNCtion VOLTage|CURRent"""
        self._p.write_scpi(f'SOUR:FUNC {mode}')

    def function_query(self) -> str:
        return self._p.query_scpi('SOUR:FUNC?')

    def function_mode_set(self, mode: str):
        """SOUR:FUNCtion:MODE FIXed|TRANsient etc."""
        self._p.write_scpi(f'SOUR:FUNC:MODE {mode}')

    def function_mode_query(self) -> str:
        return self._p.query_scpi('SOUR:FUNC:MODE?')

    @staticmethod
    def _check_channel(channel: int) -> None:
        if type(channel) is not int or channel != 1:
            raise ConfigurationError("IT-M3900D source uses a single unnumbered output; channel must be 1")

    @staticmethod
    def _check_setpoint(value: Number) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ConfigurationError("setpoint must be a finite real number")
        if value < 0:
            raise ConfigurationError("setpoint must be nonnegative")

    # Voltage / Current setpoints
    def voltage_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._check_setpoint(value)
        self._p.write_scpi(f'SOUR:VOLT {value}')

    def voltage_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return parse_float(self._p.query_scpi('SOUR:VOLT?'))

    def current_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._check_setpoint(value)
        self._p.write_scpi(f'SOUR:CURR {value}')

    def current_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return parse_float(self._p.query_scpi('SOUR:CURR?'))

    # Protections
    def ovp_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._check_setpoint(value)
        self._p.write_scpi(f'SOUR:VOLT:OVER:PROT:LEV {value}')

    def ovp_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return parse_float(self._p.query_scpi(f'SOUR:VOLT:OVER:PROT:LEV?'))

    def ovp_enable(self, enable: BoolLike, channel: int = 1):
        self._check_channel(channel)
        if type(enable) not in (bool, int) or enable not in (0, 1):
            raise ConfigurationError("protection enable must be bool or 0/1")
        self._p.write_scpi(f'SOUR:VOLT:OVER:PROT:STAT {1 if enable else 0}')

    def ovp_enable_query(self, channel: int = 1) -> bool:  # Added: Missing query method
        self._check_channel(channel)
        return parse_bool(self._p.query_scpi(f'SOUR:VOLT:OVER:PROT:STAT?'))

    def ocp_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._check_setpoint(value)
        self._p.write_scpi(f'SOUR:CURR:OVER:PROT:LEV {value}')

    def ocp_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return parse_float(self._p.query_scpi(f'SOUR:CURR:OVER:PROT:LEV?'))

    def ocp_enable(self, enable: BoolLike, channel: int = 1):
        self._check_channel(channel)
        if type(enable) not in (bool, int) or enable not in (0, 1):
            raise ConfigurationError("protection enable must be bool or 0/1")
        self._p.write_scpi(f'SOUR:CURR:OVER:PROT:STAT {1 if enable else 0}')

    def ocp_enable_query(self, channel: int = 1) -> bool:  # Added: Missing query method
        self._check_channel(channel)
        return parse_bool(self._p.query_scpi(f'SOUR:CURR:OVER:PROT:STAT?'))

    def power_limit_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._check_setpoint(value)
        self._p.write_scpi(f'SOUR:POW:OVER:PROT:LEV {value}')

    def power_limit_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return parse_float(self._p.query_scpi(f'SOUR:POW:OVER:PROT:LEV?'))

    def power_limit_enable(self, enable: BoolLike, channel: int = 1):  # Added: Missing enable method
        self._check_channel(channel)
        if type(enable) not in (bool, int) or enable not in (0, 1):
            raise ConfigurationError("protection enable must be bool or 0/1")
        self._p.write_scpi(f'SOUR:POW:OVER:PROT:STAT {1 if enable else 0}')

    def power_limit_enable_query(self, channel: int = 1) -> bool:  # Added: Missing query method
        self._check_channel(channel)
        return parse_bool(self._p.query_scpi(f'SOUR:POW:OVER:PROT:STAT?'))

    # Remote sense enable
    def remote_sense_set(self, enable: BoolLike, channel: int = 1):
        self._p.write_scpi(f'SOUR{channel}:REM:SENS {1 if enable else 0}')

    def remote_sense_query(self, channel: int = 1) -> bool:
        return parse_bool(self._p.query_scpi(f'SOUR{channel}:REM:SENS?'))

    # Advanced: transient / dynamic function interface
    def transient_mode_set(self, mode: str):
        self._p.write_scpi(f'SOUR:FUNC:MODE {mode}')

    def transient_mode_query(self) -> str:
        return self._p.query_scpi('SOUR:FUNC:MODE?')
