from itm3900d import ITM3900D


def test_no_output_on_during_connect():
    psu = ITM3900D(dry_run=True, strict=False)
    psu.open()
    joined = "\n".join(psu.dry_run_writes).upper()
    assert "OUTP ON" not in joined
    assert "OUTP 1" not in joined
