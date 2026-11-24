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
        self._p.write_scpi(f'BATT:SHUT:TIME {int(seconds)}')

    def shutdown_time_query(self) -> int:
        return parse_int(self._p.query_scpi('BATT:SHUT:TIME?'))

    def mode_set(self, mode: str):
        """BATT:MODE CHAR|DISCH etc."""
        self._p.write_scpi(f'BATT:MODE {mode}')

    def mode_query(self) -> str:  # Added: Missing query method
        return self._p.query_scpi('BATT:MODE?')

    def state_set(self, enable: BoolLike):  # Added: Battery state control
        self._p.write_scpi(f'BATT:STATe {1 if enable else 0}')

    def state_query(self) -> bool:  # Added: Battery state query
        return parse_bool(self._p.query_scpi('BATT:STATe?'))

