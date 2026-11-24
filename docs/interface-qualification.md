# Communication interface qualification runbook

## Offline acceptance matrix

| Interface | Automated evidence | What still requires hardware |
|---|---|---|
| USBTMC | PyVISA-sim USB INSTR | Real USB driver, VID/PID, cable and firmware |
| VISA LAN | PyVISA-sim TCPIP INSTR | LXI/VXI-11 actual backend, reconnect |
| Native LAN TCP | Real loopback socket, fragmented LF response, no-VISA job | Actual socket framing, configured port, link interruption |
| USB VCP | Fake backend settings and real pyserial loopback | OS enumeration, actual serial framing and baud |
| Discovery | Injected candidates, identity filtering, dedup and diagnostics | Actual VISA enumeration and mDNS behavior |
| Remote/local | Scripted mode sequence, failures and session generation | Front panel observation, vendor error response |

Run `python -m pip install -e '.[dev]'` and `python -m pytest --junitxml=offline.xml`.
No bench endpoints are contacted in normal CI. PyVISA-sim is not a physical
VXI-11 or USBTMC protocol test.

## Physical qualification (operator only)

1. Confirm the bench is free and operator explicitly authorizes the connection.
   Identify actual model, serial and firmware from panel; use a safe,
   de-energized, independently verified output configuration, no DUT attached.
   Do not infer de-energization from software state. Follow vendor electrical safety procedures.
2. Select USB TMC or VCP in the panel menu, or configure the LAN IP and port.
   Record actual VISA backend or serial driver and settings. Use a dedicated
   environment and run only one interface at a time.
3. Run each test on the same known instrument; replace placeholders with actual
   endpoint and exact serial. Use `-m hardware --run-hil` explicitly.

```sh
python -m pip install -e '.[dev,discovery]'
python -m pytest -m hardware --run-hil --hil-interface usbtmc --hil-address 'USB0::<VID>::<PID>::<SERIAL>::INSTR' --hil-serial '<SERIAL>' --junitxml=hil-usbtmc.xml
python -m pytest -m hardware --run-hil --hil-interface visa-lan --hil-address 'TCPIP0::<IP>::inst0::INSTR' --hil-serial '<SERIAL>' --junitxml=hil-visa-lan.xml
python -m pytest -m hardware --run-hil --hil-interface tcp --hil-address '<IP>' --hil-tcp-port 30000 --hil-serial '<SERIAL>' --junitxml=hil-tcp.xml
python -m pytest -m hardware --run-hil --hil-interface vcp --hil-address '<COM-or-device>' --hil-baudrate 9600 --hil-serial '<SERIAL>' --junitxml=hil-vcp.xml
```

4. For each interface, repeat after a controlled disconnect/reconnect with
   operator present; collect errors and elapsed time, no automatic write replay.
   Verify the actual panel remains in its initial local/remote state after
   read-only testing. A separate run with `--hil-remote-local` is permitted only
   with operator consent and observation of the panel before, during and after
   the transition. It does not test or change output state.
5. Run discovery only with operator approval; confirm both available endpoints
   refer to the same serial. VCP enumeration is opt-in; do not probe unrelated devices.
6. Record evidence, including all failures and skipped tests. Do not mark an
   interface physically qualified based solely on an offline pass or successful IDN.

## Evidence template (one record per interface)

- Date/time, operator, git commit, OS/Python, package versions, VISA/serial backend.
- Instrument model, firmware, serial, exact endpoint, cable, baud/framing/port.
- Independent safe-output precondition, authorization, panel before/after.
- JUnit XML path, repeated IDN and response time, disconnect/reconnect outcome.
- Discovery result, remote/local panel observations if authorized.
- Verdict PASS/FAIL/NOT RUN; unresolved limitations and follow-up owner.

No protection/energized/ARB/battery procedure is authorized by this runbook.
