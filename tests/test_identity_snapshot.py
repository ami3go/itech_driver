from dataclasses import FrozenInstanceError

import pytest
from scpi_driver_core import IdentityError, SessionClosedError, TransportTimeoutError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import GenericSCPIInstrument, ITM3900D
from itech_driver.exceptions import TimeoutError


def test_immutable_core_snapshot_cached_per_generation():
    t = ScriptedScpiTransport().on("*IDN?", 'ITECH,UNKNOWN,"S,1",1.0')
    with GenericSCPIInstrument("sim", transport=t) as d:
        first = d.identity_snapshot()
        assert first.serial_number == "S,1"
        assert d.identity_snapshot() is first
        with pytest.raises(FrozenInstanceError):
            first.model = "changed"
        a = d.get_instrument_info(refresh=False)
        a["capabilities"]["output_control"] = True
        assert d.get_instrument_info(refresh=False)["capabilities"]["output_control"] is None
        assert t.history == ["*IDN?"]
        d.session.close()
        t.on("*IDN?", "OTHER,UNKNOWN,S2,2.0")
        d.session.open()
        second = d.identity_snapshot()
        assert second.serial_number == "S2"
        assert second is not first
        assert t.history == ["*IDN?", "*IDN?"]


def test_failed_refresh_does_not_reuse_previous_snapshot():
    t = ScriptedScpiTransport().on("*IDN?", "ITECH,UNKNOWN,S1,1")
    with GenericSCPIInstrument("sim", transport=t) as d:
        d.identity_snapshot()
        t.on("*IDN?", "bad")
        with pytest.raises(IdentityError):
            d.identity_snapshot(refresh=True)
        t.on("*IDN?", "ITECH,UNKNOWN,S2,2")
        assert d.identity_snapshot().serial_number == "S2"
        assert t.history == ["*IDN?"] * 3


def test_faulted_identity_preserves_timeout_and_invalidates_remote():
    t = ScriptedScpiTransport().on("*IDN?", "ITECH,IT-M3902D-80-40,S1,1")
    t.on("SYST:REM")
    with ITM3900D("sim", transport=t, require_remote=True) as d:
        d.enter_remote()
        assert d.identity_snapshot().model == "IT-M3902D-80-40"
        def fail(_):
            raise TransportTimeoutError("lost identity")
        t.on("*IDN?", fail)
        with pytest.raises(TimeoutError) as error:
            d.identity_snapshot(refresh=True)
        assert isinstance(error.value.__cause__, TransportTimeoutError)
        assert d.requested_mode is None
        with pytest.raises(SessionClosedError):
            d.identity_snapshot()
        assert t.history == ["SYST:REM", "*IDN?", "*IDN?"]
