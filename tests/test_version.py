from importlib.metadata import version
from itech_driver import __version__


def test_runtime_matches_distribution():
    assert __version__ == version("itech-itm3900d-driver")



def test_uninstalled_source_reports_unknown_without_inventing_release():
    import subprocess
    import sys
    subprocess.run([sys.executable, "-c", """
import importlib.metadata as metadata
real = metadata.version
def missing(name):
    if name == "itech-itm3900d-driver":
        raise metadata.PackageNotFoundError(name)
    return real(name)
metadata.version = missing
import itech_driver
assert itech_driver.__version__ == "0+unknown"
"""], check=True)
