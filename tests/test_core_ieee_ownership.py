import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError, SafetyGuardError, TransportTimeoutError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D, GenericSCPIInstrument
from itech_driver.exceptions import TimeoutError


@pytest.mark.parametrize("cls", [ITM3900D, GenericSCPIInstrument])
def test_ieee_exact_legacy_wire_and_return_contract(cls):
    t = (ScriptedScpiTransport().on("*IDN?", "legacy").on("*OPC?", "+1")
         .on("*TST?", "2").on("*CLS").on("*OPC").on("*TRG").on("*SAV 1").on("*RCL 2").on("*RST"))
    with cls("sim", transport=t) as d:
        assert d.ieee.idn() == "legacy"
        assert d.ieee.opc(wait=True) == "+1"
        assert d.ieee.self_test() == 2
        assert d.ieee.clear_status() is None
        assert d.ieee.opc() is None
        assert d.ieee.trigger() is None
        assert d.ieee.save(1) is None
        assert d.ieee.recall(2) is None
        assert d.ieee.reset() is None
    assert t.history == ["*IDN?", "*OPC?", "*TST?", "*CLS", "*OPC", "*TRG", "*SAV 1", "*RCL 2", "*RST"]


@pytest.mark.parametrize("mask", [0, 255])
def test_ieee_masks_and_explicit_stb(mask, monkeypatch):
    t = ScriptedScpiTransport().on(f"*ESE {mask}").on("*ESE?", str(mask)).on("*STB?", "64")
    monkeypatch.setattr(t, "read_status_byte", lambda **_: pytest.fail("must not serial poll"), raising=False)
    with ITM3900D("sim", transport=t) as d:
        d.status.std_event_enable_set(mask)
        assert d.status.std_event_enable_query() == mask
        assert d.status.status_byte() == 64
    assert t.history == [f"*ESE {mask}", "*ESE?", "*STB?"]


@pytest.mark.parametrize("bad", [True, 1.5, -1, 256, "1"])
def test_invalid_ieee_mask_no_io(bad):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d, pytest.raises(ConfigurationError):
        d.status.std_event_enable_set(bad)
    assert t.history == []


@pytest.mark.parametrize("method,command", [
    ("std_event_register_query", "*ESR?"), ("status_byte", "*STB?"),
    ("std_event_enable_query", "*ESE?"),
])
def test_invalid_register_response(method, command):
    t = ScriptedScpiTransport().on(command, "256")
    with ITM3900D("sim", transport=t) as d, pytest.raises(ResponseParseError):
        getattr(d.status, method)()
    assert t.history == [command]


def test_event_read_to_clear_and_no_replay():
    replies = iter(["32", "0"])
    t = ScriptedScpiTransport().on("*ESR?", lambda _: next(replies))
    with ITM3900D("sim", transport=t) as d:
        assert d.status.std_event_register_query() == 32
        assert d.status.std_event_register_query() == 0
        def fail(_):
            raise TransportTimeoutError("lost event reply")
        t.on("*ESR?", fail)
        with pytest.raises(TimeoutError) as caught:
            d.status.std_event_register_query()
        assert isinstance(caught.value.__cause__, TransportTimeoutError)
        assert not d.session.is_connected
    assert t.history == ["*ESR?"] * 3


def test_common_commands_preserve_remote_guard_and_invalidate_on_reset():
    t = ScriptedScpiTransport().on("SYST:REM").on("*RST").on("*TRG")
    with ITM3900D("sim", transport=t, require_remote=True) as d:
        with pytest.raises(SafetyGuardError):
            d.ieee.trigger()
        with pytest.raises(SafetyGuardError):
            d.status.std_event_enable_set(1)
        assert t.history == []
        d.enter_remote()
        d.ieee.reset()
        assert d.requested_mode is None
        with pytest.raises(SafetyGuardError):
            d.ieee.trigger()
    assert t.history == ["SYST:REM", "*RST"]


def test_core_methods_actually_delegated(monkeypatch):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        calls = []
        monkeypatch.setattr(d.session.ieee488, "clear_status", lambda: calls.append("core"))
        d.ieee.clear_status()
        assert calls == ["core"]
    assert t.history == []
