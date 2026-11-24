import pytest
from scpi_driver_core import ConfigurationError
from itech_driver.parallel import ParallelMember, ParallelTopology

MODEL="IT-M3902D-80-40"
MASTER=ParallelMember(MODEL,"A","master")
SLAVE=ParallelMember(MODEL,"B","slave")


def test_identical_topology():
    assert ParallelTopology((MASTER,SLAVE)).validate(approved_max_units=2)==MASTER


@pytest.mark.parametrize("members",[
    (MASTER,), (MASTER,MASTER), (SLAVE,SLAVE),
    (MASTER,ParallelMember("IT-M3904D-80-80","B","slave")),
    (MASTER,ParallelMember(MODEL,"A","slave")),
    (MASTER,ParallelMember(MODEL,"","slave")),
    (MASTER,ParallelMember(MODEL,"B","master"))])
def test_invalid_topology(members):
    with pytest.raises(ConfigurationError):
        ParallelTopology(members).validate(approved_max_units=2)


def test_capacity():
    with pytest.raises(ConfigurationError):
        ParallelTopology((MASTER,SLAVE,ParallelMember(MODEL,"C","slave"))).validate(approved_max_units=2)
