import pytest
from scpi_driver_core import ConfigurationError, IdentityError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.capabilities import ApplicationLimits, Range


def fixture(model="IT-M3902D-80-40"):
    t = ScriptedScpiTransport().on("*IDN?", f"ITECH,{model},S,1")
    for header in ("SOUR:VOLT", "SOUR:CURR", "SOUR:VOLT:LIM", "SOUR:CURR:LIM", "SOUR:POW:LIM"):
        t.on(header + "? MIN", "0").on(header + "? MAX", "9999")
        t.on(header + " 5")
    return t


@pytest.mark.parametrize("method,value", [
    ("voltage_set", 81), ("current_set", 41), ("voltage_limit_set", 81),
    ("current_limit_set", 41), ("programmed_power_limit_set", 2001)
])
def test_nominal_rating_cannot_be_exceeded_even_if_live_range_is_larger(method, value):
    t = fixture()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            getattr(d.source, method)(value)
        assert all("?" in cmd for cmd in t.history)
        getattr(d.source, method)(5)
        assert t.history.count("*IDN?") == 1
        assert t.history[-1].endswith(" 5")


@pytest.mark.parametrize("method", ["voltage_set", "current_set", "voltage_limit_set",
                                    "current_limit_set", "programmed_power_limit_set"])
def test_application_bound_enforced_before_setting_write(method):
    t = fixture()
    app = ApplicationLimits(Range(0, 5), Range(0, 5), Range(0, 5))
    with ITM3900D("sim", transport=t, application_limits=app) as d:
        with pytest.raises(ConfigurationError):
            getattr(d.source, method)(6)
        assert all("?" in cmd for cmd in t.history)
        getattr(d.source, method)(5)
    assert t.history[-1].endswith(" 5")


def test_unknown_model_rejected_before_range_or_setting_write():
    t = fixture("UNKNOWN")
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(IdentityError):
            d.source.voltage_set(1)
    assert t.history == ["*IDN?"]


def test_reconnect_uses_new_rating_not_stale_cache():
    t = fixture()
    with ITM3900D("sim", transport=t) as d:
        d.source.voltage_set(5)
        d.session.close()
        t.on("*IDN?", "ITECH,IT-M3901D-10-170,S2,1")
        d.session.open()
        with pytest.raises(ConfigurationError):
            d.source.voltage_set(11)
        assert t.history.count("*IDN?") == 2
        assert "SOUR:VOLT 11" not in t.history


def test_bad_application_limits_rejected_before_open():
    t = fixture()
    with pytest.raises(ConfigurationError):
        ITM3900D("sim", transport=t, application_limits={})
    assert not t.is_open
    assert t.history == []
