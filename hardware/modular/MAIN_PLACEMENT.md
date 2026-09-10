# Shaped main PCB placement

2026-09-11. Open [main/Main.kicad_pro](main/Main.kicad_pro) and
[main/Main.kicad_pcb](main/Main.kicad_pcb). The board is created from the split
main schematic with **246 footprints and 781 checked connected-pin assignments**.
All assembly components are on F.Cu; 37 test pads are on B.Cu. The outline is
**125 mm long, 80 mm maximum width and 44 mm across the front**. The common
four-layer JLC041611-2116 stack remains in place.

Native physical DRC and schematic parity report zero issues. This is a placed,
unrouted main PCB: 632 native unconnected items. The CLI DRC listing is capped at
499 entries, so use native connectivity for the full count. Original motherboard
copper has not been imported, and the original motherboard remains unchanged.

## Placement decisions

- USB-C sits at the front, at (40, 4) mm. Its shell can overhang the front by
  up to 0.5 mm; native DRC still checks all copper-to-edge clearances.
- Useful local power, driver, optical, IMU and MCU component groups retain their
  internal placement from the earlier motherboard. The body and courtyard checks
  use the curved outline, not only its bounding rectangle.
- ADC1/U10 and its bypass/telemetry filter parts move near the button circuitry.
  U10 is at (50.5, 46) mm. The longest provisional Hall-to-ADC centre span is
  below 34 mm; this is a placement measurement, not a routed length or noise test.
  Hall sensors and button connectors remain provisional for paddle/magnet CAD.
- PMW3360 stays facing the front, at (40.5, 72.5) mm. Its local bypass and support
  parts retain their relative geometry. The aperture reservation is a copper,
  pad and via keepout, not a fabricated hole. The 20 x 22 mm underside lens
  envelope remains a drawing that must be checked against the sampled lens,
  baseplate and feet.
- J8 faces downward at (63, 70) mm. A front-side placement reservation keeps its
  cable exit clear. The facing-header contract remains J8.N to J9.(31-N).
- J10 power is at (72, 91) mm, in the free right-side area with room to mate its
  housing. J6 remains at (28, 18.5) mm for the direct upright-encoder connection.
  Header positions do not establish cable length, bend radius or enclosure fit.
- The ESP32 module body fits within the PCB. Its larger RF courtyard includes
  antenna free space that extends beyond the rounded rear edge. The footprint's
  copper keepout remains present; enclosure material and nearby hardware still
  require RF/mechanical review.

## Mechanical interfaces and panel hold

The wheel is electrically routed, but its mounts and motor/encoder relationship
are not frozen. The main is electrically placed, but Hall/button placement,
mounting holes, wheel/shaft/bearing support, encoder support, cable bends,
USB opening and optical lens/baseplate stack still need mechanical CAD.

**Panelization is on hold until both boards have stable placement and mechanical
interfaces.** The earlier nesting study is unchanged. No panel copper, slots,
tabs, tooling holes or manufacturing exports were added in this pass.

Next, resolve those interfaces alongside the main routing plan. Preserve the
wheel's zero-unrouted result and analog/return checks as the mechanics evolve.
Then route the main power and sensing paths, USB, SPI and remaining controls.
Panel work follows interface stability, not merely zero DRC.

## Verification and source files

[main-placement.json](main-placement.json) records the initial positions and
back test pads. [start_main_board.py](start_main_board.py) creates a board from
that configuration and the exported split netlist. It refuses to overwrite an
existing board; subsequent edits belong in the PCB.

[verify_main_placement.py](verify_main_placement.py) checks inventory, values,
pad nets, body/courtyard containment, front width, USB/optical/FFC datums, ADC1
placement and required mechanical reservations. Native DRC/parity are required
separately. [main-placement-review.json](main-placement-review.json) records
the current PCB and netlist fingerprints. Four regression tests exercise the
saved board and wrong component position, FFC orientation and optical datum.

Use KiCad Python and CLI from the repository root:

```powershell
kicad-cli pcb drc --format json --schematic-parity --output build/modular/main-drc.json hardware/modular/main/Main.kicad_pcb
python hardware/modular/verify_main_placement.py --board hardware/modular/main/Main.kicad_pcb --netlist build/modular/main-review/netlist.xml --drc build/modular/main-drc.json --output hardware/modular/main-placement-review.json
python -m unittest discover -s hardware/modular -p test_main_placement_checks.py
```
