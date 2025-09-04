from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# Source Subsystem (SOURce)
# -------------------------
class SourceSubsystem:
    """Source controls: mode, voltage/current setpoints, protections, etc."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def function_set(self, mode: str):
        """SOUR:FUNCtion VOLTage|CURRent"""
        self._p.write_scpi(f'SOUR:FUNC {mode}')

    def function_query(self) -> str:
        return self._p.query_scpi('SOUR:FUNC?')

    def function_mode_set(self, mode: str):
        """SOUR:FUNCtion:MODE FIXed|TRANsient etc."""
        self._p.write_scpi(f'SOUR:FUNC:MODE {mode}')

    def function_mode_query(self) -> str:
        return self._p.query_scpi('SOUR:FUNC:MODE?')

    # Voltage / Current setpoints
    def voltage_set(self, value: Number, channel: int = 1):
        self._p.write_scpi(f'SOUR{channel}:VOLT {value}')

    def voltage_query(self, channel: int = 1) -> float:
        return float(self._p.query_scpi(f'SOUR{channel}:VOLT?'))

    def current_set(self, value: Number, channel: int = 1):
        self._p.write_scpi(f'SOUR{channel}:CURR {value}')

    def current_query(self, channel: int = 1) -> float:
        return float(self._p.query_scpi(f'SOUR{channel}:CURR?'))

    # Protections
    def ovp_set(self, value: Number, channel: int = 1):
        self._p.write_scpi(f'SOUR{channel}:VOLT:PROT:LEV {value}')

    def ovp_query(self, channel: int = 1) -> float:
        return float(self._p.query_scpi(f'SOUR{channel}:VOLT:PROT:LEV?'))

    def ovp_enable(self, enable: BoolLike, channel: int = 1):
        self._p.write_scpi(f'SOUR{channel}:VOLT:PROT:STAT {1 if enable else 0}')

    def ovp_enable_query(self, channel: int = 1) -> bool:  # Added: Missing query method
        return bool(int(self._p.query_scpi(f'SOUR{channel}:VOLT:PROT:STAT?')))

    def ocp_set(self, value: Number, channel: int = 1):
        self._p.write_scpi(f'SOUR{channel}:CURR:PROT:LEV {value}')

    def ocp_query(self, channel: int = 1) -> float:
        return float(self._p.query_scpi(f'SOUR{channel}:CURR:PROT:LEV?'))

    def ocp_enable(self, enable: BoolLike, channel: int = 1):
        self._p.write_scpi(f'SOUR{channel}:CURR:PROT:STAT {1 if enable else 0}')

    def ocp_enable_query(self, channel: int = 1) -> bool:  # Added: Missing query method
        return bool(int(self._p.query_scpi(f'SOUR{channel}:CURR:PROT:STAT?')))

    def power_limit_set(self, value: Number, channel: int = 1):
        self._p.write_scpi(f'SOUR{channel}:POW:PROT:LEV {value}')

    def power_limit_query(self, channel: int = 1) -> float:
        return float(self._p.query_scpi(f'SOUR{channel}:POW:PROT:LEV?'))

    def power_limit_enable(self, enable: BoolLike, channel: int = 1):  # Added: Missing enable method
        self._p.write_scpi(f'SOUR{channel}:POW:PROT:STAT {1 if enable else 0}')

    def power_limit_enable_query(self, channel: int = 1) -> bool:  # Added: Missing query method
        return bool(int(self._p.query_scpi(f'SOUR{channel}:POW:PROT:STAT?')))

    # Remote sense enable
    def remote_sense_set(self, enable: BoolLike, channel: int = 1):
        self._p.write_scpi(f'SOUR{channel}:REM:SENS {1 if enable else 0}')

    def remote_sense_query(self, channel: int = 1) -> bool:
        return bool(int(self._p.query_scpi(f'SOUR{channel}:REM:SENS?')))

    # Advanced: transient / dynamic function interface
    def transient_mode_set(self, mode: str):
        self._p.write_scpi(f'SOUR:FUNC:MODE {mode}')

    def transient_mode_query(self) -> str:
        return self._p.query_scpi('SOUR:FUNC:MODE?')