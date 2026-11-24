# Protection threshold qualification

IT-M3900D Programming Guide V1.4/09,2024 (https://www.altoo.dk/files/itech/manuals/IT-M3900D-Programming-Guide.pdf)
pp.46–47 (OCP), 51–52 (UCP), 65–66 (OVP), 70–71 (UVP), 80 (OPP)
documents threshold setters but no bound arguments for threshold queries.
The rated electrical operating envelope is not the trip threshold range.
Do not issue invented MIN/MAX queries or assume rated/default equals max.

All five threshold setters (including legacy power_limit_set) now require
keyword qualification=ProtectionThresholdQualification(...), containing exact
model, firmware, protection kind, command-specific Range and external evidence
reference. Missing/mismatched evidence rejects, and supplied application
ceiling still applies. Existing readbacks and timing controls are unchanged.
Test ranges are synthetic, not manufacturer limits. The driver validates
binding and declared bounds, not authenticity of external evidence.
No built-in firmware-specific limits are claimed. #152 remains open until
the actual model/firmware protection ranges are independently established.
