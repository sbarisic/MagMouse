# USB data routing and compact input-current limit

2026-09-10, KiCad 10.0.6. This review covers saved copper in
[MagMouse.kicad_pcb](../kicad/MagMouse.kicad_pcb). The motherboard still has
204 unrouted connections and is not ready for fabrication.

## USB route

J1's reversible D+ contacts reach U1.1 and R6.2; D− reaches U1.2 and R5.2.
The 33-ohm resistors then reach ESP32-S3 pads 24 and 23 respectively.
All four data nets stay on F.Cu, with **no signal vias**. The paired run goes
around the wheel and optical reservations. Board outline, optical/encoder
mechanical datums and the ESP32 antenna reservation are unchanged.

The [selected JLC041611-2116 stackup](STACKUP.md) uses 1 oz outer/inner copper
and a 0.109 mm L1–L2 dielectric. USB traces use **0.1466 mm width and
0.1501 mm edge gap**, from the saved non-coplanar 90-ohm calculator result.
The net names remain USB_DP/DM and MCU_USB_DP/DM; the copper audit explicitly
maps their pads and does not depend on KiCad recognizing a suffix convention.
The project permits the selected width; the custom rules retain a 0.15 mm
minimum on non-USB traces and require the selected USB width.

| Measurement | D+ | D− |
| --- | ---: | ---: |
| Long coupled run, mm | 77.532007 | 77.536467 |
| J1 A-contact through termination to MCU, mm | 87.397391 | 85.434378 |
| J1 B-contact through termination to MCU, mm | 84.307391 | 84.434378 |
| Resistor MCU-side pad to MCU pad, straight-line mm | 1.8916 | 2.1490 |

The coupled run differs by 0.004461 mm. Complete contact-path skew is
**1.963013 mm for A and 0.126987 mm for B**. These figures include the
connector ties and pad fanouts but exclude the resistor body; they are not
propagation-delay measurements. A 2.5 mm full-path skew limit is a local
regression budget, not a USB specification limit. About 89.9% of the
connector-side trace length has the selected pair spacing, within the
checker's 0.01 mm geometric comparison tolerance. Connector, ESD, resistor
and MCU lands require local fanout exceptions.

## Reference plane and ESD return

The saved In1 GND fill covers both data traces, plus **0.327 mm beyond each
trace edge** (three times the reference dielectric thickness). The audit
subtracts the actual filled ground polygons from each complete swept trace
area. It checks holes and narrow notches, rather than only sampling track
centers or checking the GND net name. Uncovered area is zero. Nearby
non-ground vias were moved or rerouted to keep their plane clearances out
of this margin. No signal was routed on In1.

U1 is beside J1. Its ground land has one direct 0.60/0.30 mm through via into
In1 GND. Both USB connector ground groups and the shield reach that plane.
The audit also verifies that the shortest data paths pass through the ESD
lands without a branch longer than the 0.2 mm local check budget.

**Fabrication must include filled, copper-capped vias at U1.3 and C32.1,
in addition to U21's four exposed-pad vias: six soldered component-land vias in total.** C32's
supply via keeps that bypass close to U14 despite the crowded escape area.
Confirm the fill/cap process and all affected land/paste geometry with JLCPCB;
ordinary open or merely tented holes are not the assembly assumption here.
TP17 also overlaps a via on its back-side probe land; this unsoldered test pad
does not add a backside component or require solder-wicking protection.

## U12 ILM review

The previous USB_ILM routing was 54.094 mm long and left the remote buffer
and test-point branch open. R56–R61, Q1/Q2, their gate pull-downs, U19/C34 and
TP14 have been regrouped near U12. USB_ILM now contains **22.934913 mm of
copper**, with all setting/input/test pads within **8.989994 mm of U12.9**.
The setting branches stay on F.Cu; the nearby back-side TP14 uses a short
via branch. U19's local feedback is routed, and its buffered output reaches
R64/C33 and ADC1. Current-limit resistor values and the schematic are unchanged.

The input copper audit checks the complete ILM/telemetry connections and
limits ILM copper to 40 mm and setting/input/test-pad radius to 10.5 mm.
These budgets prevent a return to the earlier spread-out placement.
They do **not** prove the TPS25947's less-than-50-pF ILM loading requirement.
Parasitic capacitance, switching pickup, current-limit accuracy and stability
still require engineering review and bench measurements. See
[TI TPS25947 layout guidance](https://www.ti.com/lit/ds/symlink/tps25947.pdf).

The affected actuator and control connections were restored. The ACT_5V
cross-board feed keeps 0.75 mm copper and crosses the USB route on In2,
with paired 0.60/0.30 mm transition vias at each end. In1 separates the two
circuits. The affected main 3.3 V connection uses 0.50 mm copper. Local
bypass, logic, current-sense and test connections were repaired and checked;
power capacity, heating and switching return currents are not established
by connectivity alone.

## Automated validation

Run from the repository root with KiCad's Python:

```powershell
$kicadPython = "$env:LOCALAPPDATA/Programs/KiCad/10.0/bin/python.exe"
& $kicadPython hardware/kicad/verify_usb_layout.py
& $kicadPython hardware/kicad/test_usb_layout_checks.py
& $kicadPython hardware/kicad/verify_input_layout.py
& $kicadPython hardware/kicad/test_input_layout_checks.py
& $kicadPython hardware/kicad/verify_distribution_layout.py
python hardware/kicad/export_pcb_review.py
```

The ten USB test methods cover a changed reference dielectric, all four open
data legs, width, pair spacing, a wrong
signal layer, an added signal via, absent saved ground fill, a small local
plane void with ground connectivity preserved, and removal of the direct
ESD via. Reports include the exact PCB SHA-256. The input suite also injects
buffer/ADC opens and excessive ILM copper length. Run physical DRC and
schematic parity alongside these checks; continuity alone cannot detect
all shorts or clearance problems.

Final validation: **0 physical DRC violations, 0 schematic-parity issues,
and 204 native unrouted connections** (247 at the start). All five copper
checkers pass. All **37 regression test methods** pass: buck 3, input 11,
actuator 10, distribution 3 and USB 10, including their fault-injection
subcases. Static power, wheel/brake and encoder/harness checks pass.
Front/back placement exports were visually inspected. Existing DRC exclusions
are unchanged; the added rules enforce USB and non-USB trace widths.
The R49 ground-open test now selects the actual pad connections after its move.

## Acceptance still open

The route follows the placement/reference principles in
[Espressif's ESP32-S3 PCB guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html)
and [TI's TPD2EUSB30 guidance](https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf).
The selected geometry is a **90-ohm design target**, not measured impedance.
Nearby front-layer pads/traces and local fanouts depart from an ideal uniform
non-coplanar structure. Review those discontinuities and neighboring copper
with the final stackup; request the fabricator's impedance tolerance, CAM
adjustments and coupon/test provision before releasing production files.

Finish SPI, optical and remaining board routing, then review the full layout,
analog returns, route lengths, thermal paths and test access. USB enumeration,
signal quality in both plug orientations, ESD, power transitions and suspend
behavior remain hardware tests. Mechanical fit and a complete manufacturing
package are also outstanding.
