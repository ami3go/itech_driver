import pytest
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.command_specs import COMMAND_SPECS, ResultKind, execute_parameterized

@pytest.mark.parametrize("bad", ["", "1;*RST", "1\n*RST", "1\r", "1\x00", "1", True, 1.5])
def test_parameterized_executor_rejects_multiple_messages_before_io(bad):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            execute_parameterized(d, "ArbSubsystem.count_set", bad)
    assert t.history == []

def test_parameterized_metadata_and_effect():
    for spec in COMMAND_SPECS.values():
        if spec.kind in (ResultKind.PARAM_WRITE, ResultKind.PARAM_QUERY):
            assert spec.fields
            assert spec.parameters == tuple(f"{f.name}:{f.kind.value}" for f in spec.fields)
            assert spec.replay == "never"
            assert spec.modifies_state == (spec.kind is ResultKind.PARAM_WRITE)

def test_existing_arb_and_io_wire_contract():
    t = ScriptedScpiTransport().on("ARB:COUNT 2").on("IO:DIRE 0,1")
    with ITM3900D("sim", transport=t) as d:
        d.arb.count_set(2)
        d.io.direction_set(0, "IN")
    assert t.history == ["ARB:COUNT 2", "IO:DIRE 0,1"]


@pytest.mark.parametrize("method,args", [
    ("ArbSubsystem.udef_level_set", (1,)),
    ("ArbSubsystem.udef_level_set", (1.5, 2)),
    ("ArbSubsystem.udef_level_set", (1, float("nan"))),
    ("ArbSubsystem.function_shape_set", ("UDEF;*RST",)),
    ("IOConfigSubsystem.pwm_enable", (1, "ON")),
    ("OutputSubsystem.delay_rise_set", (-1,)),
    ("SystemSubsystem.date_set", (2026, 1.2, 2)),
])
def test_individual_wire_fields_reject_wrong_type_and_count(method,args):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            execute_parameterized(d, method, *args)
    assert t.history == []


def test_typed_arguments_preserve_exact_wire_format():
    t = ScriptedScpiTransport().on("ARB:UDEFined:LEVel 1,2.0").on("IO:PWM:ENABle 0,1")
    with ITM3900D("sim", transport=t) as d:
        d.arb.udef_level_set(1, 2)
        d.io.pwm_enable(0, True)
    assert t.history == ["ARB:UDEFined:LEVel 1,2.0", "IO:PWM:ENABle 0,1"]


@pytest.mark.parametrize("method,args", [
    ("continuous_arb_set", ("true",)), ("continuous_acq_set", (2,)),
])
def test_continuous_initiation_rejects_lossy_booleans(method,args):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d, pytest.raises(ConfigurationError):
        getattr(d.initiate, method)(*args)
    assert t.history == []
