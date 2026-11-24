import threading
from types import SimpleNamespace

import pytest
from scpi_driver_core import ConfigurationError, TransportTimeoutError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.exceptions import TimeoutError
import itech_driver.base as base


@pytest.mark.parametrize("bad", [-1, True, "1", float("nan"), float("inf"), 10**1000, 1, 2])
def test_invalid_delay_has_no_io(bad):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t, timeout=1000) as d:
        with pytest.raises(ConfigurationError):
            d.query_scpi("*IDN?", delay=bad)
    assert t.history == []


def test_delay_reduces_transaction_budget(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(base, "time", SimpleNamespace(monotonic=lambda: now[0],
                        sleep=lambda delay: now.__setitem__(0, now[0] + delay)))
    t = ScriptedScpiTransport().on("*IDN?", "ID")
    with ITM3900D("sim", transport=t, timeout=1000) as d:
        original = d.client.query
        seen = []
        def query(command, **kwargs):
            seen.append(kwargs)
            return original(command, **kwargs)
        monkeypatch.setattr(d.client, "query", query)
        assert d.query_scpi("*IDN?", delay=.25) == "ID"
        assert seen == [{"timeout_s": .75}]
        assert d.query_scpi("*IDN?") == "ID"
        assert seen[-1] == {}
    assert t.history == ["*IDN?", "*IDN?"]


def test_overslept_deadline_never_transmits(monkeypatch):
    now = [0.]
    monkeypatch.setattr(base, "time", SimpleNamespace(monotonic=lambda: now[0],
                        sleep=lambda _: now.__setitem__(0, 2.0)))
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t, timeout=1000) as d:
        with pytest.raises(TimeoutError, match="before transmission"):
            d.query_scpi("*IDN?", delay=.25)
        assert d.session.is_connected
    assert t.history == []


def test_delay_and_query_are_serialized(monkeypatch):
    entered, release, other_started = threading.Event(), threading.Event(), threading.Event()
    def sleep(_):
        entered.set()
        assert release.wait(2)
    monkeypatch.setattr(base, "time", SimpleNamespace(monotonic=lambda: 0., sleep=sleep))
    t = ScriptedScpiTransport().on("*IDN?", "ID").on("OUTP:STAT?", "0")
    errors = []
    with ITM3900D("sim", transport=t, timeout=1000) as d:
        def run(cmd, delay):
            try:
                if not delay:
                    other_started.set()
                d.query_scpi(cmd, delay=delay)
            except BaseException as exc:
                errors.append(exc)
        first = threading.Thread(target=run, args=("*IDN?", .1))
        second = threading.Thread(target=run, args=("OUTP:STAT?", 0))
        first.start()
        try:
            assert entered.wait(2)
            second.start()
            assert other_started.wait(2)
            assert t.history == []
        finally:
            release.set()
            first.join(3)
            second.join(3)
        assert not first.is_alive() and not second.is_alive()
        assert not errors
    assert t.history == ["*IDN?", "OUTP:STAT?"]


def test_delayed_query_timeout_no_replay(monkeypatch):
    monkeypatch.setattr(base, "time", SimpleNamespace(monotonic=lambda: 0., sleep=lambda _: None))
    def fail(_):
        raise TransportTimeoutError("lost response")
    t = ScriptedScpiTransport().on("*ESR?", fail)
    with ITM3900D("sim", transport=t, timeout=1000) as d:
        with pytest.raises(TimeoutError):
            d.query_scpi("*ESR?", delay=.1)
        assert not d.session.is_connected
    assert t.history == ["*ESR?"]
