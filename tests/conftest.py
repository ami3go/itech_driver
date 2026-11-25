import pytest


def pytest_addoption(parser):
    group = parser.getgroup("itech-hil")
    group.addoption("--hil-config")
    group.addoption("--hil-authority")
    group.addoption("--hil-key")
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
    approved_hil_config(config)
    for option in ("--hil-interface", "--hil-address", "--hil-serial"):
        if not config.getoption(option):
            raise pytest.UsageError(f"{option} is required with --run-hil")
    if not 1 <= config.getoption("--hil-timeout") <= 10000:
        raise pytest.UsageError("--hil-timeout must be 1..10000 ms")


def approved_hil_config(config):
    from pathlib import Path
    from itech_driver.hil_authorization import read_object, validate, validate_pytest
    get = config.getoption
    root = Path(__file__).resolve().parents[1]
    try:
        paths = [get("--hil-authority"), get("--hil-key")]
        if any(not p or Path(p).resolve().is_relative_to(root) for p in paths):
            raise ValueError("external authorization files required")
        if not get("--hil-config"):
            raise ValueError("bench configuration required")
        bench = read_object(get("--hil-config"))
        validate(paths[0], bench, paths[1])
        validate_pytest(bench, get)
        return bench
    except (ValueError, OSError, KeyError, TypeError):
        raise pytest.UsageError("HIL authorization or bench scope rejected") from None


def pytest_runtest_setup(item):
    if "hardware" in item.keywords and item.config.getoption("--run-hil"):
        approved_hil_config(item.config)
