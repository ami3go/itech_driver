# ARB integer validation evidence

ITECH IT-M3900D User Manual V2.6/5,2025 section 4.6.1 pp.58–59
(https://www.altoo.dk/files/itech/manuals/IT-M3900D-User-Manual.pdf)
establishes the family LIST envelope of 200 steps, 10 stored LIST files
and up to 999999 repetitions. The implementation applies these conservative
family bounds to existing legacy LIST-oriented integer arguments and allows
finite positive repeats only; zero-repeat meaning is not inferred. This is
not a claim that every ARB waveform/firmware has the same command ranges.
Programming Guide V1.4/09,2024 index pp.243–246 and 267–268 confirms command
names and integer argument syntax, but the detailed command pages could not
be retrieved. Existing wire syntax is preserved; exact command-specific
range/firmware qualification remains open under #167 and #173. Termination
remains quarantined, no unverified commands added. Fractional, bool, negative,
overflow and string arguments fail before I/O.
