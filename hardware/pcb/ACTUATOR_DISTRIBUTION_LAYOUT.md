# Actuator distribution and interlock routing

2026-09-10, KiCad 10.0.6. This pass connects the actuator supply, driver outputs,
current sensing, autonomous brake and remaining interlocks on the saved
60 x 95 mm motherboard. It follows the [local U13](ACTUATOR_POWER_LAYOUT.md)
and [enable/fault/reset](ACTUATOR_CONTROL_LAYOUT.md) passes. The schematic,
317 motherboard footprints, 273 BOM parts and separate encoder board are unchanged.

The subsequent [high-current review](HIGH_CURRENT_REVIEW.md) widens local driver
paths, adds front/back ground spreading, screens feed/output resistance and
corrects the rail capacitor inventory. The routing dimensions below describe
the original distribution pass.

## Copper and placement

- ACT_5V reaches all 39 pads, including storage, button-driver bypass capacitors,
  DRV8316 supply/bulk capacitors, the clamp and four brake resistors. Main feed,
  wheel-phase and brake trunks use 0.75 mm copper, with narrower local pad escapes.
- All six button coil outputs reach J2/J3/J4. Driver VM, bypass and exposed-pad
  returns are connected. Coil trunks generally use 0.5 mm copper; the short left
  negative output and pin escapes use 0.25 mm. Each button driver has four local
  0.60/0.30 mm ground vias.
- Paired DRV8316 phase pins have short front fanouts and two parallel through vias
  per phase before their wider routes to J5. C41, C46/C47, C49/C50 and associated
  support parts moved to clear the supply, charge-pump and signal escapes.
  Charge-pump and unused-buck support connections remain on F.Cu.
- Four additional 0.60/0.30 mm vias connect U21's exposed pad directly to ground.
  **These in-pad vias require a filled and copper-capped fabrication process.**
  Include this requirement in the JLCPCB quote and review the QFN stencil and
  assembly process before release. The four via centers, in millimetres, are
  (142.30, 152.90), (144.00, 152.00), (142.55, 153.75), (143.70, 154.30).
  Seven connected ground vias lie within 5 mm of the exposed-pad center overall.
- Q5, R121-R124, the comparator/reference ladder, gate resistor and local bypass
  are connected. R119 is beside the comparator output. The brake ladder and
  sense connections stay on F.Cu; the reference and gate routes use other layers
  where required. Resistor cooling and the long gate/reference paths still need
  thermal and transient review.
- All button command/input pairs, Hall enable, actuator request/permit/heartbeat,
  wheel request/run/disable, PWM inputs, current outputs/filters, source capability,
  VBUS detection, undervoltage/overvoltage, fault and reset nets are connected.
  Gate supplies and local timing/bypass returns are included. All nine ESP32
  exposed-ground lands are checked individually.

In1 remains the filled ground-reference layer. Routing uses F.Cu, In2.Cu and
B.Cu. The single schematic GND net is retained; this is not a separately isolated
analog/power star-ground implementation. The optical, wheel and antenna copper
reservations are retained. Some command/PWM/fault routes take long detours with
multiple layer changes around the dense driver area. Their shortening, return
stitching and coupling review remain part of the complete-board routing review.

The placement follows the local bypass, wide-current-path and thermal-ground
principles in the [DRV8231A](https://www.ti.com/lit/ds/symlink/drv8231a.pdf) and
[DRV8316](https://www.ti.com/lit/ds/symlink/drv8316.pdf) datasheets. The local
comparator bypass and series output resistor follow the
[TLV1811 guidance](https://www.ti.com/lit/ds/symlink/tlv1811.pdf).
Connectivity checks do not demonstrate compliance with every layout recommendation.

## Verification

The new `hardware/kicad/verify_distribution_layout.py` checks native saved-copper
connectivity across **84 named nets**, **33 supply pads** and **174 ground pads**.
It also checks selected front-only local loops, driver ground-via counts and the
four direct U21 exposed-pad vias. It records the PCB SHA-256 and native unrouted
count in `build/pcb-review/distribution-layout-checks.json`.

This pass ended with **247 native unrouted connections**, down from 651.
The subsequent [USB/ILM pass](USB_LAYOUT.md) retains these copper checks and
reduces the board to 204 unrouted connections. The remaining connections belong to the unfinished board;
the actuator distribution/interlock checks require their own scope to be complete.
Use the generated native DRC and checker reports as the validation record.

Final checks pass: **0 physical DRC violations**, **0 schematic-parity issues**,
all four native copper checkers, and **24 regression test methods** across the
distribution (3), actuator (10), input (8) and buck (3) suites. The distribution
suite includes 14 open-circuit subcases. No DRC rule or exclusion was added.
Power checks pass 195 critical pins and 4,096 interlock truth-table cases; wheel
checks pass 266 critical pins, 32 shutdown cases and 128 brake corners. The
encoder split/harness checker passes. Front/back exports were visually inspected.
The buck open-sense test now removes copper at U2.6 explicitly, because the wider
3.3 V distribution makes its former first-thin-track selection ambiguous.

Run with the installed KiCad Python from the repository root:

```powershell
$kp = "$env:LOCALAPPDATA/Programs/KiCad/10.0/bin/python.exe"
& $kp hardware/kicad/verify_distribution_layout.py
& $kp hardware/kicad/verify_actuator_layout.py
& $kp hardware/kicad/verify_input_layout.py
& $kp hardware/kicad/verify_buck_layout.py
& $kp hardware/kicad/test_distribution_layout_checks.py
& $kp hardware/kicad/test_actuator_layout_checks.py
& $kp hardware/kicad/test_input_layout_checks.py
& $kp hardware/kicad/test_buck_layout_checks.py
python hardware/kicad/export_pcb_review.py
```

The distribution regression suite exercises the saved board, removal of the
ground-reference zone and 14 deliberately disconnected power, driver, sense and
interlock nets. Existing power, wheel and encoder schematic checks remain applicable.

## Remaining acceptance work

USB routing is now covered by [the USB review](USB_LAYOUT.md). Finish SPI, optical and remaining board signals, then review return paths,
ground stitching, current-path necks, voltage drop, test access and silkscreen.
Confirm filled/capped vias and QFN solder-paste geometry with the fabricator.
The local widths and via counts are routing choices, not measured ampacity or
thermal acceptance. Verify simultaneous coil/motor loading against the roughly
2.02 A nominal combined actuator limit and measure driver/resistor temperatures.

The provisional wheel test envelope remains: returned peak current at most
0.4 A, average returned power at most 0.5 W, effective ACT capacitance at least
47 uF, brake response at most 10 us and measured rail peak below 6.5 V.
Four parallel 47-ohm resistors give 11.75 ohms; at 6 V they dissipate about
3.06 W total. These are bench gates, not demonstrated performance. See
[wheel review](../kicad/WHEEL_REVIEW.md) and [power review](../kicad/POWER_REVIEW.md).

Enclosure fit, optical height, magnetic separation, cable clearance and mounting
holes remain open. No fabrication or assembly package is released by this pass.
