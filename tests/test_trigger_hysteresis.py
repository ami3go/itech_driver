import pytest
from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("subsystem", ["ACQ", "DLOG", "ELOG"])
@pytest.mark.parametrize("quantity", ["VOLT", "CURR"])
@pytest.mark.parametrize("bound,other,other_value", [("HIGH","LOW","1"), ("LOW","HIGH","3")])
def test_hysteresis(subsystem, quantity, bound, other, other_value):
    prefix = f"TRIG:{subsystem}:{quantity}:HYST"
    t = ScriptedScpiTransport().on(f"{prefix}:{other}?", other_value)
    t.on(f"{prefix}:{bound} 2").on(f"{prefix}:{bound}?", "2")
    with ITM3900D("sim", transport=t) as d:
        d.trigger.hysteresis_threshold_set(subsystem, quantity, bound, 2)
        assert d.trigger.hysteresis_threshold_query(subsystem, quantity, bound) == 2
        assert t.history == [f"{prefix}:{other}?", f"{prefix}:{bound} 2", f"{prefix}:{bound}?"]


def test_invalid_order_no_setting_write():
    t = ScriptedScpiTransport().on("TRIG:ACQ:VOLT:HYST:LOW?", "5")
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.trigger.hysteresis_threshold_set("ACQ","VOLT","HIGH",3)
        assert t.history == ["TRIG:ACQ:VOLT:HYST:LOW?"]
        with pytest.raises(ConfigurationError):
            d.trigger.hysteresis_threshold_set("ARB","VOLT","HIGH",3)
        with pytest.raises(UnsupportedOperationError):
            d.trigger.hysteresis_set(1)
        with pytest.raises(UnsupportedOperationError):
            d.trigger.hysteresis_query()
        assert t.history == ["TRIG:ACQ:VOLT:HYST:LOW?"]
