# ARB timing, acquisition accuracy and communication soak (#76)

Status: NOT RUN. No HIL permission is implied. Use the #75 qualification gate before performing any physical work. The commands below only analyze existing CSV files; they never contact hardware.

## Test matrix and acceptance preparation

For each claimed model/firmware/interface combination, record actual instrument ID, driver/core commits, guide revision, ambient conditions, reference calibration, connection and load. Freeze acceptance limits from the exact manufacturer's specification and test procedure before collecting data. Include measurement uncertainty, timebase uncertainty and loading. Do not reuse limits from another model.

| Test | Procedure under separately authorized HIL | Evidence |
|---|---|---|
| ARB timing | For each qualified waveform and finite repeat, capture waveform/trigger with calibrated scope; repeat at approved representative settings; compare measured period, dwell, transition and latency to expected values | Raw scope files, extracted expected/reference pairs, tolerance provenance, waveform plots |
| Acquisition | Use stable reference levels and synchronized reference waveform; compare sample count/order/timebase and DC values against calibrated DMM/scope | Raw buffers, reference files, time alignment, dropped/duplicate counts, expected and observed pairs |
| 24-hour soak | Each interface separately; non-energized read-only queries at specified cadence for at least 86400 s; log every attempt including failures, latency, generation changes and identity | UTC start/end, monotonic elapsed times, every attempt with sequence number and status, raw logs |
| Fault/reconnect | Separately approved disconnect and manual reconnect; no replay; verify identity and session generation before resuming | Raw log, fault/reconnect count, unknown outcomes; separate from uninterrupted soak |

Stop on unknown state, unexpected output, protection trip or lost communications. Operator independently secures bench. No automatic output enable/reset or reconnect during energized work. Do not omit failed attempts or splice different runs.

## Offline analysis

Use CSV with header expected,observed,abs_tolerance,uncertainty for timing or accuracy (one consistent unit per file). Set tolerance and uncertainty from approved sources before testing. Conservative acceptance: absolute error + measurement uncertainty <= tolerance. Report maximum error and every failed row.

Use CSV with header sequence,elapsed_s,latency_s,status,generation for soak, starting sequence 0; status OK/ERROR/TIMEOUT; generation is an integer. Log the first and last attempt. Choose max-gap and max-latency using approved cadence and interface requirements. A pass requires uninterrupted generation, contiguous sequence, no errors, full elapsed span >=24 hours and all gaps/latencies within limits. Attach actual UTC timestamps and raw transcripts separately, as elapsed values alone cannot establish real duration.

    python -m itech_driver.performance_evidence accuracy accuracy.csv
    python -m itech_driver.performance_evidence soak soak.csv --max-gap 5 --max-latency 2

Example numeric arguments are illustrative, not specified ITECH limits. Output JSON is a structural/numeric report, not certification of physical evidence. Run #75 checker and independent review for release. All actual HIL, timing, accuracy, and soak results remain NOT RUN.
