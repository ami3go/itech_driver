from itm3900d import ITM3900D


def test_invoke_formats_set_command():
    psu = ITM3900D(dry_run=True, strict=False)
    psu.open()
    psu.invoke("source_voltage_level_immediate_amplitude", 5.0)
    assert "SOURce:VOLTage:LEVel:IMMediate:AMPLitude 5.0" in psu.dry_run_writes


def test_dynamic_proxy_query():
    psu = ITM3900D(dry_run=True, strict=False)
    psu.open()
    psu.scpi.source_voltage_level_immediate_amplitude_query()
    assert "SOURce:VOLTage:LEVel:IMMediate:AMPLitude?" in psu.dry_run_writes
