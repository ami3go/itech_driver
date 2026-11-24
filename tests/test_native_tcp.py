import socket
import threading

import pytest
from scpi_driver_core import ConfigurationError
from itech_driver import connect_tcp


def test_native_tcp_fragmented_reply_and_close():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        listener.settimeout(3)
        received = []
        errors = []

        def server():
            try:
                with listener.accept()[0] as conn:
                    conn.settimeout(3)
                    with conn.makefile("rb") as stream:
                        received.append(stream.readline())
                        conn.sendall(b"ITECH,IT-M3902D-80-40,")
                        conn.sendall(b"SIM,1.0\n")
                        received.append(stream.readline())
            except Exception as exc:
                errors.append(exc)

        worker = threading.Thread(target=server, daemon=True)
        worker.start()
        with connect_tcp("127.0.0.1", listener.getsockname()[1], timeout=1000) as d:
            assert d.identify() == "ITECH,IT-M3902D-80-40,SIM,1.0"
        worker.join(4)
        assert not worker.is_alive()
        assert not errors
        assert received == [b"*IDN?\n", b""]


@pytest.mark.parametrize("port", [0, 65536, True, 3.5])
def test_invalid_port(port):
    with pytest.raises(ConfigurationError):
        connect_tcp("127.0.0.1", port)
