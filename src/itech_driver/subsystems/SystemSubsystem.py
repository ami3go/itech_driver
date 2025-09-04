from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# System Subsystem (SYSTem)
# -------------------------
class SystemSubsystem:
    """SYSTem subsystem commands."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def preset(self):
        self._p.write_scpi('SYST:PRES')  # Corrected: Standard SCPI preset command

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
        self._p.write_scpi(f'SYST:BEEPer:STATe {"ON" if on else "OFF"}')

    def beeper_state_query(self) -> bool:
        response = self._p.query_scpi('SYST:BEEPer:STATe?').strip().upper()
        return response.startswith('ON') or response == '1'

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
        return int(self._p.query_scpi('SYST:COMMunicate:GPIB:ADDRess?'))

    def lan_ip_set(self, ip_cfg: str):
        """Set LAN IP configuration string (might accept 'DHCP' or '192.168.x.y')."""
        self._p.write_scpi(f'SYST:COMMunicate:LAN:IP {ip_cfg}')

    def lan_ip_query(self) -> str:
        return self._p.query_scpi('SYST:COMMunicate:LAN:IP?')

    def lan_subnet_set(self, mask: str):
        self._p.write_scpi(f'SYST:COMMunicate:LAN:SMASk {mask}')

    def lan_subnet_query(self) -> str:
        return self._p.query_scpi('SYST:COMMunicate:LAN:SMASk?')

    def lan_gateway_set(self, gw: str):
        self._p.write_scpi(f'SYST:COMMunicate:LAN:DGATeway {gw}')

    def lan_gateway_query(self) -> str:
        return self._p.query_scpi('SYST:COMMunicate:LAN:DGATeway?')
