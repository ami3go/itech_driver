"""Legacy IEEE common-command API; the shared core owns commands and parsers."""
from typing import Optional
from ..base import BaseInstrument


class IEEE488:
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def idn(self) -> str:
        return self._p.identify()

    def reset(self):
        return self._p._invoke_ieee(self._p.session.ieee488.reset, write=True, invalidate=True)

    def clear_status(self):
        return self._p._invoke_ieee(self._p.session.ieee488.clear_status, write=True)

    def opc(self, wait: bool = False) -> Optional[str]:
        ieee = self._p.session.ieee488
        if wait:
            return self._p._invoke_ieee(ieee.operation_complete_raw).strip()
        return self._p._invoke_ieee(ieee.set_operation_complete, write=True)

    def self_test(self) -> int:
        return self._p._invoke_ieee(self._p.session.ieee488.self_test).code

    def trigger(self):
        return self._p._invoke_ieee(self._p.session.ieee488.trigger, write=True)

    def save(self, slot: int):
        return self._p._invoke_ieee(self._p.session.ieee488.save, slot, write=True)

    def recall(self, slot: int):
        return self._p._invoke_ieee(self._p.session.ieee488.recall, slot, write=True, invalidate=True)
