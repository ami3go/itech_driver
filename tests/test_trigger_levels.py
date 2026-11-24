import pytest
from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("quantity,header", [("voltage","VOLT"),("current","CURR")])
def test_acquisition_threshold(quantity, header):
    cmd = f"TRIG:ACQ:{header}:LEV"
    t = ScriptedScpiTransport().on(f"{cmd} 2.5").on(f"{cmd}?", "2.5")
    with ITM3900D("sim", transport=t) as d:
        getattr(d.trigger, f"acquire_{quantity}_level_set")(2.5)
        assert getattr(d.trigger, f"acquire_{quantity}_level_query")() == 2.5
        assert t.history == [f"{cmd} 2.5", f"{cmd}?"]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True, "1;*RST"])
def test_invalid_threshold_no_io(value):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        for quantity in ("voltage","current"):
            with pytest.raises(ConfigurationError):
                getattr(d.trigger, f"acquire_{quantity}_level_set")(value)
        with pytest.raises(UnsupportedOperationError):
            d.trigger.level_set(1)
        with pytest.raises(UnsupportedOperationError):
            d.trigger.level_query()
        assert t.history == []
