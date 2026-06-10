from itm3900d import ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=12, max_current_a=1, max_power_w=10)
psu = ITM3900D.open_usb(safety=policy, allow_output_enable=True)
try:
    psu.configure_cc(current=0.1, voltage_limit=10, power_limit=5)
    if input("Type ENABLE to turn output ON: ") == "ENABLE":
        psu.output_on(confirm=True)
finally:
    psu.output_off(verify=True)
    psu.close()
