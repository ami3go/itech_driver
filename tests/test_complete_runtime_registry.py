import json
from pathlib import Path
import pytest
from scpi_driver_core import UnsupportedOperationError, ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.command_specs import COMMAND_SPECS, ResultKind, execute

def test_complete_runtime_inventory_disposition():
    inventory = Path(__file__).resolve().parents[1] / "docs" / "command_registry.json"
    keys = {e["method"] for e in json.loads(inventory.read_text(encoding="utf-8"))["entries"]}
    assert set(COMMAND_SPECS) == keys
    for key, spec in COMMAND_SPECS.items():
        assert spec.replay == "never"
        assert all(dep in keys for dep in spec.dependencies)
        if spec.kind is ResultKind.RESTRICTED:
            assert not spec.header
        if spec.kind is ResultKind.ALIAS:
            assert len(spec.dependencies) == 1
        if spec.kind is ResultKind.CORE:
            assert spec.header.startswith("*")

def test_non_generic_execution_dispositions_reject_without_io():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        for key in ("SourceSubsystem.ovp_set", "ArbSubsystem.init",
                    "IEEE488.reset", "BatterySubsystem.state_set",
                    "OutputSubsystem.watchdog_set"):
            with pytest.raises(UnsupportedOperationError):
                execute(d, key)
    assert t.history == []

def test_protection_queries_and_trigger_source_use_existing_wire():
    t = ScriptedScpiTransport().on("SOUR:VOLT:OVER:PROT:LEV?", "5").on("TRIG:ARB:SOUR BUS").on("TRIG:ARB:SOUR?", "BUS")
    with ITM3900D("sim", transport=t) as d:
        assert d.source.ovp_query() == 5
        d.trigger.arb_source_set("BUS")
        assert d.trigger.arb_source_query() == "BUS"
    assert t.history == ["SOUR:VOLT:OVER:PROT:LEV?", "TRIG:ARB:SOUR BUS", "TRIG:ARB:SOUR?"]
