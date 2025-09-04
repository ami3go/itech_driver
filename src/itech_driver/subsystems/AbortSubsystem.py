from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# Abort Subsystem (ABORt)
# -------------------------
class AbortSubsystem:
    """Abort commands for ACQuire and ARB."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def acquire(self):
        self._p.write_scpi('ABORt:ACQuire')

    def arb(self):
        self._p.write_scpi('ABORt:ARB')

    def dlog(self):  # Added: Missing DLOG abort
        self._p.write_scpi('ABORt:DLOG')

    def elog(self):  # Added: Missing ELOG abort
        self._p.write_scpi('ABORt:ELOG')