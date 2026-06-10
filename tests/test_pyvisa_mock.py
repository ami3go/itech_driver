from itm3900d import ITM3900D


def test_dry_run_idn():
    psu = ITM3900D(dry_run=True, strict=False)
    psu.open()
    assert "ITECH" in psu.idn()
