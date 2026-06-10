# itm3900d

Production-intent Python/PyVISA driver for the **ITECH IT-M3900D Series** high-power programmable DC power supply.

> Safety: this package is a software guard, not a substitute for external interlocks, fuses, emergency-stop wiring, proper insulation, and trained operators. The driver never enables output during construction, discovery, connection, reset, reconnect, or context-manager entry.

## Install

From this generated folder:

```bash
pip install -e .
```

For a real instrument you also need a VISA backend such as NI-VISA or pyvisa-py:

```bash
pip install pyvisa pyvisa-py
```

## USB safe example

```python
from itm3900d import ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=30.0, max_current_a=5.0, max_power_w=100.0)

with ITM3900D.open_usb(safety=policy, allow_output_enable=False) as psu:
    print(psu.idn())
    psu.configure_cv(voltage=12.0, current_limit=2.0, power_limit=50.0)
    print(psu.measure_voltage())
    psu.output_off()
```

## Ethernet socket example

```python
from itm3900d import ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=10.0, max_current_a=1.0, max_power_w=10.0)

psu = ITM3900D.open_ethernet(
    "192.168.0.50",
    lan_mode="socket",
    port=5025,
    safety=policy,
    allow_output_enable=False,
)
print(psu.idn())
psu.configure_cv(voltage=5.0, current_limit=1.0, power_limit=5.0)
psu.output_off()
psu.close()
```

## Explicit output enable

```python
from itm3900d import ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=5.5, max_current_a=0.5, max_power_w=3.0)
psu = ITM3900D.open_usb(safety=policy, allow_output_enable=True)
psu.configure_cv(voltage=5.0, current_limit=0.2, power_limit=2.0)

answer = input("Type ENABLE to turn output ON: ")
if answer == "ENABLE":
    psu.output_on(confirm=True)

psu.output_off(verify=True)
psu.close()
```

## Dynamic SCPI catalog

All commands extracted from the task file are present in `itm3900d.command_catalog.COMMANDS` and callable via `invoke()` or `psu.scpi.<catalog_key>()`.

```python
from itm3900d import ITM3900D

psu = ITM3900D(dry_run=True, strict=False)
psu.open()
print(psu.scpi_keys("voltage"))
psu.invoke("source_voltage_level_immediate_amplitude", 5.0)
print(psu.invoke("source_voltage_level_immediate_amplitude_query"))
```

## Hardware-in-loop status

This package has not been hardware-verified in this environment. Before real production deployment, run the scripts in `scripts/` over USB-TMC, Ethernet VXI-11, raw socket, DLOG/ELOG, ARB/list mode, protection, timeout, reconnect, and output safety paths.
