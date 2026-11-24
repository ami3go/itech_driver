import pytest
from scpi_driver_core import ConfigurationError, IdentityError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.capabilities import RATINGS


def fixture(model="IT-M3902D-80-40", manufacturer="ITECH", hi="9999"):
    t = ScriptedScpiTransport().on("*IDN?", f"{manufacturer},{model},SN,1.0")
    for h in ("SOUR:VOLT","SOUR:CURR","SOUR:VOLT:LIM","SOUR:CURR:LIM","SOUR:POW:LIM"):
        t.on(h+"? MIN", "0").on(h+"? MAX", hi)
    return t


def test_ratings_are_explicit_and_discovery_is_read_only():
    assert len(RATINGS) == 26
    t = fixture()
    with ITM3900D("sim", transport=t) as d:
        cap = d.discover_capabilities()
        assert cap.ratings.power_w == 2000
        assert cap.voltage.maximum == 80
        assert cap.current.maximum == 40
        assert cap.power_limit.maximum == 2000
        assert len(t.history) == 11
        assert all("?" in cmd for cmd in t.history)
        with pytest.raises(ConfigurationError):
            cap.voltage.validate(81)


@pytest.mark.parametrize("model,manufacturer", [("IT-M3900D","ITECH"),("IT-M3902D-80-41","ITECH"),("IT-M3902D-80-40","OTHER")])
def test_unknown_model_rejected_before_range_probe(model, manufacturer):
    t = fixture(model,manufacturer)
    with ITM3900D("sim", transport=t) as d, pytest.raises(IdentityError):
        d.discover_capabilities()
    assert t.history == ["*IDN?"]


def test_bad_range():
    t = fixture(hi="-1")
    with ITM3900D("sim", transport=t) as d, pytest.raises(ResponseParseError):
        d.discover_capabilities()
