"""Acquisition configuration setters from guide pp.216–217.

Exact readback syntax, units and hardware-dependent limits need further
qualification. The caller supplies protocol values, not inferred rates.
"""
import math
from scpi_driver_core import ConfigurationError, UnsupportedOperationError


class SenseSubsystem:
    def __init__(self, parent):
        self._p = parent

    def acquisition_points_set(self, points: int):
        if type(points) is not int or points <= 0:
            raise ConfigurationError("acquisition point count must be a positive integer")
        self._p.write_scpi(f"SENS:ACQ:POIN {points}")

    def acquisition_offset_set(self, points: int):
        if type(points) is not int:
            raise ConfigurationError("acquisition offset must be integral points")
        self._p.write_scpi(f"SENS:ACQ:OFFS:POIN {points}")

    def acquisition_interval_set(self, interval: float):
        if isinstance(interval, bool) or not isinstance(interval, (int,float)) or not math.isfinite(interval) or interval <= 0:
            raise ConfigurationError("acquisition interval must be finite and positive")
        self._p.write_scpi(f"SENS:ACQ:TINT {interval}")

    def acquisition_points_query(self):
        raise UnsupportedOperationError("acquisition points readback not guide-qualified")

    def acquisition_offset_query(self):
        raise UnsupportedOperationError("acquisition offset readback not guide-qualified")

    def acquisition_interval_query(self):
        raise UnsupportedOperationError("acquisition interval readback not guide-qualified")
