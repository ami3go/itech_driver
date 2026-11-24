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
        return self._p.query_scpi('SYST:VERSion?')

    def error(self) -> str:
        return self._p.query_scpi('SYST:ERRor?')

    def clear(self):
        self._p.write_scpi('SYST:CLEar')

    def remote(self):
        self._p.write_scpi('SYST:REMote')

    def local(self):
        self._p.write_scpi('SYST:LOCal')

    def beeper_immediate(self):
        self._p.write_scpi('SYST:BEEPer:IMMediate')

    def beeper_state_set(self, on: BoolLike):
        if type(on) not in (bool, int) or on not in (0, 1):
            raise ConfigurationError("beeper state must be bool or 0/1")
        self._p.write_scpi(f'SYST:BEEPer:STATe {"ON" if on else "OFF"}')

    def beeper_state_query(self) -> bool:
        return parse_bool(self._p.query_scpi('SYST:BEEPer:STATe?'))

    def date_set(self, yyyy: int, mm: int, dd: int):
        self._p.write_scpi(f'SYST:DATE {yyyy},{mm},{dd}')

    def date_query(self) -> str:
        return self._p.query_scpi('SYST:DATE?')

    def time_set(self, hh: int, mm: int, ss: int):
        self._p.write_scpi(f'SYST:TIME {hh},{mm},{ss}')

    def time_query(self) -> str:
        return self._p.query_scpi('SYST:TIME?')

    # Communication helpers
    def comm_select(self, iface: str):
        """SYST:COMM:SEL <CPD>  e.g. 'LAN','USB','GPIB','SER'"""
        self._p.write_scpi(f'SYST:COMMunicate:SELect {iface}')

    def comm_select_query(self) -> str:
        return self._p.query_scpi('SYST:COMMunicate:SELect?')

    def comm_gpib_addr_set(self, addr: int):  # Corrected: Fixed method name from gpiB to gpib
        self._p.write_scpi(f'SYST:COMMunicate:GPIB:ADDRess {int(addr)}')

    def comm_gpib_addr_query(self) -> int:  # Corrected: Fixed method name from gpiB to gpib
        return parse_int(self._p.query_scpi('SYST:COMMunicate:GPIB:ADDRess?'))

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
        self._lan_set("SYST:COMM:LAN:IP", ip_cfg)

    def lan_ip_query(self) -> str:
        return self._lan_query("SYST:COMM:LAN:IP")

    def lan_subnet_set(self, mask: str):
        self._lan_set("SYST:COMM:LAN:SMAS", mask, mask=True)

    def lan_subnet_query(self) -> str:
        return self._lan_query("SYST:COMM:LAN:SMAS", mask=True)

    def lan_gateway_set(self, gw: str):
        self._lan_set("SYST:COMM:LAN:DGAT", gw)

    def lan_gateway_query(self) -> str:
        return self._lan_query("SYST:COMM:LAN:DGAT")

    def lan_ip_mode_set(self, mode: str):
        modes = {"AUTO":"AUTO", "MAN":"MAN", "MANUAL":"MAN"}
        token = modes.get(mode.upper()) if isinstance(mode, str) else None
        if token is None:
            raise ConfigurationError("LAN IP mode must be AUTO or MANual")
        self._p.write_scpi(f"SYST:COMM:LAN:IP:MODE {token}")

    def lan_ip_mode_query(self) -> str:
        raw = self._p.query_scpi("SYST:COMM:LAN:IP:MODE?").strip().upper()
        modes = {"AUTO":"AUTO", "MAN":"MAN", "MANUAL":"MAN"}
        if raw not in modes:
            raise ResponseParseError("invalid LAN IP mode reply", raw=raw)
        return modes[raw]
