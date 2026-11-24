import pytest
from itech_driver import ITM3900D
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport


@pytest.mark.parametrize("coefficient",["MX","MB"])
@pytest.mark.parametrize("value",[-9000,0,9000])
def test_coefficient(coefficient,value):
    h=f"SOUR:EXT:PROG:CHAN:{coefficient}"
    t=ScriptedScpiTransport().on("OUTP:STAT?","0").on("SOUR:EXT:PROG?","0").on(f"{h} 2,{value}").on(f"{h}? 2",str(value))
    with ITM3900D("sim",transport=t) as d:
        d.source.external_coefficient_set(2,coefficient,value,option_confirmed=True,deenergized_confirmed=True)
        assert d.source.external_coefficient_query(2,coefficient)==value
        assert t.history==["OUTP:STAT?","SOUR:EXT:PROG?",f"{h} 2,{value}",f"{h}? 2"]


def test_enable_requires_explicit_confirmations():
    t=ScriptedScpiTransport().on("OUTP:STAT?","0").on("SOUR:EXT:PROG 1")
    with ITM3900D("sim",transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.source.external_programming_set(True)
        assert t.history==[]
        d.source.external_programming_set(True,wiring_confirmed=True,deenergized_confirmed=True,option_confirmed=True)
        assert t.history==["OUTP:STAT?","SOUR:EXT:PROG 1"]


def test_reject_energized_or_invalid():
    t=ScriptedScpiTransport().on("OUTP:STAT?","1")
    with ITM3900D("sim",transport=t) as d:
        for ch,coef,v in [(0,"MX",1),(1,"MX",9001),(1,"MB",float("nan")),(1,"MX;*RST",1)]:
            with pytest.raises(ConfigurationError):
                d.source.external_coefficient_set(ch,coef,v,option_confirmed=True,deenergized_confirmed=True)
        assert t.history==[]
        with pytest.raises(ConfigurationError):
            d.source.external_programming_set(True,wiring_confirmed=True,deenergized_confirmed=True,option_confirmed=True)
        assert t.history==["OUTP:STAT?"]
