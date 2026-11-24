import pytest
from itech_driver import ConnectionConfig, ITM3900D
from scpi_driver_core import ConfigurationError
from scpi_driver_core.transport import TcpTransport, SerialTransport, VisaTransport
from scpi_driver_core.simulation import ScriptedScpiTransport


@pytest.mark.parametrize("resource,kind", [
    ("tcp://127.0.0.1:30000", TcpTransport),
    ("vcp:loop://", SerialTransport),
    ("USB0::1::2::INSTR", VisaTransport),
])
def test_factory_selects_unopened_core_transport(resource, kind):
    session = ConnectionConfig(resource).make_session()
    assert isinstance(session.transport, kind)
    assert not session.is_connected


def test_injected_transport_and_legacy_constructor():
    t = ScriptedScpiTransport().on("*IDN?", "ITECH,IT-M3902D-80-40,S,1")
    with ITM3900D("sim", transport=t) as d:
        assert d.session.transport is t
        assert d.identify().startswith("ITECH")
    assert not t.is_open
    assert t.history == ["*IDN?"]


@pytest.mark.parametrize("kwargs", [
    {"timeout_ms": True}, {"timeout_ms": float("inf")}, {"timeout_ms": 10**1000},
    {"command_termination": ""}, {"response_termination": "x"},
    {"baudrate": 1.5}, {"dtr": 1}, {"chunk_size": False}, {"interface": "bad"},
])
def test_invalid_config(kwargs):
    with pytest.raises(ConfigurationError):
        ConnectionConfig("sim", **kwargs)


def test_conflicting_legacy_options_never_open():
    t = ScriptedScpiTransport()
    with pytest.raises(ConfigurationError):
        ITM3900D("sim", connection=ConnectionConfig("sim"), transport=t)
    assert not t.is_open
    with pytest.raises(ConfigurationError):
        ConnectionConfig("tcp://localhost:30000", visa_library="@sim").make_session()


@pytest.mark.parametrize("resource", ["tcp://localhost:0", "tcp://localhost:65536", "tcp://user@host:123", "tcp://host/path", "vcp:"])
def test_invalid_endpoint_before_open(resource):
    with pytest.raises(ConfigurationError):
        ConnectionConfig(resource).make_session()


def test_asymmetric_codec():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t, command_termination="\r\n", response_termination="\n") as d:
        assert d.client.codec.encode_command("*IDN?") == b"*IDN?\r\n"
        assert d.client.codec.decode_response(b"reply\n") == "reply"
