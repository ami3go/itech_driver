from types import SimpleNamespace
import pytest
from scpi_driver_core import ConfigurationError
import scpi_driver_core.transport.serial as serial_module
from itech_driver import connect_vcp


def test_vcp_settings_and_framing(monkeypatch):
    class Backend:
        def open(self):
            self.opened = True
            self.writes = []
        def write(self, data):
            self.writes.append(data)
            return len(data)
        def read_until(self, expected, size):
            assert expected == b"\r\n"
            return b"ITECH,IT-M3902D-80-40,SIM,1.0\r\n"
        def close(self):
            self.opened = False
    backend = Backend()
    monkeypatch.setattr(serial_module, "_load_serial",
                        lambda: SimpleNamespace(serial_for_url=lambda *a, **k: backend))
    with connect_vcp("COM5", baudrate=19200, bytesize=7, parity="E",
                     stopbits=2, termination="\r\n", dtr=False, rts=False) as d:
        assert d.identify().startswith("ITECH,")
        assert backend.writes == [b"*IDN?\r\n"]
        assert (backend.baudrate, backend.bytesize, backend.parity, backend.stopbits) == (19200, 7, "E", 2)
        assert backend.dtr is False and backend.rts is False
    assert not backend.opened


def test_real_pyserial_loopback():
    with connect_vcp("loop://", timeout=1000) as d:
        # Echo exercises actual serial framing, not an instrument identity.
        assert d.query_scpi("*IDN?") == "*IDN?"


@pytest.mark.parametrize("settings", [{"baudrate": 0}, {"bytesize": 9}, {"parity": "X"}, {"stopbits": 3}, {"termination": ""}, {"timeout": 0}])
def test_reject_settings_before_open(settings):
    with pytest.raises(ConfigurationError):
        connect_vcp("COM5", **settings)
