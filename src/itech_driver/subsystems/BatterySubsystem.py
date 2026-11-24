from ..command_specs import execute, execute_parameterized, command_spec
import math
from scpi_driver_core import ConfigurationError, ResponseParseError, UnsupportedOperationError
from scpi_driver_core.scpi.parsers import parse_float
from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# Battery Subsystem (BATTery)
# -------------------------
class BatterySubsystem:
    """Battery-test configuration and mode selection; not a battery emulator.

    Execution, state and physical cutoff behavior are not qualified.
    """
    simulation_supported = False
    execution_supported = False
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def charge_voltage_set(self, volts: Number):
        execute_parameterized(self._p, "BatterySubsystem.charge_voltage_set", f'{volts}')

    def charge_voltage_query(self) -> float:
        return execute(self._p, "BatterySubsystem.charge_voltage_query")

    def charge_current_set(self, amps: Number):
        execute_parameterized(self._p, "BatterySubsystem.charge_current_set", f'{amps}')

    def charge_current_query(self) -> float:
        return execute(self._p, "BatterySubsystem.charge_current_query")

    def shutdown_voltage_set(self, volts: Number):
        execute_parameterized(self._p, "BatterySubsystem.shutdown_voltage_set", f'{volts}')

    def shutdown_voltage_query(self) -> float:
        return execute(self._p, "BatterySubsystem.shutdown_voltage_query")

    def shutdown_current_set(self, amps: Number):
        execute_parameterized(self._p, "BatterySubsystem.shutdown_current_set", f'{amps}')

    def shutdown_current_query(self) -> float:
        return execute(self._p, "BatterySubsystem.shutdown_current_query")

    def shutdown_capacity_set(self, ah: Number):
        execute_parameterized(self._p, "BatterySubsystem.shutdown_capacity_set", f'{ah}')

    def shutdown_capacity_query(self) -> float:
        return execute(self._p, "BatterySubsystem.shutdown_capacity_query")

    def shutdown_time_set(self, seconds: Number):
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
            raise ConfigurationError("battery cutoff time must be a finite nonnegative number of seconds")
        execute_parameterized(self._p, "BatterySubsystem.shutdown_time_set", f'{seconds}')

    def shutdown_time_query(self) -> float:
        return execute(self._p, "BatterySubsystem.shutdown_time_query")

    def mode_set(self, mode: str):
        """Select battery-test function mode without starting a battery test."""
        if not isinstance(mode, str) or mode.upper() not in ("BATT", "BATTERY"):
            raise ConfigurationError("battery mode must be BATT; use source.function_mode_set for other modes")
        execute(self._p, "BatterySubsystem.mode_set")

    def mode_query(self) -> str:
        """Read the instrument's source function mode, not battery execution state."""
        raw = execute(self._p, "BatterySubsystem.mode_query").strip().upper()
        modes = {"FIX":"FIX", "FIXED":"FIX", "LIST":"LIST", "BATT":"BATT", "BATTERY":"BATT"}
        if raw not in modes:
            raise ResponseParseError("invalid source function mode", raw=raw)
        return modes[raw]

    def state_set(self, enable: BoolLike):
        raise UnsupportedOperationError("battery execution procedure is not yet qualified; no implicit start/stop")

    def state_query(self) -> bool:
        raise UnsupportedOperationError("battery execution status is not yet qualified")
