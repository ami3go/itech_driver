import pytest
from itech_driver import ITM3900D
from itech_driver.simulator import ItechSimulator
from itech_driver.output_lifecycle import request_output_off
from itech_driver.exceptions import TimeoutError


def test_state_and_error_queue():
    sim=ItechSimulator()
    with ITM3900D("sim",transport=sim.transport) as d:
        d.write_scpi("SOUR:VOLT 5")
        d.write_scpi("SOUR:CURR 2")
        d.write_scpi("OUTP:STAT ON")
        assert d.query_scpi("MEAS:POW?")=="10.0"
        d.write_scpi("SOUR:VOLT 999")
        assert d.query_scpi("SYST:ERR?").startswith("-222")
        assert d.query_scpi("SOUR:VOLT?")=="5.0"
        sim.inject_trip()
        assert d.query_scpi("OUTP:STAT?")=="1"
        assert float(d.query_scpi("MEAS:VOLT?"))==0
        assert request_output_off(d,max_residual_v=0,max_residual_a=0).outcome=="instrument_below_limits"


def test_external_trigger_and_finite_ticks():
    sim=ItechSimulator()
    with ITM3900D("sim",transport=sim.transport) as d:
        d.write_scpi("TRIG:ARB:SOUR EXT")
        d.write_scpi("ARB:COUNT 2")
        d.write_scpi("INIT:ARB")
        d.write_scpi("*TRG")
        assert d.query_scpi("ARB:EXE:STAT?")=="ARMED"
        sim.external_trigger()
        sim.tick()
        assert d.query_scpi("ARB:EXE:STAT?")=="RUNNING"
        sim.tick()
        assert d.query_scpi("ARB:EXE:STAT?")=="COMPLETE"
        d.write_scpi("ABOR:ARB")
        assert d.query_scpi("ARB:EXE:STAT?")=="ABORTED"


def test_timeout_does_not_replay():
    sim=ItechSimulator()
    sim.fail_next_query("*IDN?")
    with ITM3900D("sim",transport=sim.transport) as d:
        with pytest.raises(TimeoutError):
            d.identify()
        assert sim.transport.history==["*IDN?"]
        assert not d.session.is_connected
