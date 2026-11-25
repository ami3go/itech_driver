# IT-M3900D source command range evidence — #152 / #168 / #173

Source: ITECH IT-M3900D Programming Guide V1.4/09,2024, part 402225,
[manufacturer-authored guide mirror](https://www.4test.no/files/itech/manuals/IT-M3900D-Programming-Guide.pdf).
Printed page references below; guide index pp. IX–X. User manual V2.6/5,2025
[mirror](https://device.report/m/c717b848efd10e49e595bdfa897e495264467d4dd84c7123a668fb015ce93ff4),
§4.1–4.5 supports the distinction between programmed values and trip levels.

This is family-level syntax evidence, not a model/firmware support matrix.
Numerical instrument endpoints are not established by this guide index.
Do not substitute a nominal rating, a default value, or a synthetic test range
for a protection trip range. For programmed electrical quantities, intersect
live bounds with the installed model's rating and application bounds.
For protection levels, retain explicit command/model/firmware range evidence,
plus the existing independent application safety ceiling policy.

| Runtime header (write; append ? for query) | Unit | Guide write/read pp. | MIN/MAX/DEF query | Endpoint evidence |
|---|---|---|---|---|
| SOUR:VOLT | V | 57/58 | yes | live bounds; model ceiling |
| SOUR:CURR | A | 38/39 | yes | live bounds; model ceiling |
| SOUR:VOLT:LIM | V | 75/76 | yes | live bounds; model ceiling |
| SOUR:CURR:LIM | A | 56/56 | yes | live bounds; model ceiling |
| SOUR:POW:LIM | W | 76/77 | yes | live bounds; model ceiling |
| SOUR:VOLT:OVER:PROT:LEV | V | 65/66 | no | external range required |
| SOUR:CURR:OVER:PROT:LEV | A | 46/47 | no | external range required |
| SOUR:POW:OVER:PROT:LEV | W | 80/80 | no | external range required |
| SOUR:VOLT:UND:PROT:LEV | V | 70/71 | no | external range required |
| SOUR:CURR:UND:PROT:LEV | A | 51/52 | no | external range required |
| SOUR:VOLT:OVER:PROT:DEL | s | 67/68 | yes | live bounds |
| SOUR:CURR:OVER:PROT:DEL | s | 48/48 | yes | live bounds |
| SOUR:POW:OVER:PROT:DEL | s | 81/82 | yes | live bounds |
| SOUR:VOLT:UND:PROT:DEL | s | 71/72 | yes | live bounds |
| SOUR:CURR:UND:PROT:DEL | s | 52/53 | yes | live bounds |
| SOUR:VOLT:UND:PROT:WARM | s | 73/74 | yes | live bounds |
| SOUR:CURR:UND:PROT:WARM | s | 54/55 | yes | live bounds |
| SOUR:VOLT:SLEW:BOTH | s | 59/60 | yes | live bounds |
| SOUR:VOLT:SLEW:POS | s | 60/61 | yes | live bounds |
| SOUR:VOLT:SLEW:NEG | s | 62/63 | yes | live bounds |
| SOUR:CURR:SLEW:BOTH | s | 40/41 | yes | live bounds |
| SOUR:CURR:SLEW:POS | s | 41/42 | yes | live bounds |
| SOUR:CURR:SLEW:NEG | s | 43/44 | yes | live bounds |
| SOUR:RES | ohm | 83/84 | yes | live bounds, CV only |

Each setter takes a finite numerical parameter (NRf+); queries return a numeric
value. The power-limit alias shares the programmed power command. MIN/MAX/DEF
on setters are deliberately not exposed as an alternative to numeric validation.
The guide describes SLEW parameters as times, not rates. The registry records
indexed guide page, unit and permitted query selectors; the internal executor
rejects unlisted bound queries before SCPI. The runtime guard rechecks after
identity refresh and before the final write. Strict capability qualification
still requires an external attestation covering selectors for the exact
model, firmware and interface; legacy mode remains explicitly permissive.

Regression ranges are synthetic and do not certify the hardware. No physical
I/O was performed. Local Git checkout unavailable in this execution
environment; GitHub CI is the verification gate. Do not close the parent
issues until remaining model/firmware evidence and full acceptance criteria
are met.
