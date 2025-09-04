import pyvisa
import time
from typing import Union, Optional
from .exceptions import InstrumentNotFoundError, CommandError, TimeoutError
from .utils.retry import retry

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

    @retry(max_attempts=3, delay=0.1, exceptions=(CommandError, TimeoutError))
    def write_scpi(self, cmd: str):
        self._res.write(cmd)
        self.log_command(cmd, is_query=False)

    # def write_scpi(self, cmd: str) -> None:
    # """Send SCPI command with error handling."""
    #     try:
    #         self._res.write(cmd)
    #     except pyvisa.errors.VisaIOError as e:
    #         raise CommandError(f"Failed to write command '{cmd}': {e}") from e

    @retry(max_attempts=3, delay=0.1, exceptions=(CommandError, TimeoutError))
    def query_scpi(self, cmd: str, delay: float = 0.0) -> str:
        if delay:
            time.sleep(delay)
        return self._res.query(cmd).strip()

    @retry(max_attempts=3, delay=0.1, exceptions=(CommandError, TimeoutError))
    def query_binary(self, cmd: str, datatype: str = 'f', container=list):
        return self._res.query_binary_values(cmd, datatype=datatype, container=container)

    # def query_scpi(self, cmd: str, delay: float = 0.0) -> str:
    # """Send SCPI query with error handling."""
    #     if delay:
    #         time.sleep(delay)
    #     try:
    #         return self._res.query(cmd).strip()
    #     except pyvisa.errors.VisaIOError as e:
    #         if "timeout" in str(e).lower():
    #             raise TimeoutError(f"Query timeout for command '{cmd}': {e}") from e
    #         raise CommandError(f"Failed to query '{cmd}': {e}") from e

    def identify(self) -> str:
        """Identify the instrument (convenience method for ieee.idn())."""
        return self.ieee.idn()

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

    # def enable_debug(self, level: int = logging.DEBUG) -> None:
    #     """Enable debug logging for this instrument."""
    #     from .utils.ulogger import setup_logging
    #     setup_logging(level)
    #     self._debug_enabled = True
    #
    # def log_command(self, command: str, is_query: bool = False) -> None:
    #     """Log SCPI commands for debugging."""
    #     if getattr(self, '_debug_enabled', False):
    #         logger = ulogger.getLogger('itech_driver')
    #         action = "QUERY" if is_query else "WRITE"
    #         logger.debug(f"{action}: {command}")

    # from .exceptions import InstrumentNotFoundError, CommandError, TimeoutError
    #
    # class BaseInstrument:
    #     def __init__(self, resource_name: str, timeout: int = 5000,
    #                  termination: str = '\n', interface_kwargs: dict = None):
    #         try:
    #             self._rm = pyvisa.ResourceManager()
    #             self._res = self._rm.open_resource(resource_name, **(interface_kwargs or {}))
    #             self._res.timeout = timeout
    #             try:
    #                 self._res.read_termination = termination
    #                 self._res.write_termination = termination
    #             except Exception:
    #                 pass
    #         except pyvisa.errors.VisaIOError as e:
    #             raise InstrumentNotFoundError(f"Cannot connect to {resource_name}: {e}") from e
    #
    #     def write_scpi(self, cmd: str) -> None:
    #         """Send SCPI command with error handling."""
    #         try:
    #             self._res.write(cmd)
    #         except pyvisa.errors.VisaIOError as e:
    #             raise CommandError(f"Failed to write command '{cmd}': {e}") from e
    #
    #
    from .utils.retry import retry
    from .exceptions import CommandError, TimeoutError

    # class BaseInstrument:
    #     # ... existing code ...
    #
    #     @retry(max_attempts=3, delay=0.1, exceptions=(CommandError, TimeoutError))
    #     def write_scpi(self, cmd: str) -> None:
    #         """Send SCPI command with retry mechanism."""
    #         try:
    #             self._res.write(cmd)
    #         except pyvisa.errors.VisaIOError as e:
    #             raise CommandError(f"Failed to write command '{cmd}': {e}") from e
    #
    #     @retry(max_attempts=3, delay=0.1, exceptions=(CommandError, TimeoutError))
    #     def query_scpi(self, cmd: str, delay: float = 0.0) -> str:
    #         """Send SCPI query with retry mechanism."""
    #         if delay:
    #             time.sleep(delay)
    #         try:
    #             return self._res.query(cmd).strip()
    #         except pyvisa.errors.VisaIOError as e:
    #             if "timeout" in str(e).lower():
    #                 raise TimeoutError(f"Query timeout for command '{cmd}': {e}") from e
    #             raise CommandError(f"Failed to query '{cmd}': {e}") from e