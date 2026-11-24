from ..command_specs import execute, execute_parameterized, command_spec
import ipaddress
from scpi_driver_core import ConfigurationError, ResponseParseError, UnsupportedOperationError
from scpi_driver_core.scpi.parsers import parse_bool, parse_int, quote_scpi_string
from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# System Subsystem (SYSTem)
# -------------------------
class SystemSubsystem:
    """SYSTem subsystem commands."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def preset(self):
        raise UnsupportedOperationError("use status.preset() for register preset or ieee.reset() for explicit reset")

    def version(self) -> str:
        return execute(self._p, "SystemSubsystem.version")

    def error(self) -> str:
        return execute(self._p, "SystemSubsystem.error")

    def clear(self):
        execute(self._p, "SystemSubsystem.clear")

    def remote(self):
        execute(self._p, "SystemSubsystem.remote")

    def local(self):
        execute(self._p, "SystemSubsystem.local")

    def beeper_immediate(self):
        execute(self._p, "SystemSubsystem.beeper_immediate")

    def beeper_state_set(self, on: BoolLike):
        if type(on) not in (bool, int) or on not in (0, 1):
            raise ConfigurationError("beeper state must be bool or 0/1")
        execute_parameterized(self._p, "SystemSubsystem.beeper_state_set", on)

    def beeper_state_query(self) -> bool:
        return execute(self._p, "SystemSubsystem.beeper_state_query")

    def date_set(self, yyyy: int, mm: int, dd: int):
        execute_parameterized(self._p, "SystemSubsystem.date_set", yyyy, mm, dd)

    def date_query(self) -> str:
        return execute(self._p, "SystemSubsystem.date_query")

    def time_set(self, hh: int, mm: int, ss: int):
        execute_parameterized(self._p, "SystemSubsystem.time_set", hh, mm, ss)

    def time_query(self) -> str:
        return execute(self._p, "SystemSubsystem.time_query")

    # Communication helpers
    def comm_select(self, iface: str):
        """SYST:COMM:SEL <CPD>  e.g. 'LAN','USB','GPIB','SER'"""
        execute_parameterized(self._p, "SystemSubsystem.comm_select", iface)

    def comm_select_query(self) -> str:
        return execute(self._p, "SystemSubsystem.comm_select_query")

    def comm_gpib_addr_set(self, addr: int):  # Corrected: Fixed method name from gpiB to gpib
        execute_parameterized(self._p, "SystemSubsystem.comm_gpib_addr_set", addr)

    def comm_gpib_addr_query(self) -> int:  # Corrected: Fixed method name from gpiB to gpib
        return execute(self._p, "SystemSubsystem.comm_gpib_addr_query")

    @staticmethod
    def _ipv4(value: str, *, mask: bool = False) -> str:
        if not isinstance(value, str):
            raise ConfigurationError("LAN configuration requires an IPv4 string")
        try:
            address = str(ipaddress.IPv4Address(value))
            if mask:
                bits = f"{int(ipaddress.IPv4Address(address)):032b}"
                if "01" in bits:
                    raise ValueError("noncontiguous subnet mask")
            return address
        except ValueError as exc:
            raise ConfigurationError(f"invalid IPv4 configuration: {value!r}") from exc

    def _lan_set(self, header: str, value: str, *, mask: bool = False):
        address = self._ipv4(value, mask=mask)
        self._p.write_scpi(f"{header} {quote_scpi_string(address)}")

    def _lan_query(self, header: str, *, mask: bool = False) -> str:
        raw = self._p.query_scpi(f"{header}?").strip()
        value = raw[1:-1] if raw.startswith('"') and raw.endswith('"') else raw
        try:
            return self._ipv4(value, mask=mask)
        except ConfigurationError as exc:
            raise ResponseParseError("invalid LAN configuration reply", raw=raw) from exc

    def lan_ip_set(self, ip_cfg: str):
        """Set IPv4 address explicitly; changing network settings may disconnect."""
        self._lan_set(command_spec("SystemSubsystem.lan_ip_set").header, ip_cfg)

    def lan_ip_query(self) -> str:
        return self._lan_query(command_spec("SystemSubsystem.lan_ip_query").header)

    def lan_subnet_set(self, mask: str):
        self._lan_set(command_spec("SystemSubsystem.lan_subnet_set").header, mask, mask=True)

    def lan_subnet_query(self) -> str:
        return self._lan_query(command_spec("SystemSubsystem.lan_subnet_query").header, mask=True)

    def lan_gateway_set(self, gw: str):
        self._lan_set(command_spec("SystemSubsystem.lan_gateway_set").header, gw)

    def lan_gateway_query(self) -> str:
        return self._lan_query(command_spec("SystemSubsystem.lan_gateway_query").header)

    def lan_ip_mode_set(self, mode: str):
        modes = {"AUTO":"AUTO", "MAN":"MAN", "MANUAL":"MAN"}
        token = modes.get(mode.upper()) if isinstance(mode, str) else None
        if token is None:
            raise ConfigurationError("LAN IP mode must be AUTO or MANual")
        execute_parameterized(self._p, "SystemSubsystem.lan_ip_mode_set", token)

    def lan_ip_mode_query(self) -> str:
        raw = execute(self._p, "SystemSubsystem.lan_ip_mode_query").strip().upper()
        modes = {"AUTO":"AUTO", "MAN":"MAN", "MANUAL":"MAN"}
        if raw not in modes:
            raise ResponseParseError("invalid LAN IP mode reply", raw=raw)
        return modes[raw]
