import pytest
from itech_driver import ITM3900D, GenericSCPIInstrument
from itech_driver import cli
from scpi_driver_core import TransportTimeoutError
from scpi_driver_core.simulation import ScriptedScpiTransport


BASE = ["control", "--resource", "sim"]
BOUNDS = ["--max-voltage", "10", "--max-current", "2", "--max-power", "20"]
RESIDUAL = ["--max-residual-voltage", "0.1", "--max-residual-current", "0.1"]
ON = ["--output", "on", "--authorize-output", "--hold-seconds", "0"] + BOUNDS + RESIDUAL


def transport():
    t = ScriptedScpiTransport().on("*IDN?", "ITECH,IT-M3902D-80-40,S,1")
    state = {"on": False, "voltage": 5, "current": 1}
    t.on("SYST:REM").on("SYST:LOC")
    t.on("OUTP:STAT?", lambda _: str(int(state["on"])))
    t.on("OUTP:STAT ON", lambda _: state.update(on=True))
    t.on("OUTP:STAT OFF", lambda _: state.update(on=False))
    t.on("STAT:QUES:COND?", "0")
    t.on("MEAS:VOLT?", lambda _: str(state["voltage"] if state["on"] else 0))
    t.on("MEAS:CURR?", lambda _: str(state["current"] if state["on"] else 0))
    for q, ceiling in (("VOLT", 10), ("CURR", 2), ("POW", 20)):
        t.on(f"SOUR:{q}:LIM? MIN", "0").on(f"SOUR:{q}:LIM? MAX", str(ceiling))
        t.on(f"SOUR:{q}:LIM?", str(ceiling))
        t.on(f"SOUR:{q}:OVER:PROT:STAT?", "1").on(f"SOUR:{q}:OVER:PROT:LEV?", str(ceiling))
        if q != "POW":
            t.on(f"SOUR:{q}? MIN", "0").on(f"SOUR:{q}? MAX", str(ceiling))
            key = "voltage" if q == "VOLT" else "current"
            t.on(f"SOUR:{q}?", lambda _, k=key: str(state[k]))
    t.on("SOUR:VOLT 6.0", lambda _: state.update(voltage=6))
    t.on("SOUR:FUNC:MODE?", "FIX").on("SOUR:EXT:PROG?", "0")
    return t


def install(monkeypatch, t, cls=ITM3900D):
    monkeypatch.setattr(cli, "auto_detect_instrument", lambda resource, **kwargs: cls(resource, transport=t, **kwargs))


@pytest.mark.parametrize("args", [
    ["--output", "on"],
    ["--voltage", "nan"] + BOUNDS,
    ["--voltage", "11"] + BOUNDS,
    ["--output", "off"],
    ["--output", "off", "--voltage", "1"] + BOUNDS + RESIDUAL,
    ["--authorize-output"],
])
def test_invalid_requests_do_not_open(monkeypatch, args):
    def fail(*a, **k):
        pytest.fail("opened transport for invalid request")
    monkeypatch.setattr(cli, "auto_detect_instrument", fail)
    with pytest.raises(SystemExit) as error:
        cli.main(BASE + args)
    assert error.value.code == 1


def test_read_only_generic_identity(monkeypatch):
    t = ScriptedScpiTransport().on("*IDN?", "OTHER,UNKNOWN,S,1")
    install(monkeypatch, t, GenericSCPIInstrument)
    cli.main(BASE)
    assert t.history == ["*IDN?"]
    assert not t.is_open


def test_setting_only_no_implicit_activation(monkeypatch):
    t = transport()
    install(monkeypatch, t)
    cli.main(BASE + ["--voltage", "6"] + BOUNDS)
    assert "SOUR:VOLT 6.0" in t.history
    assert "OUTP:STAT ON" not in t.history
    assert t.history[-1] == "SYST:LOC"


def test_readback_mismatch_prevents_on(monkeypatch):
    t = transport().on("SOUR:VOLT 6.0")
    install(monkeypatch, t)
    with pytest.raises(SystemExit):
        cli.main(BASE + ["--voltage", "6"] + ON)
    assert "OUTP:STAT ON" not in t.history
    assert not t.is_open


def test_supervised_on_then_verified_off(monkeypatch):
    t = transport()
    install(monkeypatch, t)
    cli.main(BASE + ON)
    assert t.history.count("OUTP:STAT ON") == 1
    assert t.history.count("OUTP:STAT OFF") == 1
    assert t.history.index("OUTP:STAT ON") < t.history.index("OUTP:STAT OFF")
    assert t.history[-1] == "SYST:LOC"
    assert not t.is_open


def test_ambiguous_activation_unknown_never_replayed(monkeypatch, capsys):
    t = transport()
    def fail(_):
        raise TransportTimeoutError("lost after activation")
    t.on("OUTP:STAT ON", fail)
    install(monkeypatch, t)
    with pytest.raises(SystemExit) as error:
        cli.main(BASE + ON)
    assert error.value.code == 1
    assert t.history.count("OUTP:STAT ON") == 1
    assert "OUTP:STAT OFF" not in t.history
    assert "UNKNOWN" in capsys.readouterr().err


def test_off_residual_not_confirmed_is_nonzero(monkeypatch):
    t = transport().on("MEAS:VOLT?", "5")
    install(monkeypatch, t)
    with pytest.raises(SystemExit):
        cli.main(BASE + ["--output", "off"] + RESIDUAL)
    assert t.history.count("OUTP:STAT OFF") == 1
    assert "OUTP:STAT ON" not in t.history


def test_interruption_during_hold_attempts_one_off(monkeypatch):
    t = transport()
    install(monkeypatch, t)
    def interrupt(_):
        raise KeyboardInterrupt()
    monkeypatch.setattr(cli.time, "sleep", interrupt)
    with pytest.raises(SystemExit):
        cli.main(BASE + ON)
    assert t.history.count("OUTP:STAT ON") == 1
    assert t.history.count("OUTP:STAT OFF") == 1


def test_post_on_measurement_outside_envelope_causes_off(monkeypatch):
    t = transport()
    calls = []
    def measured(_):
        calls.append(1)
        return "12" if len(calls) == 2 else "0"
    t.on("MEAS:VOLT?", measured)
    install(monkeypatch, t)
    with pytest.raises(SystemExit):
        cli.main(BASE + ON)
    assert t.history.count("OUTP:STAT ON") == 1
    assert t.history.count("OUTP:STAT OFF") == 1
