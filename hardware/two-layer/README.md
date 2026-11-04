# MagMouse two-layer bench variant

Separate experimental Main, Wheel and Encoder projects derived from the maintained
four-layer boards. The original boards, schematics, panel, CAM submission and
manufacturing package are not modified. This directory is not an ordering package.

| Project | Outline | Status |
| --- | --- | --- |
| [Main](main/Main.kicad_pro) | 180 x 295 mm, USB access notch | Routed; native CAD checks pass |
| [Wheel](wheel/Wheel.kicad_pro) | 80 x 75 mm | Routed; native CAD checks pass |
| [Encoder](encoder/Encoder.kicad_pro) | 14 x 18 mm | Routed; native CAD checks pass |

All original components, values, pad-to-net assignments and schematic sheets are
retained, including the IMU. No feature has been deliberately removed. The copies
use the existing shared symbol/footprint libraries with corrected relative paths.
Keep this directory inside the repository when opening a project.

The [stacked Main placement study](sandwich/README.md) explores replacing Main
with two smaller two-layer boards connected by soldered wires. It includes a
19-wire map with three shared grounds and two editable boards with matching
70 × 100 mm tapered outlines (38.5 mm front edge).
The active study uses passive plastic clicks with Hall sensing; 38 button-coil
parts and six control wires have been removed. The routed checkpoints above
retain the earlier coil circuitry.
Those separate study boards are unrouted and do not replace this routed checkpoint.
The study also includes a matching Wheel variant with a 19-wire harness, three
shared grounds, and shorter 17-pad signal arrays on Lower and Wheel. See its
[wheel wire map](sandwich/WHEEL_WIRE_MAP.md); the routed checkpoints in the table
above retain the earlier 32-wire interface.
That matching Wheel variant is now 55 × 60 mm and retains two copper layers.

## Checkpoint — 2026-11-03

Main's four track overruns have been trimmed at their connected junctions. A
redundant WHEEL_PWM_A branch that formed a copper sliver has been removed, and
the retained left-hand branch now ends at the MCU pad center. Main, Wheel and
Encoder all have zero reported DRC findings, zero unrouted connections and zero
schematic-parity issues under the saved rule settings. Five inherited ignored
check categories remain explicitly listed in the reports.

The [layout review](review/LAYOUT_REVIEW.md) records the cleanup, visual screening
and routing measurements. Next address Main's long SPI/PWM routes and power-path
review, then the electrical checks below. Final board resizing and manufacturing
release remain future work. These boards have not been electrically validated.
The original four-layer projects are unchanged.

The larger outlines are deliberately provisional. They are not compatible with
the existing three-board panel or the original edge-support fixture. Wire lengths
also need to be reassessed for this placement. Resizing,
mechanical supports and a new panel are separate future work.

## Electrical and manufacturing status

- Copper layers: F.Cu and B.Cu only. Nominal stack: 1.6 mm FR4, 35 um copper
  on both sides. Dielectric data are provisional, not a fabricator impedance model.
- Ground is distributed using outer-layer pours and through-via stitching.
  There is no internal uninterrupted reference plane.
- Short Wheel phase/current-sense routes remain on the top layer. Original
  exposed-pad thermal vias remain; new stitching connects the outer ground islands.
- Small signal vias remain 0.45/0.20 mm. Existing via-in-pad construction still
  needs a solder-wicking/fill/cap review. Two layers do not remove that issue.
- Main's USB pair has a top-layer main run with 1.10 mm traces and a 0.15 mm
  edge gap, with bottom ground reserved beneath that run. Connector, ESD and
  resistor escapes remain narrower. The USB and USB_Breakout routing presets
  distinguish those geometries. This is a provisional two-layer geometry;
  the original four-layer 90-ohm assumption **does not transfer** to this stack.
  Confirm impedance against the chosen fabricator's stack and validate USB.
- Some analog traces lack ground directly opposite them. The raw geometry is
  recorded in [reference-copper.json](review/reference-copper.json); local ground
  continuity is a separate native connectivity check. Noise, settling and EMC
  performance require measurements with all actuators operating.
- Input droop, button-driver temperatures, wheel current-sense accuracy, brake
  transients, SPI timing and USB operation need powered validation. Main's longer
  signal paths also need clock-rate and signal-integrity checks. A native DRC
  pass does not establish those behaviors or production suitability.

Main's controller module and its local supporting parts were moved and rotated
so the antenna faces the upper board edge. Its copper keepout is retained.
Keep the antenna clearance when reducing the outline or designing a fixture.

## Evidence

[baseline.json](baseline.json) records source PCB hashes and the component/pad-net
inventory. [review/summary.json](review/summary.json) records the current variant
hashes, source preservation, circuit identity, layer counts and native DRC results.
Reports must be regenerated after editing a board. Treat any nonzero unrouted count
as unfinished work, regardless of this summary text.

[review/routing.json](review/routing.json) records per-net copper lengths, widths,
layers and via counts, with hashes of the measured boards. Length includes all
branches; it is not an endpoint delay or an impedance measurement.

## Tools and reproduction

Use KiCad 10.0.6's bundled Python and CLI. `prepare.py` copies schematic/project
files and removes internal copper from the variant. **It overwrites the variant**;
use it only to intentionally restart a routing revision. `expand.py` adds the
provisional outlines. `spread_main.py` replaces Main with the spacious grouped
placement and records every component translation in `main-placement.json`.
`prune_routing.py` removes orphaned/conflicting translated copper before routing;
it is not a way to make a routed board pass DRC. These are construction steps,
not routine validation commands.

`route.py BOARD export` creates a Specctra DSN in ignored `build/two-layer/BOARD`.
Wheel routing used Freerouting 2.5.0; Main used Freerouting 1.9.0 and direct,
geometry-constrained connections, with analytics disabled. Import the corresponding
session with `route.py BOARD import`; then run `finish_copper.py BOARD`, native DRC,
and the reviewed `cleanup.py` repairs as needed. All imports must retain the
component/pad-net signature. Preserve session inputs/results locally when iterating.

`trim_main_stubs.py` applies the reviewed 2026-11-03 track cleanup using UUID and
geometry guards. It is idempotent on the repaired checkpoint. It does not replace
native DRC or perform general automatic track deletion.

The saved KiCad boards are the editable design sources. These construction helpers
are not a one-command reproduction of the final routing and cleanup. The Main
routing process removed inherited ground traces and unnecessary ground vias to
open pin escapes, retained thermal-pad vias, and rebuilt ground stitching after
signal routing. Its six coil nets use the Power routing preset in the variant.

`finish_copper.py` and `review_geometry.py` use Shapely 2.1.2 from
`build/two-layer/python`. Downloads, Java runtimes, routing sessions and verbose
logs remain under ignored `build/`; they are not project deliverables.

Routine validation with KiCad Python:

```powershell
& '<KiCad>/bin/python.exe' hardware/two-layer/verify.py --strict-warnings
& '<KiCad>/bin/python.exe' hardware/two-layer/review_geometry.py
& '<KiCad>/bin/python.exe' hardware/two-layer/review_routing.py
& '<KiCad>/bin/python.exe' hardware/two-layer/export_views.py
```

`verify.py` fails if a board is unrouted, has physical errors, differs from its
schematic, changes component/pad-net identity, has more than two copper layers,
or the original PCB hashes differ from the recorded source baseline.
`--strict-warnings` also fails on reported warnings; it does not enable ignored
checks. Schematic identity normalizes CRLF to LF before comparison, retaining
all other bytes so Windows checkout line endings cannot cause false failures.

Hardware files: CERN-OHL-S-2.0, as in [../LICENSE](../LICENSE).
Automation scripts: GPL-3.0-or-later, identified in their source headers.
