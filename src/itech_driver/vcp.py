"""USB virtual COM connection using the shared serial transport."""
import math
from scpi_driver_core import ConfigurationError
from scpi_driver_core.transport import SerialTransport
from .instruments import ITM3900D
from .capabilities import ApplicationLimits


def connect_vcp(port: str, *, baudrate: int = 9600, bytesize: int = 8,
                parity: str = "N", stopbits: float = 1, timeout: int = 5000,
                termination: str = "\n", dtr: bool | None = None,
                rts: bool | None = None, require_remote: bool = False, application_limits: ApplicationLimits | None = None) -> ITM3900D:
    """Open an explicitly selected USB VCP; serial settings must match the device."""
    if not isinstance(port, str) or not port.strip():
        raise ConfigurationError("serial port is required")
    if type(baudrate) is not int or baudrate <= 0:
        raise ConfigurationError("baudrate must be a positive integer")
    if type(bytesize) is not int or bytesize not in (5, 6, 7, 8):
        raise ConfigurationError("bytesize must be 5, 6, 7 or 8")
    if not isinstance(parity, str) or parity.upper() not in ("N", "E", "O"):
        raise ConfigurationError("parity must be N, E or O")
    if isinstance(stopbits, bool) or stopbits not in (1, 2):
        raise ConfigurationError("stopbits must be 1 or 2")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ConfigurationError("timeout must be finite positive milliseconds")
    if termination not in ("\n", "\r\n"):
        raise ConfigurationError("termination must be LF or CRLF")
    transport = SerialTransport(port, baudrate=baudrate, bytesize=bytesize,
                                parity=parity, stopbits=stopbits, timeout_s=timeout / 1000,
                                write_timeout_s=timeout / 1000, dtr=dtr, rts=rts)
    return ITM3900D(f"vcp:{port}", timeout=timeout, termination=termination, transport=transport, require_remote=require_remote, application_limits=application_limits)
