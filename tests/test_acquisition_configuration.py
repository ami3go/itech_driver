import pytest
from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("method,value,wire", [
    ("acquisition_points_set",100,"SENS:ACQ:POIN 100"),
    ("acquisition_offset_set",-2,"SENS:ACQ:OFFS:POIN -2"),
    ("acquisition_interval_set",0.01,"SENS:ACQ:TINT 0.01"),
])
def test_acquisition_setter(method,value,wire):
    t = ScriptedScpiTransport().on(wire)
    with ITM3900D("sim", transport=t) as d:
        getattr(d.sense,method)(value)
        assert t.history == [wire]


@pytest.mark.parametrize("method,value", [
    ("acquisition_points_set",0),("acquisition_points_set",1.2),
    ("acquisition_offset_set",True),("acquisition_offset_set",1.2),
    ("acquisition_interval_set",0),("acquisition_interval_set",float("nan")),
    ("acquisition_interval_set",float("inf")),("acquisition_interval_set","1;*RST"),
])
def test_invalid_config(method,value):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            getattr(d.sense,method)(value)
        assert not t.history


def test_unqualified_readback_is_not_sent():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        for method in ("acquisition_points_query","acquisition_offset_query","acquisition_interval_query"):
            with pytest.raises(UnsupportedOperationError):
                getattr(d.sense,method)()
        assert not t.history
