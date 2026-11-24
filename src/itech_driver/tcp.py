"""Native ITECH socket connection, via the common connection factory."""
from scpi_driver_core import ConfigurationError
from .instruments import ITM3900D
from .capabilities import ApplicationLimits
from .connection import ConnectionConfig, DEFAULT_TCP_PORT
from .utils.validation import exact_integer


def connect_tcp(host: str, port: int = DEFAULT_TCP_PORT, *, timeout: int = 5000,
                require_remote: bool = False, application_limits: ApplicationLimits | None = None, require_qualified_capabilities: bool = False,
                command_termination: str = "\n", response_termination: str = "\n") -> ITM3900D:
    if not isinstance(host, str) or not host.strip() or any(c in host for c in "/?#@"):
        raise ConfigurationError("host is required")
    exact_integer(port, minimum=1, maximum=65535, name="port")
    authority = f"[{host}]" if ":" in host and not host.startswith("[") else host
    config = ConnectionConfig(f"tcp://{authority}:{port}", timeout, command_termination, response_termination)
    return ITM3900D(config.resource, connection=config, require_remote=require_remote, application_limits=application_limits, require_qualified_capabilities=require_qualified_capabilities)
