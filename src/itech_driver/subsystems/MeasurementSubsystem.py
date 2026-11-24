"""Fresh DC measurements, independent of programmed setpoints."""
from ._arrays import ascii_array_query
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

    def voltage_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return ascii_array_query(self._p, "MEAS:ARR:VOLT?", ascii_confirmed=ascii_confirmed, expected_points=expected_points)

    def current_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return ascii_array_query(self._p, "MEAS:ARR:CURR?", ascii_confirmed=ascii_confirmed, expected_points=expected_points)

    def power_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return ascii_array_query(self._p, "MEAS:ARR:POW?", ascii_confirmed=ascii_confirmed, expected_points=expected_points)
