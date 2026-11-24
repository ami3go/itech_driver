import struct

import pytest
from hypothesis import given, strategies as st
from scpi_driver_core import ScpiClient, ScpiSession
from scpi_driver_core.exceptions import ConfigurationError, ResponseParseError, TransportTimeoutError
from scpi_driver_core.simulation import ScriptedReply, ScriptedScpiTransport

from itech_driver import ITM3900D, GenericSCPIInstrument, auto_detect_instrument
from itech_driver.exceptions import TimeoutError

IDN = "ITECH,IT-M3902D-80-40,SIM001,1.0"


def make_driver(transport):
    return ITM3900D("sim", transport=transport)


def test_session_and_subsystem_wiring():
    t = ScriptedScpiTransport().on("*IDN?", IDN)
    with make_driver(t) as driver:
        assert isinstance(driver.session, ScpiSession)
        assert isinstance(driver.client, ScpiClient)
        assert t.history == []
        assert driver.identify() == IDN
        for name in ("system", "source", "output", "status", "trigger", "arb", "battery", "initiate", "abort", "io", "ieee"):
            assert getattr(driver, name) is not None
    assert not t.is_open
    driver.close()


def test_exact_command_coverage():
    t = ScriptedScpiTransport().on("*IDN?", IDN)
    commands = [
        "SOUR:VOLT 12.5", "OUTP:STAT OFF", "ARB:FUNCTION:SHAPE UDEF",
        "BATT:CHAR:VOLT 3.5", "IO:SELect 1", "TRIG:ACQ:SOUR EXT",
        "INIT:ACQ", "INITiate:ARB", "ABORt:ARB", "*CLS",
    ]
    for command in commands:
        t.on(command)
    t.on("SOUR:VOLT? MIN", "0").on("SOUR:VOLT? MAX", "30")
    t.on("SOUR:VOLT?", "12.5").on("OUTP:STAT?", "OFF")
    t.on("STAT:OPER:COND?", "4").on("SYST:VERSion?", "1999.0")
    with make_driver(t) as d:
        d.source.voltage_set(12.5)
        d.output.state_set(False)
        d.arb.function_shape_set("UDEF")
        d.battery.charge_voltage_set(3.5)
        d.io.select(1)
        d.trigger.acquire_start()
        d.initiate.arb()
        d.abort.arb()
        d.ieee.clear_status()
        assert [s.upper() for s in t.history] == [s.upper() for s in ["*IDN?","SOUR:VOLT? MIN","SOUR:VOLT? MAX",*commands]]
        assert d.source.voltage_query() == 12.5
        assert d.output.state_query() is False
        assert d.status.oper_condition_query() == 4
        assert d.system.version() == "1999.0"


def test_no_replay_on_ambiguous_timeout():
    def ambiguous_write(_command):
        # Handler runs after bytes have reached the transport and history.
        raise TransportTimeoutError("timeout after transmission")

    t = ScriptedScpiTransport().on("*TRG", ambiguous_write)
    with make_driver(t) as d:
        with pytest.raises(TimeoutError) as failure:
            d.ieee.trigger()
        assert isinstance(failure.value.__cause__, TransportTimeoutError)
        assert t.history == ["*TRG"]
        assert not d.session.is_connected


def test_query_timeout_is_not_replayed():
    t = ScriptedScpiTransport().on("*IDN?", ScriptedReply(raises=TransportTimeoutError("timeout")))
    with make_driver(t) as d:
        with pytest.raises(TimeoutError):
            d.identify()
        assert t.history == ["*IDN?"]


@pytest.mark.parametrize("response", ["UNKNOWN", "ONWARD", "2", "-1"])
def test_malformed_output_is_not_silently_false(response):
    t = ScriptedScpiTransport().on("OUTP:STAT?", response)
    with make_driver(t) as d, pytest.raises(ResponseParseError):
        d.output.state_query()


def test_binary_and_following_query():
    t = ScriptedScpiTransport().reply_block("DATA?", struct.pack("<2f", 1.5, -2.0))
    t.on("*IDN?", IDN)
    with make_driver(t) as d:
        assert d.query_binary("DATA?", container=tuple) == (1.5, -2.0)
        assert d.identify() == IDN


def test_binary_partial_value():
    t = ScriptedScpiTransport().reply_block("DATA?", b"abc")
    with make_driver(t) as d, pytest.raises(ResponseParseError):
        d.query_binary("DATA?")


def test_auto_detect_and_generic():
    t = ScriptedScpiTransport().on("*IDN?", IDN)
    with auto_detect_instrument("sim", transport=t) as d:
        assert isinstance(d, ITM3900D)
        assert d.identify() == IDN
    unknown = ScriptedScpiTransport().on("*IDN?", "ITECH,UNKNOWN,SIM001,1.0")
    with auto_detect_instrument("sim", transport=unknown) as d:
        assert isinstance(d, GenericSCPIInstrument)
        assert d.ieee.idn().startswith("ITECH")


def test_invalid_idn_closes_transport():
    from scpi_driver_core.exceptions import IdentityError
    t = ScriptedScpiTransport().on("*IDN?", "bad")
    with pytest.raises(IdentityError):
        auto_detect_instrument("sim", transport=t)
    assert not t.is_open


def test_bad_settings_fail_before_open():
    t = ScriptedScpiTransport()
    with pytest.raises(ConfigurationError):
        ITM3900D("sim", timeout=0, transport=t)
    assert not t.is_open


@pytest.mark.property
@given(st.integers(min_value=-32768, max_value=32767))
def test_binary_signed_short_roundtrip(value):
    t = ScriptedScpiTransport().reply_block("DATA?", struct.pack(">h", value))
    with make_driver(t) as d:
        assert d.query_binary("DATA?", "h", is_big_endian=True) == [value]
