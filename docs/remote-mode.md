# Remote control
The programming guide specifies SYST:REM and SYST:LOC without a response.
```python
from itech_driver import connect_tcp
with connect_tcp("192.0.2.10", require_remote=True) as psu:
    print(psu.identify())
    with psu.remote_mode():
        # Explicit setting commands only under an approved bench procedure.
        pass
```
`requested_mode` is a local record of the most recent successful mode command,
not proof of the physical panel state. A front-panel action or another client
can change it. The opt-in write guard is not a safety interlock and does not
cover direct core-client calls or side-effecting queries. It is invalidated on
session generation changes, disconnect, reset/preset or public communication
failure. Opening/closing never implicitly changes remote or output state.
The context requests local on exit if the same session is live; local mode
does not disable output. Physical qualification requires panel observation.
