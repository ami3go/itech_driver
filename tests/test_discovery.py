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


def test_cli_uses_common_discovery_without_visa(monkeypatch, capsys):
    from itech_driver.cli import main
    endpoint = discovery.Endpoint("vcp", "COM7")
    def forbidden():
        pytest.fail("disabled provider called")
    monkeypatch.setattr(discovery, "_visa_candidates", forbidden)
    monkeypatch.setattr(discovery, "_mdns_candidates", forbidden)
    monkeypatch.setattr(discovery, "_vcp_candidates", lambda: [endpoint])
    monkeypatch.setattr(discovery, "_probe", lambda *a: parse_identity("ITECH,IT-M3902D-80-40,S,1"))
    main(["discover", "--no-visa", "--no-mdns", "--vcp"])
    assert "COM7" in capsys.readouterr().out


def test_probe_closes_injected_session_even_on_failure(monkeypatch):
    from itech_driver import GenericSCPIInstrument
    t = ScriptedScpiTransport().on("*IDN?", "bad")
    def factory(resource, **kwargs):
        return GenericSCPIInstrument(resource, transport=t)
    monkeypatch.setattr(discovery, "GenericSCPIInstrument", factory)
    from scpi_driver_core import IdentityError
    with pytest.raises(IdentityError):
        discovery._probe(discovery.Endpoint("tcp", "127.0.0.1", 30000), 100, 9600)
    assert not t.is_open
    assert t.history == ["*IDN?"]


def test_probe_success_closes_and_never_writes_setting(monkeypatch):
    from itech_driver import GenericSCPIInstrument
    t = ScriptedScpiTransport().on("*IDN?", "ITECH,IT-M3902D-80-40,S,1")
    monkeypatch.setattr(discovery, "GenericSCPIInstrument",
                        lambda resource, **kwargs: GenericSCPIInstrument(resource, transport=t))
    assert discovery._probe(discovery.Endpoint("vcp", "COM7"), 100, 9600).serial_number == "S"
    assert not t.is_open
    assert t.history == ["*IDN?"]


def test_unknown_serials_not_deduplicated(monkeypatch):
    a = discovery.Endpoint("tcp", "192.0.2.1", 30000)
    b = discovery.Endpoint("tcp", "192.0.2.2", 30000)
    monkeypatch.setattr(discovery, "_mdns_candidates", lambda: [a, b])
    monkeypatch.setattr(discovery, "_probe", lambda *a: parse_identity("ITECH,IT-M3902D-80-40,unknown,1"))
    assert len(discovery.discover_instruments(use_visa=False).devices) == 2


def test_mdns_cleanup_when_cancel_raises(monkeypatch):
    import sys
    from types import SimpleNamespace
    closed = []
    class Z:
        def close(self):
            closed.append(True)
    class B:
        def __init__(self, *args):
            pass
        def cancel(self):
            raise RuntimeError("cancel failed")
    monkeypatch.setitem(sys.modules, "zeroconf", SimpleNamespace(
        Zeroconf=Z, ServiceBrowser=B, ServiceListener=object))
    monkeypatch.setattr(discovery.threading.Event, "wait", lambda *args: None)
    with pytest.raises(RuntimeError, match="cancel failed"):
        discovery._mdns_candidates()
    assert closed == [True]
