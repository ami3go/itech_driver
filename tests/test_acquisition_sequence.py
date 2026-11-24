import threading
import pytest
from scpi_driver_core import ConfigurationError, TransportTimeoutError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.exceptions import TimeoutError
from itech_driver.acquisition import AcquisitionConfig, configure_and_arm


COMMANDS = ["SENS:ACQ:POIN 100", "SENS:ACQ:OFFS:POIN -2",
            "SENS:ACQ:TINT 0.01", "TRIG:ACQ:SOUR BUS", "INIT:ACQ"]


def config():
    return AcquisitionConfig(100, -2, .01, "BUS")


def transport():
    t = ScriptedScpiTransport()
    for cmd in COMMANDS:
        t.on(cmd)
    return t


@pytest.mark.parametrize("args", [
    (0, 0, .01, "BUS"), (True, 0, .01, "BUS"), (1.5, 0, .01, "BUS"),
    (10**1000, 0, .01, "BUS"), (10, True, .01, "BUS"),
    (10, 0, float("inf"), "BUS"), (10, 0, .01, "IMM"), (10, 0, .01, "invalid"),
])
def test_validate_all_before_io(args):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            configure_and_arm(d, AcquisitionConfig(*args))
    assert t.history == []


def test_configure_and_arm_does_not_trigger():
    t = transport().on("*TRG")
    with ITM3900D("sim", transport=t) as d:
        configure_and_arm(d, config())
        assert t.history == COMMANDS
        d.ieee.trigger()
    assert t.history == COMMANDS + ["*TRG"]


@pytest.mark.parametrize("failure", COMMANDS)
def test_fault_each_step_never_continues_or_replays(failure):
    t = transport()
    def fail(_):
        raise TransportTimeoutError("lost")
    t.on(failure, fail)
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(TimeoutError):
            configure_and_arm(d, config())
        assert not d.session.is_connected
    assert t.history == COMMANDS[:COMMANDS.index(failure)+1]
    assert "*TRG" not in t.history


def test_other_thread_cannot_interleave_compound_sequence():
    entered, release, attempting, second_done = (threading.Event() for _ in range(4))
    t = transport().on("*IDN?", "ID")
    errors = []
    def block(_):
        entered.set()
        assert release.wait(2)
    t.on(COMMANDS[0], block)
    with ITM3900D("sim", transport=t) as d:
        def first():
            try:
                configure_and_arm(d, config())
            except BaseException as exc:
                errors.append(exc)
        def second():
            try:
                attempting.set()
                d.identify()
            except BaseException as exc:
                errors.append(exc)
            finally:
                second_done.set()
        a, b = threading.Thread(target=first), threading.Thread(target=second)
        a.start()
        try:
            assert entered.wait(2)
            b.start()
            assert attempting.wait(2)
            # Scripted transport history takes the same transport lock as the
            # blocked handler; inspecting it here would deadlock the test.
            assert not second_done.wait(.05)
        finally:
            release.set()
            a.join(3)
            b.join(3)
        assert not a.is_alive() and not b.is_alive()
        assert not errors
    assert t.history == COMMANDS + ["*IDN?"]
