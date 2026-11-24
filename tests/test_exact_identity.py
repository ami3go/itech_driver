import pytest
from scpi_driver_core.scpi.parsers import parse_identity
from itech_driver.identity import is_itm3900d
from itech_driver.capabilities import RATINGS


@pytest.mark.parametrize("model",sorted(RATINGS))
def test_exact_known_model(model):
    assert is_itm3900d(parse_identity(f"ITECH,{model},S,1.0"))


@pytest.mark.parametrize("manufacturer,model",[
    ("OTHER","IT-M3902D-80-40"),("ITECH CLONE","IT-M3902D-80-40"),
    ("ITECH","IT-M3900D"),("ITECH","IT-M3902D-80-41"),
    ("ITECH","IT-M3902D-80-40-FAKE"),("ITECH","ITM3902D-80-40"),
    ("ITECH","XIT-M3902D-80-40"),("ITECH","IT-M3909D-80-40")])
def test_near_matches_not_specialized(manufacturer,model):
    assert not is_itm3900d(parse_identity(f"{manufacturer},{model},S,1.0"))
