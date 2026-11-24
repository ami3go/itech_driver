"""Acquisition configuration setters from guide pp.216–217.

Exact readback syntax, units and hardware-dependent limits need further
qualification. The caller supplies protocol values, not inferred rates.
"""
from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from ..utils.validation import finite_number


def _points(value):
    if type(value) is not int or value <= 0:
        raise ConfigurationError("acquisition point count must be a positive integer")
    return finite_number(value, "acquisition points")


def _offset(value):
    if type(value) is not int:
        raise ConfigurationError("acquisition offset must be integral points")
    return finite_number(value, "acquisition offset")


def _interval(value):
    if finite_number(value, "acquisition interval") <= 0:
        raise ConfigurationError("acquisition interval must be finite and positive")
    return value


class SenseSubsystem:
    def __init__(self, parent):
        self._p = parent

    def acquisition_points_set(self, points: int):
        self._p.write_scpi(f"SENS:ACQ:POIN {_points(points)}")

    def acquisition_offset_set(self, points: int):
        self._p.write_scpi(f"SENS:ACQ:OFFS:POIN {_offset(points)}")

    def acquisition_interval_set(self, interval: float):
        self._p.write_scpi(f"SENS:ACQ:TINT {_interval(interval)}")

    def acquisition_points_query(self):
        raise UnsupportedOperationError("acquisition points readback not guide-qualified")

    def acquisition_offset_query(self):
        raise UnsupportedOperationError("acquisition offset readback not guide-qualified")

    def acquisition_interval_query(self):
        raise UnsupportedOperationError("acquisition interval readback not guide-qualified")
