# Motherboard PCB

Routing draft, 2026-09-09, KiCad 10.0.6. Open the editable
[MagMouse.kicad_pcb](../kicad/MagMouse.kicad_pcb) from the
[KiCad project](../kicad/MagMouse.kicad_pro).
**This is a partially routed prototype draft, not a fabrication release.**

## Starting geometry

The board is a provisional **60 x 95 mm**, nominal 1.6 mm (1.578 mm CAD laminate), with 3 mm corner
chamfers. Its bounds are X = 95..155 mm and Y = 100..195 mm in KiCad;
the USB/front edge is Y = 100 mm. These are layout assumptions, not dimensions
from a measured enclosure. No mounting holes or optical aperture have been cut.

All **317 motherboard footprints** are inside the outline: 273 BOM components,
43 test pads and J5 motor wire pads. The [60 mm placement pass](PLACEMENT_60MM.md)
was followed by the [separate encoder project](../encoder/README.md): U27/C62
moved to that board and J6 was added here. The input-power pass added local
output bypass C88; the U13 pass added input bypass C89 and moved C40 beside
U13 OUT. No off-board staging parts remain.
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
The [buck routing pass](BUCK_LAYOUT.md) is now followed by the
[input-power and source-selection subset](INPUT_POWER_LAYOUT.md), including
USB-to-U12 and U12-to-buck power copper and a filled In1 ground plane. The
[Type-C pass](TYPEC_LAYOUT.md) connects detector inputs and source-logic supplies.
The [U13 pass](ACTUATOR_POWER_LAYOUT.md) adds its local feed, bypass and protection copper.
The [control pass](ACTUATOR_CONTROL_LAYOUT.md) connects enable fanout and power-fault/reset wiring.
The [distribution pass](ACTUATOR_DISTRIBUTION_LAYOUT.md) connects actuator feeds,
driver/brake current paths, sensing and remaining interlocks. U21 now requires
four filled and capped vias in its exposed pad. The [USB pass](USB_LAYOUT.md)
adds two more at U1/C32, compacts U12 ILM and routes the data pair with a
checked continuous In1 reference. Include all six component-land vias in the quote.
[JLC041611-2116](STACKUP.md) is selected with 1 oz outer/inner copper;
board-wide routing and thermal review remain open.

The project starts with 0.15 mm net clearance, a 0.127 mm absolute minimum,
0.25 mm default tracks, 0.60/0.30 mm through vias and 0.30 mm copper-to-edge
clearance. The four supply nets have a 0.75 mm suggested track width. These are
editor starting values: size power paths, copper and thermal vias from measured
current and temperature limits. Neck-downs and pad escapes require local review.
The USB netclass now uses the supplier-calculated 0.1466 mm width and
0.1501 mm gap for the 90-ohm target on the selected stackup. The saved USB
route/reference audits pass; manufacturer impedance acceptance and USB hardware
tests remain open. See [USB layout](USB_LAYOUT.md) and [stackup notes](STACKUP.md).

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
without new DRC exclusions. Native connectivity counts **204 unrouted connections**;
the current DRC report also lists 204 entries. The buck, input-power/source-selection,
U13, actuator distribution, driver/brake, interlock, ILM/telemetry and USB subsets are routed.
See [USB layout and native copper checks](USB_LAYOUT.md) for the latest scope.
This checks local footprint geometry and synchronization, not board fit, operation, magnetic
separation, heat dissipation, signal integrity or enclosure fit.

1. Fit the implemented upright encoder board, its harness and the complete wheel
   assembly; allocate paddle magnets, mounting holes and connector access.
   Design the shell/base around the board and verified optical height.
2. Qualify [PMW3360 samples, SROM and optical fit](../kicad/OPTICAL_DESIGN.md).
   Optical, [IMU and RGB](../kicad/PERIPHERAL_REVIEW.md) circuits are drawn.
   The wheel/ADC2/encoder and provisional brake circuits are drawn; their
   [timing and energy measurements](../kicad/WHEEL_REVIEW.md) remain open.
3. Review actuator current-path necks, decoupling and analog returns; qualify
   driver and brake heating, and confirm the filled/capped U1/C32/U21 vias.
4. Route SPI, optical and remaining sensing/control; obtain USB impedance acceptance.
   Shorten circuitous control routes, add ground stitching and review return
   paths, thermal paths and test access.
5. Complete ERC/DRC and package/stencil review before exporting revision-matched
   Gerbers, drills, assembly drawings, BOM and placement files for JLCPCB.

The custom button coils remain mechanical assemblies wired to J2/J3/J4; there
are no PCB spiral actuators. No manufacturing files are provided yet. See the
[roadmap](../../docs/roadmap.md) for schematic and bench-validation gates.
