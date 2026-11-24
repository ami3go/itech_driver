import pytest


def pytest_addoption(parser):
    group = parser.getgroup("itech-hil")
    group.addoption("--run-hil", action="store_true", help="operator authorizes physical communication")
    group.addoption("--hil-interface", choices=["usbtmc", "visa-lan", "tcp", "vcp"])
    group.addoption("--hil-address")
    group.addoption("--hil-serial")
    group.addoption("--hil-timeout", type=int, default=2000)
    group.addoption("--hil-tcp-port", type=int, default=30000)
    group.addoption("--hil-baudrate", type=int, default=9600)
    group.addoption("--hil-bytesize", type=int, default=8)
    group.addoption("--hil-parity", default="N")
    group.addoption("--hil-stopbits", type=int, default=1)
    group.addoption("--hil-termination", choices=["lf", "crlf"], default="lf")
    group.addoption("--hil-remote-local", action="store_true",
                    help="additional operator authorization for remote/local panel transitions")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-hil"):
        for item in items:
            if "hardware" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="explicit --run-hil required"))
        return
    for option in ("--hil-interface", "--hil-address", "--hil-serial"):
        if not config.getoption(option):
            raise pytest.UsageError(f"{option} is required with --run-hil")
    if not 1 <= config.getoption("--hil-timeout") <= 10000:
        raise pytest.UsageError("--hil-timeout must be 1..10000 ms")
