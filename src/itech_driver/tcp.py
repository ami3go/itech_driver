"""Native ITECH SCPI socket connection (no VISA required)."""
import math
from scpi_driver_core import ConfigurationError
from scpi_driver_core.transport import TcpTransport
from .instruments import ITM3900D
from .capabilities import ApplicationLimits

DEFAULT_TCP_PORT = 30000


def connect_tcp(host: str, port: int = DEFAULT_TCP_PORT, *, timeout: int = 5000, require_remote: bool = False, application_limits: ApplicationLimits | None = None) -> ITM3900D:
    """Open an explicit endpoint, with no identification or output command."""
    if not isinstance(host, str) or not host.strip():
        raise ConfigurationError("host is required")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ConfigurationError("invalid TCP port")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ConfigurationError("timeout must be positive finite milliseconds")
    transport = TcpTransport(host, port, connect_timeout_s=timeout / 1000, timeout_s=timeout / 1000)
    return ITM3900D(f"tcp://{host}:{port}", timeout=timeout, transport=transport, require_remote=require_remote, application_limits=application_limits)
