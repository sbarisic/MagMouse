# Copper trace cleanup — 2026-09-13

Simplified Main, Wheel and Encoder copper polylines on every routed layer.
The search handles shared endpoints, nanometre coordinate rounding, and
mutually nearest forward-facing ends with overlapping copper caps. It keeps
net/layer/width transitions, branch vertices, pad and via positions fixed.
Simplified centerlines stay within 0.05 mm of the original run, including the
small cap-overlap joins. Existing USB pair copper is unchanged.

Native DRC rejected some candidate shortcuts; their original chains were
restored. Main VBUS_USB, ACT_5V and CS_PAW were retained after the initial
strict checks exposed power-path screening and reference-coverage regressions.
No electrical acceptance limits were relaxed. This is a clearance-constrained
cleanup, not a claim that every remaining short segment can be removed.

| Board | Accepted runs | Original segments in those runs | Replacement segments |
|---|---:|---:|---:|
| Main | 1,572 | 8,627 | 1,572 |
| Wheel | 358 | 3,308 | 358 |
| Encoder | 5 | 19 | 5 |

The polyline edits remove **10,019 track segments**. One additional zero-length
track inside an unchanged +3V3 via was removed, for **10,020 fewer segments**.
Pads, vias, components, board outlines,
trace widths and net assignments remain unchanged. Native connectivity, physical
DRC and schematic parity pass on each board. The strict analog, USB/reference/ESD,
power, interlock and signal-return checks also pass.

The Main total includes one explicit local repair of the screenshot's CC_OUT1
run: 21 short segments between R26 and the diagonal exit were replaced with
one 0.15 mm trace from (56.325, 31.100) to (57.350, 34.500) mm. This manual
pad-to-exit shortcut is separate from the automatic 0.05 mm corridor rule and
passes the same native and electrical checks.

`straighten_tracks.py` implements the cleanup and rolls back candidates that
fail native DRC. `test_straighten_tracks.py` covers grid runs, overlapping and
separated caps, width transitions, branch points, corners and protected USB.
Re-run the full electrical checks separately after using the tool; its native
DRC result alone is not full electrical acceptance.

Updated images are in `copper-images/index.html`; the vector SVGs are preferable
for detailed inspection. The known unsupported panel tabs are not part of this
trace edit and remain unresolved. No replacement package has been sent to JLC.
The frozen 2026-09-12 submitted archive is preserved under `submissions/`.
