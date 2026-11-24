import pytest
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.protection import ProtectionThresholdQualification
from itech_driver.capabilities import Range

QUAL = ProtectionThresholdQualification("IT-M3902D-80-40", "1", "opp", Range(0, 100), "synthetic test only")


def test_limit_and_opp_are_distinct():
    t = ScriptedScpiTransport().on("*IDN?", "ITECH,IT-M3902D-80-40,SIM,1")
    t.on("SOUR:POW:LIM? MIN", "0").on("SOUR:POW:LIM? MAX", "100")
    t.on("SOUR:POW:LIM 20").on("SOUR:POW:LIM?", "20")
    t.on("SOUR:POW:OVER:PROT:LEV 25").on("SOUR:POW:OVER:PROT:LEV?", "25")
    t.on("SOUR:POW:OVER:PROT:STAT 1").on("SOUR:POW:OVER:PROT:STAT?", "1")
    with ITM3900D("sim", transport=t) as d:
        d.source.output_power_limit_set(20)
        d.source.opp_threshold_set(25, qualification=QUAL)
        assert d.source.output_power_limit_query() == 20
        assert d.source.opp_threshold_query() == 25
        d.source.opp_enable(True)
        assert d.source.opp_enable_query()
        assert t.history == ["*IDN?", "SOUR:POW:LIM? MIN", "SOUR:POW:LIM? MAX", "SOUR:POW:LIM 20", "SOUR:POW:OVER:PROT:LEV 25",
                             "SOUR:POW:LIM?", "SOUR:POW:OVER:PROT:LEV?",
                             "SOUR:POW:OVER:PROT:STAT 1", "SOUR:POW:OVER:PROT:STAT?"]


def test_legacy_power_limit_warns_without_silent_semantic_change():
    t = ScriptedScpiTransport().on("*IDN?", "ITECH,IT-M3902D-80-40,SIM,1").on("SOUR:POW:OVER:PROT:LEV 25")
    with ITM3900D("sim", transport=t) as d:
        with pytest.warns(DeprecationWarning):
            d.source.power_limit_set(25, qualification=QUAL)
        assert t.history == ["*IDN?", "SOUR:POW:OVER:PROT:LEV 25"]
