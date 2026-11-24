import socket
import struct
import threading

import pytest
from itech_driver import ITM3900D, connect_tcp
from itech_driver.exceptions import TimeoutError


def run_exchange(replies, action, *, timeout=1000):
    """Loopback only. Assert exact wire command framing, including binary follow-up."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(3)
        errors = []
        history = []

        def serve():
            try:
                with listener.accept()[0] as peer:
                    peer.settimeout(3)
                    with peer.makefile("rb") as stream:
                        for command, chunks in replies:
                            actual = stream.readline()
                            history.append(actual)
                            assert actual == command
                            for chunk in chunks:
                                peer.sendall(chunk)
                        assert stream.readline() == b""
            except Exception as exc:
                errors.append(exc)

        worker = threading.Thread(target=serve, daemon=True)
        worker.start()
        try:
            with ITM3900D(f"tcp://127.0.0.1:{listener.getsockname()[1]}",
                           timeout=timeout, command_termination="\r\n",
                           response_termination="\n") as driver:
                action(driver)
        finally:
            worker.join(4)
        assert not worker.is_alive()
        assert not errors
        assert history == [command for command, _ in replies]


def test_asymmetric_fragmented_text_and_binary_then_text():
    payload = struct.pack("<ff", 1.5, 2.5)
    def action(driver):
        assert driver.identify() == "ITECH,IT-M3902D-80-40,SIM,1"
        assert driver.query_binary("MEAS:ARR:VOLT?") == [1.5, 2.5]
        assert driver.query_scpi("OUTP:STAT?") == "0"

    run_exchange([
        (b"*IDN?\r\n", [b"ITECH,IT-M3902", b"D-80-40,SIM,1", b"\n"]),
        (b"MEAS:ARR:VOLT?\r\n", [b"#", b"18", payload[:3], payload[3:], b"\n"]),
        (b"OUTP:STAT?\r\n", [b"0\n"]),
    ], action)


def test_missing_response_terminator_faults_without_replay():
    def action(driver):
        with pytest.raises(TimeoutError):
            driver.identify()
        assert not driver.session.is_connected
    run_exchange([(b"*IDN?\r\n", [b"ITECH,IT-M3902D-80-40,SIM,1"])], action, timeout=150)
