"""Fresh DC measurements, independent of programmed setpoints."""
from scpi_driver_core import ConfigurationError, ResponseParseError
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

    def _ascii_array_query(self, header: str, *, ascii_confirmed: bool, expected_points: int | None) -> list[float]:
        if ascii_confirmed is not True:
            raise ConfigurationError("confirm instrument ASCII data format before array query")
        if expected_points is not None and (type(expected_points) is not int or expected_points <= 0):
            raise ConfigurationError("expected_points must be a positive integer")
        raw = self._p.query_scpi(header)
        if not raw.strip() or any(not item.strip() for item in raw.split(",")):
            raise ResponseParseError("empty or incomplete measurement array", raw=raw)
        result = [parse_float(item) for item in raw.split(",")]
        if expected_points is not None and len(result) != expected_points:
            raise ResponseParseError("unexpected measurement point count", raw=raw)
        return result

    def voltage_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return self._ascii_array_query("MEAS:ARR:VOLT?", ascii_confirmed=ascii_confirmed, expected_points=expected_points)

    def current_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return self._ascii_array_query("MEAS:ARR:CURR?", ascii_confirmed=ascii_confirmed, expected_points=expected_points)

    def power_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return self._ascii_array_query("MEAS:ARR:POW?", ascii_confirmed=ascii_confirmed, expected_points=expected_points)
