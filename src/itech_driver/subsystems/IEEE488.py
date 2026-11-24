from scpi_driver_core.scpi.parsers import parse_int
from typing import Optional
from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# IEEE-488 Common Commands
# -------------------------
class IEEE488:
    """Common IEEE commands: *IDN?, *RST, *OPC, *TST? etc."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def idn(self) -> str:
        return self._p.query_scpi('*IDN?')

    def reset(self):
        self._p.write_scpi('*RST')

    def clear_status(self):
        self._p.write_scpi('*CLS')

    def opc(self, wait: bool = False) -> Optional[str]:
        if wait:
            return self._p.query_scpi('*OPC?')
        self._p.write_scpi('*OPC')

    def self_test(self) -> int:
        return parse_int(self._p.query_scpi('*TST?'))

    def trigger(self):
        self._p.write_scpi('*TRG')

    def save(self, slot: int):
        self._p.write_scpi(f'*SAV {int(slot)}')

    def recall(self, slot: int):
        self._p.write_scpi(f'*RCL {int(slot)}')
