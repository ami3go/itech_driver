"""Offline validation of a proposed parallel topology.

Never switch roles or aggregate ratings automatically. Guide V1.4 pp.213–214
indexes role and number commands; full argument/readback semantics unresolved.
"""
from dataclasses import dataclass
from scpi_driver_core import ConfigurationError
from .capabilities import RATINGS


@dataclass(frozen=True)
class ParallelMember:
    model: str
    serial: str
    role: str


@dataclass(frozen=True)
class ParallelTopology:
    members: tuple[ParallelMember,...]

    def validate(self, *, approved_max_units: int) -> ParallelMember:
        if type(approved_max_units) is not int or approved_max_units < 2:
            raise ConfigurationError("explicit approved topology capacity required")
        if not isinstance(self.members,tuple) or not 2 <= len(self.members) <= approved_max_units:
            raise ConfigurationError("invalid parallel member count")
        if any(not isinstance(member,ParallelMember) for member in self.members):
            raise ConfigurationError("invalid member")
        models={m.model for m in self.members}
        if len(models)!=1 or next(iter(models)) not in RATINGS:
            raise ConfigurationError("only identical known models allowed")
        if any(not isinstance(m.serial,str) or not m.serial.strip() for m in self.members):
            raise ConfigurationError("serial required for each member")
        if len({m.serial.strip() for m in self.members}) != len(self.members):
            raise ConfigurationError("duplicate serial")
        masters=[m for m in self.members if m.role=="master"]
        if len(masters)!=1 or any(m.role not in ("master","slave") for m in self.members):
            raise ConfigurationError("exactly one master and all other members slaves required")
        return masters[0]
