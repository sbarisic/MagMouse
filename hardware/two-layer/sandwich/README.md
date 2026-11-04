# MagMouse stacked two-layer boards

All four boards are routed and have independent schematics. Native KiCad 10.0.6
checks report zero ERC findings, DRC findings, unconnected items and schematic
parity findings under the saved rules. The [quote package](quote-package/README.md)
contains the files for supplier pricing; physical and supplier acceptance remain open.

The standard-via revision uses 0.30 mm via drills and at least 0.45 mm copper
lands. All four boards are checked for via-hole/SMD-land overlaps. The derived
[223 × 114 mm panel](panel/Panel.kicad_pcb) combines one of each board using
2 mm routed gaps and 5 mm mouse-bite tabs. Source copper is copied exactly,
with isolated net names for each board; individual outlines remain unchanged.

![Routed Main boards](main-routing.png)

| Board/project | Dimensions | Copper layers | Original circuit footprints | Added interface/mount footprints |
| --- | --- | ---: | ---: | ---: |
| [Lower](lower/Lower.kicad_pro) | 70 × 100 mm, tapered | 2 | 122 | 6 |
| [Upper](upper/Upper.kicad_pro) | 70 × 100 mm, tapered | 2 | 86 | 6 |
| [Wheel](wheel/Wheel.kicad_pro) | 55 × 60 mm | 2 | 87 | 0 |
| [Encoder](../encoder/Encoder.kicad_pro) | 14 × 18 mm | 2 | 3 | 0 |

[All-board overview](all-boards.png). Component footprints, pads and drills are
full size. Both Main outlines retain the approved taper and 38.5 mm front edge.
The Wheel reduction from 80 × 75 to 55 × 60 mm removed 45% of its board area.

## Circuit and schematic split

Lower contains the ESP32, USB connector and data/CC circuitry, 3.3 V regulator,
optical sensor and local supplies, IMU, RGB, encoder interface and Wheel signal
connector J8. Upper contains the eFuses, power monitoring, three Hall sensors,
ADC1, hardware interlock and Wheel power connector J10.

The independent [Lower schematic](lower/Lower.kicad_sch) and
[Upper schematic](upper/Upper.kicad_sch) each include `20_Stack_Harness` with the
actual signal/power arrays and mounting holes. PCB symbol paths match these
projects. The combined [Main circuit](main-circuit/Main.kicad_sch) is retained as
the migration reference; edit the independent projects for subsequent work.
Every retained component value and pin/net connection was compared with that
reference. USB data/CC and analog Hall/current-sense/ADC connections stay local
to their respective boards.

Buttons use passive plastic click mechanisms and one sensing magnet per Hall
sensor. The active design removes 38 button-only parts, including U4/U5/U6,
J2/J3/J4 and U17. ADC1 channels 3–5 are grounded spares; GPIO4–9 are unused.
U18 retains the shared HALL_EN gate. Wheel drive, interlock, ACT_5V protection
and shared storage remain. [passive-buttons.json](passive-buttons.json) records
the exact removed parts and pin changes. The older routed checkpoints retain
the superseded button-coil circuitry.

## Wiring

The Main stack has **19 wires with three shared grounds**:

| Interface | Signals/supplies | Grounds | Total |
| --- | ---: | ---: | ---: |
| J101 ↔ J102 | 13 signals | 1 | 14 |
| J103 ↔ J104 | 3 supply rails | 2 | 5 |

Connect equal pad numbers using [WIRE_MAP.md](WIRE_MAP.md). Signal arrays are
2 × 7 at 2.54 mm pitch: x = 6/8.54 mm, y = 42–57.24 mm, 1.8 mm lands and
0.8 mm drills. Five power pads use 5.08 mm pitch at y = 11 mm, x = 25–45.32 mm,
2.4 mm lands and 1.2 mm drills. Raw VBUS goes up, PWR_5V returns to Lower and
+3V3 goes back up. ACT_5V stays on Upper and feeds Wheel.

The Wheel harness also has **19 wires with three shared grounds**. Lower J8
and Wheel J9 each use 17 pads in a 2 × 9 grid with one hole omitted; their copper
envelope is 22.12 × 4.34 mm. Upper J10 and Wheel J11 carry ACT_5V and the third
ground. See [WHEEL_WIRE_MAP.md](WHEEL_WIRE_MAP.md). Wire gauges, cut lengths and
stack height still depend on the mechanical assembly.

## Placement and routing

The approved component spacing and fixed USB, optical, Hall, antenna, connector
and mounting positions are retained. Two underside test pads moved to clear
the USB corridor: TP28 to (34,69.5), TP29 to (38,78) mm. Fitted electronic parts
remain on the front; several diagnostic test pads are on the back.

The long USB pair was placed before routing, around the right side of the
optical reserve, using the inherited 1.10 mm trunk width and 0.15 mm nominal
gap with narrow land escapes. Freerouting 2.5.0 completed the remaining routes.
KiCad then restored minimum track/via sizes, filled and stitched ground copper,
removed unused fanout vias, and checked actual connectivity and clearances.
Power escapes were widened where geometry permits. The fabricator's stack and
physical USB, power, thermal and analog performance still need verification.

Aligned M2 mounting candidates remain at (18,6), (52,6), (7,76), (63,76) mm:
2.2 mm holes and 5 mm support envelopes. The optical aperture reserve remains
on Lower. U3 stays at (35,89.25) mm, with its antenna approximately 0.43 mm from
the curved board edge at the corners. The requested 5 mm reserve is
x = 22.3–47.7, y = 94.5–104 mm on both boards, extending beyond the rear edge.
Upper retains substrate over that region; assembled radio performance is untested.

## Validation and quote files

[routing-review/summary.json](routing-review/summary.json) records current board
hashes, sizes, layer counts, ERC/DRC/parity results and fabrication dimensions.
The native reports, exported netlists, front/back copper SVGs and track-width
measurements are alongside it. Inherited ignored categories remain explicit in
the reports; no new DRC or ERC exclusions were added for routing.

[MagMouse-quote-package.zip](MagMouse-quote-package.zip) includes four separate
Gerber/drill ZIPs, per-board BOM/CPL CSVs, combined purchasing inventory, manual
items and via-in-pad intersection lists. Read its [quotation notes](quote-package/README.md)
for stack, assembly, stock, shipping/tax and mechanical assumptions. This is a
pricing package. The [first live quote](quotes/2026-11-04-jlcpcb/QUOTE.md) records
the superseded 0.20 mm, separate-board version. No fabrication order is placed.

`partition.json` preserves ownership and the checked 19-wire contract.
`placement-positions.json`, `spacing-review.json`, `spacing-baseline.json`,
`placement.svg/png` and `passive-validation.json` are historical pre-routing
evidence; their old board hashes and airwire counts are not current route results.

## Reproduction

Use KiCad 10 Python. `split_main.py` is a guarded one-time extraction;
`build_study.py` now refuses to overwrite the independent projects. Edit the
independent KiCad projects for future circuit or layout changes.

`route_main.py` exports/imports Specctra sessions, `route_usb.py` defines the
initial USB corridor, `finish_main.py` fills and stitches ground, and
`widen_power.py` widens power where clearance and keepouts allow. Freerouting
2.5.0 used neck retry at 150 µm with the optimizer disabled for Lower. Lower's
DSN clearance was increased to 165 µm to leave margin for native minimum-width
restoration; saved KiCad clearances remain unchanged. Temporary sessions, router
binaries and logs stay in ignored `build/sandwich/main-routing`.

`export_quote.py` rechecks all four boards before exporting the package and
compares Main pins against the retained migration reference. `overview.py`
renders placement views; add `--main-only --copper` for the routed Main image.
`wheel_interface.py verify` refreshes the Wheel harness check. Its `prepare`
action is a destructive rebuild of that variant and is not routine validation.

`standard_vias.py` records the one-time drill migration and assists local via
relocation; `repair_wheel.py` and `continuous_routes.py` provide local path repairs.
`standard-via-review.json` records unchanged component placement and pad/net identity,
unchanged motor-phase/brake copper, and the final drill and via-in-pad counts. The finished
KiCad boards are the editable source. `panelize.py` derives and verifies the
combined manufacturing panel and exports its Gerbers/drills. Its verification
compares every source pad, track, via drill and filled-zone vertex after translation,
checks connected substrate and router access, and runs native panel DRC.

The fabrication rules explicitly use JLCPCB's 0.075 mm via annular ring and
0.20 mm via-hole-to-copper clearance, replacing 0.125/0.25 mm in the earlier
revision. Via hole-to-hole clearance stays 0.25 mm, copper clearance stays
0.15 mm by net class (0.127 mm board minimum), and minimum track width stays
0.127 mm. No additional DRC categories are ignored. These limits are based on
[JLCPCB's published capabilities](https://jlcpcb.com/capabilities/pcb-capabilities/).

Hardware: CERN-OHL-S-2.0. Scripts: GPL-3.0-or-later. Documentation: CC-BY-SA-4.0.
