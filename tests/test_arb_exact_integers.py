import pytest
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("method,tail,maximum", [
    ("udef_count_set", (), 200),
    ("udef_level_set", (2,), 200), ("udef_level_query", (), 200),
    ("udef_dwell_set", (1,), 200), ("udef_dwell_query", (), 200),
    ("udef_slew_set", (1,), 200), ("udef_slew_query", (), 200),
    ("count_set", (), 999999), ("save", (), 10), ("recall", (), 10),
])
def test_invalid_integer_parameters_are_never_coerced(method, tail, maximum):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        for bad in (True, False, 1.0, 1.5, -1, 0, "1", maximum + 1, 10**1000):
            with pytest.raises(ConfigurationError):
                getattr(d.arb, method)(bad, *tail)
    assert t.history == []


@pytest.mark.parametrize("method,args,command", [
    ("udef_count_set", (1,), "ARB:UDEFined:COUNt 1"),
    ("udef_count_set", (200,), "ARB:UDEFined:COUNt 200"),
    ("udef_level_set", (200, 2), "ARB:UDEFined:LEVel 200,2.0"),
    ("udef_dwell_set", (1, 1), "ARB:UDEFined:DWELl 1,1.0"),
    ("udef_slew_set", (200, 1), "ARB:UDEFined:SLEW 200,1.0"),
    ("count_set", (1,), "ARB:COUNT 1"),
    ("count_set", (999999,), "ARB:COUNT 999999"),
    ("save", (1,), "ARB:SAVE 1"), ("recall", (10,), "ARB:RECall 10"),
])
def test_family_list_boundaries_preserve_existing_wire_syntax(method, args, command):
    t = ScriptedScpiTransport().on(command)
    with ITM3900D("sim", transport=t) as d:
        getattr(d.arb, method)(*args)
    assert t.history == [command]


@pytest.mark.parametrize("method,header", [
    ("udef_level_query", "ARB:UDEFined:LEVel? 200"),
    ("udef_dwell_query", "ARB:UDEFined:DWELl? 200"),
    ("udef_slew_query", "ARB:UDEFined:SLEW? 200"),
])
def test_step_query_boundary(method, header):
    t = ScriptedScpiTransport().on(header, "1")
    with ITM3900D("sim", transport=t) as d:
        assert getattr(d.arb, method)(200) == 1
    assert t.history == [header]


@pytest.mark.parametrize("method", ["udef_level_set", "udef_dwell_set", "udef_slew_set"])
@pytest.mark.parametrize("bad", [True, "1", float("nan"), float("inf"), 10**1000])
def test_invalid_numeric_arguments_before_io(method, bad):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d, pytest.raises(ConfigurationError):
        getattr(d.arb, method)(1, bad)
    assert t.history == []
