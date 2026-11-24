import pytest
from scpi_driver_core import ConfigurationError
from scpi_driver_core.scpi.parsers import parse_identity
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import auto_detect_instrument, ITM3900D
import itech_driver.discovery as discovery


def test_discovery_dedup_and_filter(monkeypatch):
    usb = discovery.Endpoint("usbtmc", "USB0::1::2::A::INSTR")
    lan = discovery.Endpoint("tcp", "192.168.1.2", 30000)
    bad = discovery.Endpoint("tcp", "192.168.1.3", 30000)
    monkeypatch.setattr(discovery, "_visa_candidates", lambda: [usb])
    monkeypatch.setattr(discovery, "_mdns_candidates", lambda: [lan, bad, lan])
    def probe(endpoint, timeout, baudrate):
        return parse_identity("OTHER,IT-M3902D-80-40,A,1") if endpoint == bad else parse_identity("ITECH,IT-M3902D-80-40,A,1")
    monkeypatch.setattr(discovery, "_probe", probe)
    result = discovery.discover_instruments()
    assert len(result.devices) == 1
    assert result.devices[0].endpoints == (usb, lan)
    assert len(result.diagnostics) == 1


def test_backend_failure_and_bounded_subnet(monkeypatch):
    def missing():
        raise ImportError("no VISA")
    monkeypatch.setattr(discovery, "_visa_candidates", missing)
    monkeypatch.setattr(discovery, "_probe", lambda *a: (_ for _ in ()).throw(TimeoutError("timeout")))
    result = discovery.discover_instruments(subnet="192.168.1.0/30", use_mdns=False)
    assert len(result.diagnostics) == 3
    assert not result.devices


@pytest.mark.parametrize("subnet", ["8.8.8.0/24", "192.168.0.0/16", "::/120", "bad"])
def test_reject_bad_subnet(subnet):
    with pytest.raises(ConfigurationError):
        discovery.discover_instruments(subnet=subnet, use_visa=False, use_mdns=False)


def test_real_variant_autodetection():
    t = ScriptedScpiTransport().on("*IDN?", "ITECH,IT-M3902D-80-40,A,1")
    with auto_detect_instrument("sim", transport=t) as d:
        assert isinstance(d, ITM3900D)
