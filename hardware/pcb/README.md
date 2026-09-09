# Motherboard PCB

Initial placement, 2026-09-09, KiCad 10.0.6. Open the editable
[MagMouse.kicad_pcb](../kicad/MagMouse.kicad_pcb) from the
[KiCad project](../kicad/MagMouse.kicad_pro).
**This is a partially routed prototype draft, not a fabrication release.**

## Starting geometry

The board is a provisional **60 x 95 mm**, 1.6 mm thick, with 3 mm corner
chamfers. Its bounds are X = 95..155 mm and Y = 100..195 mm in KiCad;
the USB/front edge is Y = 100 mm. These are layout assumptions, not dimensions
from a measured enclosure. No mounting holes or optical aperture have been cut.

All **315 motherboard footprints** are inside the outline: 271 BOM components,
43 test pads and J5 motor wire pads. The [60 mm placement pass](PLACEMENT_60MM.md)
was followed by the [separate encoder project](../encoder/README.md): U27/C62
moved to that board and J6 was added here. No off-board staging parts remain.
All BOM components on the motherboard remain on the front; 40 test pads are on
the back and three on the front. Pads do not require backside component assembly.

The outline was widened symmetrically from 50 to 60 mm. The USB connector,
ESP32 module and optical centre remain fixed. U35 is at X=125.5, Y=157.5mm on
F.Cu, rotation 270 degrees. Some earlier circuit groups and optical supplies
were moved to make space for the wheel driver, ADC2, brake, IMU and RGB.
The [optical placement notes](OPTICAL_PLACEMENT.md) describe the current arrangement.
The shell will be designed around the PCB and its mechanical interfaces.
Test pads and J5 are excluded from the BOM and placement export. MPN, LCSC and datasheet fields are
retained. Future schematic changes can use KiCad's **Update PCB from Schematic
(F8)**; do not import another set of footprints manually.

| Area | Initial placement |
| --- | --- |
| Front | USB-C connector, data/CC protection, Type-C detection, input eFuse, buck and J6 encoder cable header |
| Front sides | Left/right coil connectors, bridge drivers and Hall sensors |
| Left middle | Middle button, actuator storage/clamp, current monitor, ADC1 and optical supplies |
| Right middle | Actuator eFuse, wheel driver and ADC2; brake resistors along the edge |
| Centre | Provisional wheel/encoder mechanics, optical group and IMU; RGB near USB |
| Rear | ESP32, interlock, ADC2 SPI buffer, brake comparator/reference, reset/boot and test access |

Drawings on **Dwgs.User** identify the reserved areas. The wheel rectangle
prohibits copper, vias, pads and footprints on all four copper layers. The optical
rule area now follows the proposed aperture at X=121.20..129.80,
Y=148.68..165.94mm and prohibits copper, vias and pads on all four layers.
Footprints may straddle that aperture, as U35 must; review physical body clearance
separately. A 20 x 22mm drawing reserves space below for the lens assembly.
These are planning envelopes, not verified clearances for the GB1806,
shaft, bearings, encoder, lens or sensor. The complete wheel assembly may need
more area or a separate board. Hall positions and coil connector locations must
move to match the measured paddle/magnet assembly; their present proximity does
not establish acceptable magnetic crosstalk.

The ESP32 antenna faces the rear. Its library keepout is retained on all copper
layers; preserve the clearance outside the board in the enclosure too. The
ESP32-S3-MINI-1 uses KiCad's shared **ESP32-S2-MINI-1** land pattern. See
[Espressif's module layout guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html)
and the [module datasheet, v1.7](https://documentation.espressif.com/esp32-s3-mini-1_mini-1u_datasheet_en.html).

## Draft routing setup

Four copper layers are enabled. The intended allocation is front components and
signals, In1 ground reference, In2 power/slow signals, and back signals/test pads.
The [buck routing pass](BUCK_LAYOUT.md) adds 37 track segments, 11 vias and local
front/In1 ground pours. The inner-layer dielectric thicknesses, copper weights
and controlled-impedance stackup are not selected. Board-wide routing is open.

The project starts with 0.15 mm net clearance, a 0.127 mm absolute minimum,
0.25 mm default tracks, 0.60/0.30 mm through vias and 0.30 mm copper-to-edge
clearance. The four supply nets have a 0.75 mm suggested track width. These are
editor starting values: size power paths, copper and thermal vias from measured
current and temperature limits. Neck-downs and pad escapes require local review.
The saved differential-pair values are placeholders, not a calculated 90-ohm USB
geometry. Select a JLCPCB stackup before routing USB and verify against its
[current rigid-board capabilities](https://jlcpcb.com/capabilities/pcb-capabilities/).

Reference designators are on the fabrication layers for placement review;
component outlines remain on silkscreen. Add a readable final silkscreen after
placement is settled. No parts require backside soldering in this draft.

## Review and next work

From the repository root:

    python hardware/kicad/export_pcb_review.py

This reads the live schematic/PCB and produces front/back SVGs, native DRC JSON
and a summary under `build/pcb-review`. The legacy-named
`placement-with-staging.svg` now has no off-board encoder parts. The
exporter accepts `--kicad-cli PATH`.
The default exit status checks placement and schematic parity; add
`--require-routed` to also fail on incomplete connectivity. Neither mode
establishes manufacturing or electrical acceptance.

Current check: **0 physical DRC violations and 0 schematic parity issues**,
without DRC exclusions. Native connectivity counts **775 unrouted connections**;
the DRC JSON returns 499 unconnected entries, so its list length is not a full
connection count. Only the buck subcircuit and its local return copper are routed.
See [buck layout and native copper checks](BUCK_LAYOUT.md) for the completed scope.
This checks local footprint geometry and synchronization, not board fit, operation, magnetic
separation, heat dissipation, signal integrity or enclosure fit.

1. Fit the implemented upright encoder board, its harness and the complete wheel
   assembly; allocate paddle magnets, mounting holes and connector access.
   Design the shell/base around the board and verified optical height.
2. Qualify [PMW3360 samples, SROM and optical fit](../kicad/OPTICAL_DESIGN.md).
   Optical, [IMU and RGB](../kicad/PERIPHERAL_REVIEW.md) circuits are drawn.
   The wheel/ADC2/encoder and provisional brake circuits are drawn; their
   [timing and energy measurements](../kicad/WHEEL_REVIEW.md) remain open.
3. Continue from the routed buck with U12 input-eFuse placement and routing.
   Tighten bridge current loops, decoupling and analog return paths; provide
   exposed-pad thermal vias and space for the brake resistor's heat.
4. Choose the production stackup, route USB and power, then sensing/control.
   Fill ground planes and review return paths, thermal paths and test access.
5. Complete ERC/DRC and package/stencil review before exporting revision-matched
   Gerbers, drills, assembly drawings, BOM and placement files for JLCPCB.

The custom button coils remain mechanical assemblies wired to J2/J3/J4; there
are no PCB spiral actuators. No manufacturing files are provided yet. See the
[roadmap](../../docs/roadmap.md) for schematic and bench-validation gates.
