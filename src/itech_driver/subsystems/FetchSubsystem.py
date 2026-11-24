"""Retrieve buffered data without arming or triggering a fresh acquisition.

The caller is responsible for acquisition completion and freshness. A successful
fetch alone does not establish that data belongs to the latest acquisition.
"""
from scpi_driver_core.scpi.parsers import parse_float
from ._arrays import ascii_array_query


class FetchSubsystem:
    def __init__(self, parent):
        self._p = parent

    def voltage_query(self) -> float:
        return parse_float(self._p.query_scpi("FETC:VOLT?"))

    def voltage_high_query(self) -> float:
        return parse_float(self._p.query_scpi("FETC:VOLT:HIGH?"))

    def voltage_low_query(self) -> float:
        return parse_float(self._p.query_scpi("FETC:VOLT:LOW?"))

    def voltage_max_query(self) -> float:
        return parse_float(self._p.query_scpi("FETC:VOLT:MAX?"))

    def voltage_min_query(self) -> float:
        return parse_float(self._p.query_scpi("FETC:VOLT:MIN?"))

    def current_query(self) -> float:
        return parse_float(self._p.query_scpi("FETC:CURR?"))

    def current_high_query(self) -> float:
        return parse_float(self._p.query_scpi("FETC:CURR:HIGH?"))

    def current_low_query(self) -> float:
        return parse_float(self._p.query_scpi("FETC:CURR:LOW?"))

    def current_max_query(self) -> float:
        return parse_float(self._p.query_scpi("FETC:CURR:MAX?"))

    def current_min_query(self) -> float:
        return parse_float(self._p.query_scpi("FETC:CURR:MIN?"))

    def power_query(self) -> float:
        return parse_float(self._p.query_scpi("FETC:POW?"))

    def power_max_query(self) -> float:
        return parse_float(self._p.query_scpi("FETC:POW:MAX?"))

    def power_min_query(self) -> float:
        return parse_float(self._p.query_scpi("FETC:POW:MIN?"))

    def voltage_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return ascii_array_query(self._p, "FETC:ARR:VOLT?", ascii_confirmed=ascii_confirmed, expected_points=expected_points)

    def current_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return ascii_array_query(self._p, "FETC:ARR:CURR?", ascii_confirmed=ascii_confirmed, expected_points=expected_points)

    def power_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return ascii_array_query(self._p, "FETC:ARR:POW?", ascii_confirmed=ascii_confirmed, expected_points=expected_points)
