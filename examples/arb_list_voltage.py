from itm3900d import ArbStep, ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=5, max_current_a=1, max_power_w=5)
psu = ITM3900D.open_usb(safety=policy, allow_output_enable=True)
try:
    psu.configure_cv(0, 0.5, 3)
    psu.configure_list_voltage([ArbStep(1.0, 0.5), ArbStep(2.0, 0.5), ArbStep(0.0, 0.5)])
    if input("Type ENABLE to start ARB: ") == "ENABLE":
        psu.output_on(confirm=True)
        psu.start_arb(confirm=True)
finally:
    psu.output_off(verify=True)
    psu.close()
