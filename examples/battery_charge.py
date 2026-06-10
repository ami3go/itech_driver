from itm3900d import ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=4.3, max_current_a=1.0, max_power_w=5.0)
psu = ITM3900D.open_usb(safety=policy, allow_output_enable=True)
try:
    psu.set_battery_charge_voltage(4.2)
    psu.set_battery_charge_current(0.5)
    if input("Type ENABLE to run battery charge mode: ") == "ENABLE":
        psu.run_battery_mode(confirm=True)
finally:
    psu.output_off(verify=True)
    psu.close()
