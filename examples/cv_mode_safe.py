from itm3900d import ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=5.5, max_current_a=0.5, max_power_w=3)
psu = ITM3900D.open_usb(safety=policy, allow_output_enable=True)
try:
    psu.configure_cv(5.0, 0.2, 2.0)
    if input("Type ENABLE to turn output ON: ") == "ENABLE":
        psu.output_on(confirm=True)
    print(psu.measure_scalar())
finally:
    psu.output_off(verify=True)
    psu.close()
