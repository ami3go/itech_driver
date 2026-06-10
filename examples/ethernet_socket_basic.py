from itm3900d import ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=30, max_current_a=5, max_power_w=100)

with ITM3900D.open_ethernet("192.168.0.50", lan_mode="socket", port=5025, safety=policy, allow_output_enable=False) as psu:
    print(psu.idn())
    psu.output_off()
