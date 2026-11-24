from ..command_specs import execute, execute_parameterized, command_spec
import math
from scpi_driver_core import ConfigurationError
from scpi_driver_core.scpi.parsers import parse_bool
from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# Initiate Subsystem (INITiate)
# -------------------------
class InitiateSubsystem:
    """INITiate commands for ACQuire, ARB, DLOG, ELOG."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def acquire(self):
        execute(self._p, "InitiateSubsystem.acquire")

    def arb(self):
        execute(self._p, "InitiateSubsystem.arb")

    def continuous_arb_set(self, enable: BoolLike):
        execute_parameterized(self._p, "InitiateSubsystem.continuous_arb_set", enable)

    def continuous_arb_query(self) -> bool:  # Added: Missing query method
        return execute(self._p, "InitiateSubsystem.continuous_arb_query")

    def continuous_acq_set(self, enable: BoolLike):
        execute_parameterized(self._p, "InitiateSubsystem.continuous_acq_set", enable)

    def continuous_acq_query(self) -> bool:  # Added: Missing query method
        return execute(self._p, "InitiateSubsystem.continuous_acq_query")

    def dlog(self, *, storage_confirmed: bool = False,
             seconds_since_previous_end: float | None = None,
             no_previous_recording_confirmed: bool = False):
        """Start DLOG after explicit confirmation of external prerequisites.

        No guide-qualified query for USB storage or recording completion is
        available yet. These arguments are operator/caller attestations, not
        instrument readback. See guide p.108.
        """
        if storage_confirmed is not True:
            raise ConfigurationError("confirm USB recording storage and compatible connection")
        if no_previous_recording_confirmed is True:
            if seconds_since_previous_end is not None:
                raise ConfigurationError("conflicting DLOG history confirmations")
        else:
            elapsed = seconds_since_previous_end
            if isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed < 5:
                raise ConfigurationError("confirm previous recording ended at least 5 seconds ago")
        execute(self._p, "InitiateSubsystem.dlog")

    def elog(self):
        execute(self._p, "InitiateSubsystem.elog")

