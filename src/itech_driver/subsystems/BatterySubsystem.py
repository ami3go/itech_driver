import math
from scpi_driver_core import ConfigurationError, ResponseParseError, UnsupportedOperationError
from scpi_driver_core.scpi.parsers import parse_bool, parse_float, parse_int
from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# Battery Subsystem (BATTery)
# -------------------------
class BatterySubsystem:
    """Battery simulation/test commands (charge, shutdown thresholds, etc.)."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def charge_voltage_set(self, volts: Number):
        self._p.write_scpi(f'BATT:CHAR:VOLT {volts}')

    def charge_voltage_query(self) -> float:
        return parse_float(self._p.query_scpi('BATT:CHAR:VOLT?'))

    def charge_current_set(self, amps: Number):
        self._p.write_scpi(f'BATT:CHAR:CURR {amps}')

    def charge_current_query(self) -> float:
        return parse_float(self._p.query_scpi('BATT:CHAR:CURR?'))

    def shutdown_voltage_set(self, volts: Number):
        self._p.write_scpi(f'BATT:SHUT:VOLT {volts}')

    def shutdown_voltage_query(self) -> float:
        return parse_float(self._p.query_scpi('BATT:SHUT:VOLT?'))

    def shutdown_current_set(self, amps: Number):
        self._p.write_scpi(f'BATT:SHUT:CURR {amps}')

    def shutdown_current_query(self) -> float:
        return parse_float(self._p.query_scpi('BATT:SHUT:CURR?'))

    def shutdown_capacity_set(self, ah: Number):
        self._p.write_scpi(f'BATT:SHUT:CAP {ah}')

    def shutdown_capacity_query(self) -> float:
        return parse_float(self._p.query_scpi('BATT:SHUT:CAP?'))

    def shutdown_time_set(self, seconds: Number):
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
            raise ConfigurationError("battery cutoff time must be a finite nonnegative number of seconds")
        self._p.write_scpi(f'BATT:SHUT:TIME {seconds}')

    def shutdown_time_query(self) -> float:
        return parse_float(self._p.query_scpi('BATT:SHUT:TIME?'))

    def mode_set(self, mode: str):
        """Select battery-test function mode without starting a battery test."""
        if not isinstance(mode, str) or mode.upper() not in ("BATT", "BATTERY"):
            raise ConfigurationError("battery mode must be BATT; use source.function_mode_set for other modes")
        self._p.write_scpi("SOUR:FUNC:MODE BATT")

    def mode_query(self) -> str:
        """Read the instrument's source function mode, not battery execution state."""
        raw = self._p.query_scpi("SOUR:FUNC:MODE?").strip().upper()
        modes = {"FIX":"FIX", "FIXED":"FIX", "LIST":"LIST", "BATT":"BATT", "BATTERY":"BATT"}
        if raw not in modes:
            raise ResponseParseError("invalid source function mode", raw=raw)
        return modes[raw]

    def state_set(self, enable: BoolLike):
        raise UnsupportedOperationError("battery execution procedure is not yet qualified; no implicit start/stop")

    def state_query(self) -> bool:
        raise UnsupportedOperationError("battery execution status is not yet qualified")
