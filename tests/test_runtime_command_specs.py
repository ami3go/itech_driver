import json
from pathlib import Path

import pytest
from scpi_driver_core import ConfigurationError, UnsupportedOperationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.command_specs import COMMAND_SPECS, ResultKind, execute
from itech_driver.simulator import ItechSimulator


@pytest.mark.parametrize("method,spec", [(m,s) for m,s in COMMAND_SPECS.items()
                                         if s.kind is ResultKind.FLOAT])
def test_scalar_specs_exact_wire_and_result(method, spec):
    t = ScriptedScpiTransport().on(spec.header, "1.25")
    cls, name = method.split(".")
    with ITM3900D("sim", transport=t) as d:
        obj = d.measurement if cls == "MeasurementSubsystem" else d.fetch
        assert getattr(obj, name)() == 1.25
    assert t.history == [spec.header]


def test_registered_output_and_simulator_share_header():
    sim = ItechSimulator()
    with ITM3900D("sim", transport=sim.transport) as d:
        assert d.output.state_query() is False
        d.output.state_set(True)
        assert d.output.state_query() is True
    assert sim.transport.history == ["OUTP:STAT?", "OUTP:STAT ON", "OUTP:STAT?"]


def test_executor_rejects_unknown_methods_and_wrong_arguments_without_io():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(UnsupportedOperationError):
            execute(d, "unknown")
        with pytest.raises(ConfigurationError):
            execute(d, "OutputSubsystem.state_set", 1.5)
        with pytest.raises(ConfigurationError):
            execute(d, "MeasurementSubsystem.voltage_query", 1)
    assert t.history == []


def test_runtime_specs_are_subset_of_complete_inventory():
    registry = Path(__file__).resolve().parents[1] / "docs" / "command_registry.json"
    methods = {e["method"] for e in json.loads(registry.read_text(encoding="utf-8"))["entries"]}
    assert set(COMMAND_SPECS) <= methods
    assert all(s.replay == "never" and s.guide_status == "unverified" for s in COMMAND_SPECS.values())
