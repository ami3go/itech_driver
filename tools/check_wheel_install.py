"""Install built wheel in an isolated environment without transport extras."""
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
from importlib.metadata import metadata
assert metadata("itech-itm3900d-driver")["Requires-Python"] == ">=3.10"
"""], check=True, cwd=tmp)
