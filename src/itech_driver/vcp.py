"""USB virtual COM connection via the common connection factory."""
from scpi_driver_core import ConfigurationError
from .instruments import ITM3900D
from .capabilities import ApplicationLimits
from .connection import ConnectionConfig


def connect_vcp(port: str, *, baudrate: int = 9600, bytesize: int = 8,
                parity: str = "N", stopbits: float = 1, timeout: int = 5000,
                termination: str = "\n", dtr: bool | None = None, rts: bool | None = None,
                require_remote: bool = False, application_limits: ApplicationLimits | None = None,
                command_termination: str | None = None, response_termination: str | None = None) -> ITM3900D:
    if not isinstance(port, str) or not port.strip():
        raise ConfigurationError("serial port is required")
    if termination not in ("\n", "\r\n"):
        raise ConfigurationError("termination must be LF or CRLF")
    config = ConnectionConfig(
        f"vcp:{port}", timeout,
        termination if command_termination is None else command_termination,
        termination if response_termination is None else response_termination,
        baudrate=baudrate, bytesize=bytesize, parity=parity, stopbits=stopbits, dtr=dtr, rts=rts)
    return ITM3900D(config.resource, connection=config, require_remote=require_remote, application_limits=application_limits)
