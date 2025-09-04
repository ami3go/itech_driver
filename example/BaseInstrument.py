import pyvisa
import time
from typing import Union, Optional

Number = Union[int, float]
BoolLike = Union[bool, int]

class BaseInstrument:
    def __init__(self, resource_name: str, timeout: int = 5000, termination: str = '\n', interface_kwargs: dict = None):
        self._rm = pyvisa.ResourceManager()
        self._res = self._rm.open_resource(resource_name, **(interface_kwargs or {}))
        self._res.timeout = timeout
        try:
            self._res.read_termination = termination
            self._res.write_termination = termination
        except Exception:
            pass
        self._p = self  # used by subsystems

        # Subsystems are attached by __init__.py
        self.system = None
        self.source = None
        self.output = None
        self.status = None
        self.trigger = None
        self.arb = None
        self.battery = None
        self.initiate = None
        self.abort = None
        self.io = None
        self.ieee = None

    def write_scpi(self, cmd: str):
        self._res.write(cmd)

    def query_scpi(self, cmd: str, delay: float = 0.0) -> str:
        if delay:
            time.sleep(delay)
        return self._res.query(cmd).strip()

    def query_binary(self, cmd: str, datatype: str = 'f', container=list):
        return self._res.query_binary_values(cmd, datatype=datatype, container=container)

    def close(self):
        try:
            self._res.close()
        except Exception:
            pass
        try:
            self._rm.close()
        except Exception:
            pass

    @property
    def visa(self):
        return self._res