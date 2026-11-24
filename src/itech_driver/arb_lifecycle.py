"""Bounded ARB observation and cancellation.

Actual device status codes must come from qualified model/firmware evidence.
Synthetic simulation tokens must not be reused as hardware mappings.
"""
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping
from scpi_driver_core import ConfigurationError, ScpiDriverError, SafetyGuardError
from .subsystems.ArbSubsystem import _repeat


class ArbState(str,Enum):
    CONFIGURED="configured"
    ARMED="armed"
    RUNNING="running"
    COMPLETE="complete"
    ABORTED="aborted"
    ERROR="error"
    UNKNOWN="unknown"


@dataclass(frozen=True)
class ArbEvidence:
    state: ArbState
    raw_status: str | None
    reason: str
    polls: int = 0


class ArbLifecycle:
    """Explicit arming/triggering with bounded polling and generation binding.

    This helper does not configure or enable output, nor assert output OFF
    after completion/abort. Each individual I/O uses the session's timeout.
    """
    def __init__(self,driver,*,status_map: Mapping[str,ArbState],mapping_evidence: str):
        if not isinstance(mapping_evidence,str) or not mapping_evidence.strip():
            raise ConfigurationError("status mapping provenance required")
        if not status_map or any(not isinstance(k,str) or not k.strip() or not isinstance(v,ArbState)
                                 for k,v in status_map.items()):
            raise ConfigurationError("explicit qualified status map required")
        self.driver=driver
        self.status_map=MappingProxyType(dict(status_map))
        self.mapping_evidence=mapping_evidence
        self._generation=None
        self._trigger_source=None
        self._state=ArbState.UNKNOWN
        self._trigger_attempted=False
        self._abort_attempted=False

    def _live(self):
        return (self.driver.session.is_connected and
                self.driver.session.generation==self._generation)

    def observe(self):
        with self.driver.session.operation_lock():
            if not self._live():
                return ArbEvidence(ArbState.UNKNOWN,None,"session changed or disconnected")
            try:
                raw=self.driver.arb.state_query()
            except ScpiDriverError as exc:
                self._state=ArbState.UNKNOWN
                return ArbEvidence(self._state,None,str(exc))
            self._state=self.status_map.get(raw,ArbState.UNKNOWN)
            return ArbEvidence(self._state,raw,"mapped status" if self._state!=ArbState.UNKNOWN else "unmapped status")

    def arm(self,*,source: str,repeat_count: int,configuration_confirmed=False):
        if configuration_confirmed is not True:
            raise SafetyGuardError("explicit verified configuration required")
        if source not in ("BUS","EXT"):
            raise ConfigurationError("BUS/EXT and finite positive repeat count required")
        _repeat(repeat_count)
        with self.driver.session.operation_lock():
            if not self.driver.session.is_connected:
                raise SafetyGuardError("explicit connected session required")
            if self._live() and self._state in (ArbState.ARMED,ArbState.RUNNING,ArbState.UNKNOWN):
                raise SafetyGuardError("existing execution not resolved")
            self.driver._assert_write_authorized()
            self._generation=self.driver.session.generation
            self._trigger_source=source
            self._trigger_attempted=False
            self._abort_attempted=False
            self._state=ArbState.UNKNOWN
            try:
                self.driver.trigger.arb_source_set(source)
                self.driver.arb.count_set(repeat_count)
                self.driver.arb.init()
            except ScpiDriverError as exc:
                return ArbEvidence(ArbState.UNKNOWN,None,str(exc))
            return self.observe()

    def trigger_bus(self):
        with self.driver.session.operation_lock():
            if (not self._live() or self._trigger_source!="BUS" or self._state!=ArbState.ARMED
                    or self._trigger_attempted or self._abort_attempted):
                raise SafetyGuardError("confirmed BUS-armed state in same session required")
            self._trigger_attempted=True
            self._state=ArbState.UNKNOWN
            try:
                self.driver.ieee.trigger()
            except ScpiDriverError as exc:
                return ArbEvidence(self._state,None,str(exc))
            return self.observe()

    def abort(self):
        with self.driver.session.operation_lock():
            if not self._live():
                return ArbEvidence(ArbState.UNKNOWN,None,"session changed; abort not transmitted")
            if self._abort_attempted:
                return ArbEvidence(ArbState.UNKNOWN,None,"abort already attempted; no replay")
            self._abort_attempted=True
            self._state=ArbState.UNKNOWN
            try:
                self.driver.arb.abort()
            except ScpiDriverError as exc:
                return ArbEvidence(self._state,None,str(exc))
            evidence = self.observe()
            if evidence.state != ArbState.ABORTED:
                self._state=ArbState.UNKNOWN
                return ArbEvidence(self._state,evidence.raw_status,"abort not confirmed: "+evidence.reason)
            return evidence

    def wait(self,*,max_polls: int,cancelled=lambda:False,between_polls=lambda:None):
        if type(max_polls) is not int or not 1<=max_polls<=10000:
            raise ConfigurationError("finite poll budget 1..10000 required")
        for i in range(1,max_polls+1):
            if cancelled():
                e=self.abort()
                return ArbEvidence(e.state,e.raw_status,"cancel: "+e.reason,i)
            with self.driver.session.operation_lock():
                e=self.observe()
                if e.state in (ArbState.COMPLETE,ArbState.ABORTED,ArbState.ERROR,ArbState.UNKNOWN):
                    return ArbEvidence(e.state,e.raw_status,e.reason,i)
                if i==max_polls:
                    self._state=ArbState.UNKNOWN
                    return ArbEvidence(ArbState.UNKNOWN,e.raw_status,"poll budget exhausted",i)
            between_polls()
