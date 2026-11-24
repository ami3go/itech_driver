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
