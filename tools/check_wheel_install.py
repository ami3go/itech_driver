"""Verify installed wheel in isolated minimal and transport-extra environments."""
import pathlib
import subprocess
import sys
import tempfile
import venv

root = pathlib.Path(__file__).resolve().parents[1]
wheels = list((root / "dist").glob("*.whl"))
assert len(wheels) == 1, wheels
with tempfile.TemporaryDirectory() as tmp:
    env = pathlib.Path(tmp) / "env"
    venv.EnvBuilder(with_pip=True).create(env)
    python = env / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", str(wheels[0])], check=True, cwd=tmp)
    subprocess.run([str(python), "-m", "pip", "check"], check=True, cwd=tmp)
    subprocess.run([str(python), "-c", """
import importlib.util
from itech_driver import ITM3900D, connect_tcp
assert callable(connect_tcp)
assert importlib.util.find_spec("pyvisa") is None, "VISA unexpectedly mandatory"
assert importlib.util.find_spec("serial") is None, "serial unexpectedly mandatory"
assert importlib.util.find_spec("logger") is None
from importlib.metadata import metadata, version
from itech_driver import __version__
assert __version__ == version("itech-itm3900d-driver")
assert metadata("itech-itm3900d-driver")["Requires-Python"] == ">=3.10"
"""], check=True, cwd=tmp)

    subprocess.run([str(python), "-c", """
import importlib
import pkgutil
import itech_driver
from itech_driver import ITM3900D
from itech_driver.simulator import ItechSimulator
for module in pkgutil.walk_packages(itech_driver.__path__, itech_driver.__name__ + "."):
    importlib.import_module(module.name)
sim = ItechSimulator()
with ITM3900D("sim", transport=sim.transport) as driver:
    assert "SIMULATED" in driver.identify()
    assert driver.measurement.voltage() == 0
assert sim.transport.history == ["*IDN?", "MEAS:VOLT?"]
"""], check=True, cwd=tmp)
    for name in ("itech-control", "itech-discover"):
        command = python.parent / (name + (".exe" if sys.platform == "win32" else ""))
        subprocess.run([str(command), "--help"], check=True, cwd=tmp)

    # Upgrade the clean environment only after proving the minimal contract.
    subprocess.run([str(python), "-m", "pip", "install", str(wheels[0]) + "[discovery]", "pyvisa-sim>=0.7.1"],
                   check=True, cwd=tmp)
    subprocess.run([str(python), "-m", "pip", "check"], check=True, cwd=tmp)
    subprocess.run([str(python), "-c", """
import sys
from pathlib import Path
from itech_driver import ITM3900D, connect_vcp
import pyvisa
import serial
import zeroconf
fixture = Path(sys.argv[1])
for resource in ("USB0::0x1234::0x5678::SIM001::INSTR", "TCPIP0::127.0.0.1::inst0::INSTR"):
    with ITM3900D(resource, visa_library=f"{fixture}@sim", timeout=1000) as driver:
        assert driver.identity_snapshot().model == "IT-M3902D-80-40"
        assert driver.output.state_query() is False
with connect_vcp("loop://", timeout=1000) as driver:
    assert driver.query_scpi("*IDN?") == "*IDN?"
""", str(root / "tests" / "itech_sim.yaml")], check=True, cwd=tmp)
