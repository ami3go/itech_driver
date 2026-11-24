"""ITECH IT-M3900D series power supply driver."""

from typing import Any, List, Optional, Union
from ..base import BaseInstrument, Number, BoolLike
from ..subsystems.ArbSubsystem import ArbSubsystem
from ..subsystems.AbortSubsystem import AbortSubsystem
from ..subsystems.BatterySubsystem import BatterySubsystem
from ..subsystems.IEEE488 import IEEE488
from ..subsystems.InitiateSubsystem import InitiateSubsystem
from ..subsystems.IOConfigSubsystem import IOConfigSubsystem
from ..subsystems.OutputSubsystem import OutputSubsystem
from ..subsystems.SourceSubsystem import SourceSubsystem
from ..subsystems.StatusSubsystem import StatusSubsystem
from ..subsystems.SystemSubsystem import SystemSubsystem
from ..subsystems.TriggerSubsystem import TriggerSubsystem
# from ..subsystems. import


class ITM3900D(BaseInstrument):
    """ITECH IT-M3900D series power supply."""
    
    def __init__(self, resource_name: str, timeout: int = 5000, 
                 termination: str = '\n', interface_kwargs: dict = None, **kwargs):
        super().__init__(resource_name, timeout, termination, interface_kwargs, **kwargs)
        
        # Initialize subsystems
        self.system = SystemSubsystem(self)
        self.source = SourceSubsystem(self)
        self.output = OutputSubsystem(self)
        
        # IT-M3900D specific subsystems
        self.status = StatusSubsystem(self)
        self.trigger = TriggerSubsystem(self)
        self.arb = ArbSubsystem(self)
        self.battery = BatterySubsystem(self)
        self.initiate = InitiateSubsystem(self)
        self.abort = AbortSubsystem(self)
        self.io = IOConfigSubsystem(self)
        self.ieee = IEEE488(self)

