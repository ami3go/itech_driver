import pytest
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("name,quantity", [("ovp", "VOLT"), ("ocp", "CURR"), ("power_limit", "POW")])
def test_protection_threshold_and_state(name, quantity):
    header = f"SOUR:{quantity}:OVER:PROT"
    t = ScriptedScpiTransport().on(f"{header}:LEV 5.0").on(f"{header}:LEV?", "5.0")
    t.on(f"{header}:STAT 1").on(f"{header}:STAT?", "1")
    with ITM3900D("sim", transport=t) as d:
        getattr(d.source, name + "_set")(5.0)
        assert getattr(d.source, name + "_query")() == 5.0
        getattr(d.source, name + "_enable")(True)
        assert getattr(d.source, name + "_enable_query")() is True
        assert t.history == [f"{header}:LEV 5.0", f"{header}:LEV?", f"{header}:STAT 1", f"{header}:STAT?"]


@pytest.mark.parametrize("name", ["ovp", "ocp", "power_limit"])
def test_invalid_protection_inputs_no_io(name):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            getattr(d.source, name + "_set")(float("nan"))
        with pytest.raises(ConfigurationError):
            getattr(d.source, name + "_set")(1, channel=2)
        with pytest.raises(ConfigurationError):
            getattr(d.source, name + "_enable")("OFF")
        with pytest.raises(ConfigurationError):
            getattr(d.source, name + "_enable_query")(channel=2)
        assert t.history == []
