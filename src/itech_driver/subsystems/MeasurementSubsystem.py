"""Fresh DC measurements, independent of programmed setpoints."""
from scpi_driver_core.scpi.parsers import parse_float


class MeasurementSubsystem:
    def __init__(self, parent):
        self._p = parent

    def voltage_query(self) -> float:
        return parse_float(self._p.query_scpi("MEAS:VOLT?"))

    def voltage_high_query(self) -> float:
        return parse_float(self._p.query_scpi("MEAS:VOLT:HIGH?"))

    def voltage_low_query(self) -> float:
        return parse_float(self._p.query_scpi("MEAS:VOLT:LOW?"))

    def voltage_max_query(self) -> float:
        return parse_float(self._p.query_scpi("MEAS:VOLT:MAX?"))

    def voltage_min_query(self) -> float:
        return parse_float(self._p.query_scpi("MEAS:VOLT:MIN?"))

    def current_query(self) -> float:
        return parse_float(self._p.query_scpi("MEAS:CURR?"))

    def current_high_query(self) -> float:
        return parse_float(self._p.query_scpi("MEAS:CURR:HIGH?"))

    def current_low_query(self) -> float:
        return parse_float(self._p.query_scpi("MEAS:CURR:LOW?"))

    def current_max_query(self) -> float:
        return parse_float(self._p.query_scpi("MEAS:CURR:MAX?"))

    def current_min_query(self) -> float:
        return parse_float(self._p.query_scpi("MEAS:CURR:MIN?"))

    def power_query(self) -> float:
        return parse_float(self._p.query_scpi("MEAS:POW?"))

    def power_max_query(self) -> float:
        return parse_float(self._p.query_scpi("MEAS:POW:MAX?"))

    def power_min_query(self) -> float:
        return parse_float(self._p.query_scpi("MEAS:POW:MIN?"))
