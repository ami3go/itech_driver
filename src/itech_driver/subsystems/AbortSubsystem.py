from ..command_specs import execute
from scpi_driver_core import UnsupportedOperationError
from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# Abort Subsystem (ABORt)
# -------------------------
class AbortSubsystem:
    """Abort commands for ACQuire and ARB."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def acquire(self):
        execute(self._p, "AbortSubsystem.acquire")

    def arb(self):
        execute(self._p, "AbortSubsystem.arb")

    def dlog(self):
        raise UnsupportedOperationError("DLOG stop command not qualified for IT-M3900D")

    def elog(self):
        raise UnsupportedOperationError("ELOG stop command not qualified for IT-M3900D")
