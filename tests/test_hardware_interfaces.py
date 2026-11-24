"""Operator-only physical communication checks, never normal CI."""
import importlib.metadata
import platform
import time
import pytest

from itech_driver import ITM3900D, connect_tcp, connect_vcp
from itech_driver.identity import is_itm3900d
from scpi_driver_core.scpi.parsers import parse_identity

pytestmark = pytest.mark.hardware


@pytest.fixture
def selected_driver(request, record_property):
    get = request.config.getoption
    if not get("--run-hil"):
        pytest.skip("physical communication not authorized")
    interface = get("--hil-interface")
    address = get("--hil-address")
    timeout = get("--hil-timeout")
    expected = get("--hil-serial")
    if interface == "usbtmc" and not (address.upper().startswith("USB") and address.upper().endswith("::INSTR")):
        pytest.fail("USBTMC requires explicit USB INSTR resource")
    if interface == "visa-lan" and not (address.upper().startswith("TCPIP") and address.upper().endswith("::INSTR")):
        pytest.fail("VISA LAN requires explicit TCPIP INSTR resource")
    if interface == "vcp" and "://" in address:
        pytest.fail("physical VCP requires a local OS device path, not a URL")
    record_property("interface", interface)
    record_property("address", address)
    record_property("os", platform.platform())
    record_property("python", platform.python_version())
    record_property("timeout_ms", timeout)
    for package in ("itech-itm3900d-driver", "scpi-driver-core", "pyvisa", "pyserial"):
        try:
            record_property(package, importlib.metadata.version(package))
        except importlib.metadata.PackageNotFoundError:
            pass
    if interface == "tcp":
        d = connect_tcp(address, get("--hil-tcp-port"), timeout=timeout, require_remote=True)
    elif interface == "vcp":
        d = connect_vcp(address, timeout=timeout, baudrate=get("--hil-baudrate"),
                        bytesize=get("--hil-bytesize"), parity=get("--hil-parity"),
                        stopbits=get("--hil-stopbits"), termination="\n" if get("--hil-termination") == "lf" else "\r\n",
                        require_remote=True)
    else:
        d = ITM3900D(address, timeout=timeout, require_remote=True)
    with d:
        identity = parse_identity(d.identify())
        assert is_itm3900d(identity), "unexpected model"
        assert identity.serial_number == expected, "unexpected serial"
        record_property("idn", identity.raw)
        yield d, identity
    assert not d.session.is_connected


def test_physical_read_only_identity(selected_driver, record_property):
    d, expected = selected_driver
    start = time.monotonic()
    assert parse_identity(d.identify()) == expected
    record_property("second_idn_elapsed_s", time.monotonic() - start)
    assert d.requested_mode is None


def test_physical_remote_local(request, record_property):
    if not request.config.getoption("--run-hil") or not request.config.getoption("--hil-remote-local"):
        pytest.skip("remote/local panel transition not additionally authorized")
    d, _ = request.getfixturevalue("selected_driver")
    with d.remote_mode():
        assert d.requested_mode == "remote"
    assert d.requested_mode == "local"
    record_property("panel_state", "NOT VERIFIED: operator observation required")
