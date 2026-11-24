from importlib.metadata import version
from itech_driver import __version__


def test_runtime_matches_distribution():
    assert __version__ == version("itech-itm3900d-driver")
