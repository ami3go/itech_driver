import pytest
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.command_specs import COMMAND_SPECS, ResultKind, execute_parameterized

@pytest.mark.parametrize("bad", ["", "1;*RST", "1\n*RST", "1\r", "1\x00", 1])
def test_parameterized_executor_rejects_multiple_messages_before_io(bad):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            execute_parameterized(d, "ArbSubsystem.count_set", bad)
    assert t.history == []

def test_parameterized_metadata_and_effect():
    for spec in COMMAND_SPECS.values():
        if spec.kind in (ResultKind.PARAM_WRITE, ResultKind.PARAM_QUERY):
            assert spec.parameters == ("validated_payload",)
            assert spec.replay == "never"
            assert spec.modifies_state == (spec.kind is ResultKind.PARAM_WRITE)

def test_existing_arb_and_io_wire_contract():
    t = ScriptedScpiTransport().on("ARB:COUNT 2").on("IO:DIRE 0,1")
    with ITM3900D("sim", transport=t) as d:
        d.arb.count_set(2)
        d.io.direction_set(0, "IN")
    assert t.history == ["ARB:COUNT 2", "IO:DIRE 0,1"]
