import pytest
from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.command_specs import COMMAND_SPECS


@pytest.mark.parametrize("quantity,header", [("voltage","VOLT"),("current","CURR")])
def test_acquisition_threshold(quantity, header):
    cmd = f"TRIG:ACQ:{header}:LEV"
    t = (ScriptedScpiTransport()
         .on("TRIG:ACQ:SOUR?", header)
         .on(f"{cmd} 2.5")
         .on("TRIG:ACQ:SOUR?", header)
         .on(f"{cmd}?", "2.5"))
    with ITM3900D("sim", transport=t) as d:
        getattr(d.trigger, f"acquire_{quantity}_level_set")(2.5)
        assert getattr(d.trigger, f"acquire_{quantity}_level_query")() == 2.5
        assert t.history == [
            "TRIG:ACQ:SOUR?", f"{cmd} 2.5",
            "TRIG:ACQ:SOUR?", f"{cmd}?",
        ]


@pytest.mark.parametrize("quantity,actual", [("voltage", "CURR"), ("current", "VOLT")])
@pytest.mark.parametrize("operation", ["set", "query"])
def test_acquisition_threshold_requires_matching_source(quantity, actual, operation):
    t = ScriptedScpiTransport().on("TRIG:ACQ:SOUR?", actual)
    with ITM3900D("sim", transport=t) as d:
        method = getattr(d.trigger, f"acquire_{quantity}_level_{operation}")
        with pytest.raises(ConfigurationError, match="acquisition trigger source must be"):
            method(2.5) if operation == "set" else method()
        assert t.history == ["TRIG:ACQ:SOUR?"]


def test_acquisition_threshold_specs_declare_source_dependency():
    dependency = ("TriggerSubsystem.acquire_source_query",)
    for quantity in ("voltage", "current"):
        for operation in ("set", "query"):
            spec = COMMAND_SPECS[f"TriggerSubsystem.acquire_{quantity}_level_{operation}"]
            assert spec.dependencies == dependency


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
