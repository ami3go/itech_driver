import pytest
from itech_driver.identity import is_itm3900d
from itech_driver.capabilities import RATINGS
from scpi_driver_core.scpi.parsers import parse_identity


@pytest.mark.parametrize("model",sorted(RATINGS))
def test_registered_model(model):
    assert is_itm3900d(parse_identity(f"ITECH,{model},S,1"))


@pytest.mark.parametrize("manufacturer,model",[
    ("ITECH","IT-M3900D"),("ITECH","IT-M3902D-80-41"),
    ("ITECH","IT-M3902D-80-40-UNKNOWN"),("ITECH","IT-M3902D"),
    ("ITECH LAB","IT-M3902D-80-40"),("OTHER","IT-M3902D-80-40")])
def test_near_match(manufacturer,model):
    assert not is_itm3900d(parse_identity(f"{manufacturer},{model},S,1"))
