from itm3900d import ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=30, max_current_a=5, max_power_w=100)

with ITM3900D.open_usb(safety=policy, allow_output_enable=False) as psu:
    print(psu.idn())
    print(psu.get_scpi_version())
    print("V=", psu.measure_voltage())
    print("I=", psu.measure_current())
    psu.output_off()
