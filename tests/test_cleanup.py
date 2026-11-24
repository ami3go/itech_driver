import pytest
from itech_driver import ITM3900D
from scpi_driver_core.simulation import ScriptedScpiTransport


def test_context_preserves_primary_error(monkeypatch):
    d=ITM3900D("sim",transport=ScriptedScpiTransport())
    def fail():
        raise RuntimeError("cleanup failure")
    try:
        with monkeypatch.context() as m:
            m.setattr(d,"close",fail)
            with pytest.raises(ValueError,match="primary") as result:
                with d:
                    raise ValueError("primary")
            exc=result.value
            assert ("cleanup failure" in str(getattr(exc,"__notes__",[]))
                    or str(getattr(exc,"cleanup_error",None))=="cleanup failure")
    finally:
        d.close()


def test_cleanup_failure_without_primary_is_visible(monkeypatch):
    d=ITM3900D("sim",transport=ScriptedScpiTransport())
    def fail():
        raise RuntimeError("cleanup failure")
    try:
        with monkeypatch.context() as m:
            m.setattr(d,"close",fail)
            with pytest.raises(RuntimeError,match="cleanup failure"):
                with d:
                    pass
    finally:
        d.close()


def test_repeated_close():
    t=ScriptedScpiTransport()
    d=ITM3900D("sim",transport=t)
    d.close()
    d.close()
    assert not t.is_open


def test_shared_visa_manager_not_closed_by_driver():
    from pathlib import Path
    import pyvisa
    fixture = Path(__file__).with_name("itech_sim.yaml").resolve()
    manager = pyvisa.ResourceManager(f"{fixture}@sim")
    try:
        with ITM3900D("GPIB0::9::INSTR", resource_manager=manager) as first:
            with ITM3900D("USB0::0x1234::0x5678::SIM001::INSTR", resource_manager=manager) as second:
                first.close()
                first.close()
                assert not first.session.is_connected
                assert second.identity_snapshot().model == "IT-M3902D-80-40"
        assert manager.list_resources()
    finally:
        manager.close()


def test_primary_error_survives_interrupt_during_close(monkeypatch):
    d = ITM3900D("sim", transport=ScriptedScpiTransport())
    def fail():
        raise KeyboardInterrupt("cleanup interrupted")
    try:
        with monkeypatch.context() as m:
            m.setattr(d, "close", fail)
            with pytest.raises(ValueError, match="primary") as caught:
                with d:
                    raise ValueError("primary")
            assert ("cleanup interrupted" in str(getattr(caught.value, "__notes__", []))
                    or str(getattr(caught.value, "cleanup_error", None)) == "cleanup interrupted")
    finally:
        d.close()
