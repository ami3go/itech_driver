"""Stateful, offline-only IT-M3900D test double.

All electrical behavior and ARB state codes are synthetic fixtures, not
instrument accuracy or firmware claims. No sockets, VISA or serial access.
"""
from dataclasses import dataclass
import math
from scpi_driver_core.simulation import ScriptedScpiTransport
from scpi_driver_core.models import ScpiError
from scpi_driver_core.exceptions import ConfigurationError, TransportTimeoutError
from .command_specs import command_spec
import re


@dataclass
class SimState:
    voltage: float = 0.0
    current: float = 0.0
    output: bool = False
    tripped: bool = False
    arb: str = "IDLE"
    trigger_source: str = "BUS"
    repeats: int = 1
    remaining: int = 0
    acquisition_armed: bool = False
    acquisition_ready: bool = False


class ItechSimulator:
    def __init__(self, *, max_voltage=80., max_current=40., max_power=2000.):
        if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0
               for v in (max_voltage,max_current,max_power)):
            raise ConfigurationError("finite positive simulator envelope required")
        self.state=SimState()
        self.transport=ScriptedScpiTransport()
        self.limits={"VOLT":max_voltage,"CURR":max_current,"POW":max_power}
        self.protection={q:True for q in self.limits}
        self.thresholds=dict(self.limits)
        self._register()

    def _error(self,code,message):
        self.transport.push_error(ScpiError(code,message,f'{code},"{message}"'))

    def _value(self,cmd,maximum):
        try:
            value=float(cmd.split(maxsplit=1)[1])
            if math.isfinite(value) and 0<=value<=maximum:
                return value
        except (IndexError,ValueError):
            pass
        self._error(-222,"Data out of range")
        return None

    def _setpoint(self,cmd,q):
        v=self._value(cmd,self.limits[q])
        if v is not None:
            setattr(self.state,{"VOLT":"voltage","CURR":"current"}[q],v)

    def _set_threshold(self,cmd,q):
        v=self._value(cmd,self.limits[q])
        if v is not None:
            self.thresholds[q]=v

    def _output(self,cmd):
        self.state.output=cmd.upper().endswith("ON") or cmd.endswith(" 1")

    def _measured(self,q):
        s=self.state
        if not s.output or s.tripped:
            return 0.
        return {"VOLT":s.voltage,"CURR":s.current,"POW":s.voltage*s.current}[q]

    def _arm(self):
        self.state.arb="ARMED"
        self.state.remaining=self.state.repeats

    def _trigger(self,source):
        if self.state.arb=="ARMED" and self.state.trigger_source==source:
            self.state.arb="RUNNING"
        if self.state.acquisition_armed:
            self.state.acquisition_armed=False
            self.state.acquisition_ready=True

    def _repeat(self,cmd):
        v=self._value(cmd,10000)
        if v is not None and v.is_integer() and v>=1:
            self.state.repeats=int(v)
        elif v is not None:
            self._error(-222,"Invalid finite count")

    def tick(self):
        """Advance one synthetic repetition, not real time."""
        if self.state.arb=="RUNNING":
            self.state.remaining-=1
            if self.state.remaining<=0:
                self.state.arb="COMPLETE"
        if any(self.protection[q] and self._measured(q)>v for q,v in self.thresholds.items()):
            self.state.tripped=True

    def external_trigger(self):
        self._trigger("EXT")

    def inject_trip(self):
        self.state.tripped=True

    def fail_next_query(self,header):
        """One injected ambiguous timeout; caller explicitly reopens."""
        def failure(_):
            raise TransportTimeoutError("synthetic timeout")
        self.transport.on(header,failure)

    def _register(self):
        t=self.transport
        t.on("*IDN?","ITECH,IT-M3902D-80-40,SIMULATED,0.0")
        t.on("*CLS",lambda _: self._clear_errors())
        t.on(command_spec("OutputSubsystem.state_query").header,lambda _:str(int(self.state.output)))
        t.on_regex("^" + re.escape(command_spec("OutputSubsystem.state_set").header) + r" (ON|OFF|0|1)$",self._output)
        t.on(command_spec("StatusSubsystem.ques_condition_query").header,lambda _:str(int(self.state.tripped)))
        t.on(command_spec("SourceSubsystem.function_mode_query").header + "?","FIX")
        t.on(command_spec("SourceSubsystem.external_programming_query").header,"0")
        for q in ("VOLT","CURR"):
            name = {"VOLT": "voltage", "CURR": "current"}[q]
            query = command_spec("SourceSubsystem." + name + "_query").header
            header = command_spec("SourceSubsystem." + name + "_set").header
            t.on(query,lambda _,q=q:str(getattr(self.state,{"VOLT":"voltage","CURR":"current"}[q])))
            t.on_regex("^" + re.escape(header) + r" [^ ]+$",lambda cmd,q=q:self._setpoint(cmd,q))
            t.on(query + " MIN","0").on(query + " MAX",str(self.limits[q]))
        for q in self.limits:
            name = {"VOLT": "voltage", "CURR": "current", "POW": "programmed_power"}[q]
            protection = {"VOLT": "ovp", "CURR": "ocp", "POW": "opp"}[q]
            threshold = "opp_threshold" if protection == "opp" else protection
            t.on(command_spec("SourceSubsystem." + name + "_limit_query").header + "?",lambda _,q=q:str(self.limits[q]))
            t.on(command_spec("SourceSubsystem." + protection + "_enable_query").header,lambda _,q=q:str(int(self.protection[q])))
            t.on(command_spec("SourceSubsystem." + threshold + "_query").header,lambda _,q=q:str(self.thresholds[q]))
            t.on_regex("^" + re.escape(command_spec("SourceSubsystem." + threshold + "_set").header) + r" [^ ]+$",lambda cmd,q=q:self._set_threshold(cmd,q))
            method = {"VOLT":"voltage_query","CURR":"current_query","POW":"power_query"}[q]
            t.on(command_spec("MeasurementSubsystem." + method).header,lambda _,q=q:str(self._measured(q)))
        t.on_regex("^" + re.escape(command_spec("ArbSubsystem.count_set").header) + r" [^ ]+$",self._repeat)
        t.on_regex("^" + re.escape(command_spec("TriggerSubsystem.arb_source_set").header) + r" (BUS|EXT)$",lambda cmd:setattr(self.state,"trigger_source",cmd.split()[-1].upper()))
        t.on(command_spec("TriggerSubsystem.arb_source_query").header,lambda _:self.state.trigger_source)
        t.on("INIT:ARB",lambda _:self._arm()).on(command_spec("InitiateSubsystem.arb").header,lambda _:self._arm())
        t.on("*TRG",lambda _:self._trigger("BUS"))
        t.on("ABOR:ARB",lambda _:setattr(self.state,"arb","ABORTED"))
        t.on(command_spec("AbortSubsystem.arb").header,lambda _:setattr(self.state,"arb","ABORTED"))
        t.on(command_spec("ArbSubsystem.state_query").header,lambda _:self.state.arb)
        t.on(command_spec("TriggerSubsystem.acquire_arm").header,lambda _:self._arm_acq())

    def _clear_errors(self):
        # Core queue is drained explicitly via SYST:ERR?; no simulated reset.
        # Do not claim *CLS behavior without an explicit core queue API.
        self._error(-113,"Simulator CLS not implemented")

    def _arm_acq(self):
        self.state.acquisition_armed=True
        self.state.acquisition_ready=False
