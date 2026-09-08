# Preliminary V1 component inventory

Planning inventory updated for the elastic-paddle/custom-coil direction selected
on 2026-09-08; not a purchasing or assembly BOM. `ideas.md` is historical.
Quantities are per mouse; alternatives are not additive. Confirm exact orderable
parts, packages, footprints, ratings and availability before procurement.

| Qty | Candidate | Purpose / unresolved detail |
| --- | --- | --- |
| 1 | ESP32-S3-MINI-1-N8 | MCU module; verify exposed pins and resource budget |
| 1 | PAW3950DM-T5QU | Optical X/Y tracking; exact reference implementation required |
| 1 | LOAE-LSI1 | Optical lens; confirm mechanical stack |
| 1 | TLV74318 | Proposed local optical 1.8 V LDO |
| 1 | ICM-42688-P | Supplementary accelerometer/gyro |
| 3 | TMAG5253BA2 | Left, middle and right analog Hall sensing |
| 3 | Axial NdFeB sensing magnet, TBD | Separate button position magnets; dimensions/grade set by Hall gap/range |
| 1 | ADS7038 | Eight-channel ADC; six assigned inputs |
| 3 | Custom stationary wound-copper coil | One per moving-magnet button actuator; prototype OD 6-8 mm, height 2-4 mm; winding TBD |
| 3 | N52 actuator magnet, prototype diameter 4-5 mm x 1.5-2 mm | Moves with paddle; separate from sensing magnet; size/grade not frozen |
| 3 | Printed coil former/mount | Stationary coil support; integrated or separate bobbin TBD |
| 0-3 | Soft-steel yoke/back iron, experimental | Optional magnetic-circuit trial; geometry and effect on passive return TBD |
| 3 | Elastic paddle/flexure assembly | Passive return, mechanical stops and magnet mounts; replaceable-part design target |
| 3 | DRV8231A | Bidirectional coil drivers with current feedback/regulation; exact package/orderable suffix TBD |
| 1 | MA735 | Absolute wheel-angle sensor |
| 1 | Diametric magnet, TBD | Dedicated coaxial encoder magnet |
| 1 | SteadyWin/TSL GB1806 (PM1806), no encoder | Scroll motor; verify exact winding and variant |
| 1 | DRV8316R | SPI-configurable BLDC driver; PWM mode TBD |
| 1 | 2020/0606 RGB LED, TBD | Status/profile indication |
| 3 | LED resistors, TBD | Values depend on LED and drive circuit |
| 1 | TLV62569 or TPS62A0569 | Candidate 5 V to 3.3 V buck; select one |
| 1 | USB-C receptacle, TBD | Data and VBUS |
| 2* | 5.1 kohm CC Rd resistors | Coordinate with chosen sink detector; may be integrated |
| TBD | Type-C sink/current detector | Required for advertised-current awareness; part/interface open |
| 1 | TPD2EUSB30 | Proposed USB data ESD protection |
| 2 | 22-33 ohm USB series resistors | Final value per ESP32 implementation |
| 1 | Reset/EN button | Recovery |
| 1 | Boot button | Download-mode recovery |
| 1 set | Programming/test pads | 3V3, GND, EN, GPIO0, UART and measurements |
| TBD | Decoupling and bulk capacitors | Device-specific, logic and driver transients |
| TBD | Pull-ups/pull-downs | Boot, control and fault states |
| TBD | Buck inductor/feedback parts | Selected regulator reference circuit |
| TBD | Optical passives | Exact PAW3950 reference circuit |
| TBD | Current-setting/scaling/filter components | DRV8231A IPROPI/VREF and wheel feedback |
| TBD | Input protection and power monitoring | Inrush, current limits, reverse current and VBUS sensing |
| TBD | Connectors and mounting hardware | Wheel motor, three wound coils, mechanical assembly |
| TBD | Hardware actuator timeout/disable circuit | Safe stop on stale control; button drivers have no dedicated fault output |

The external powered hub/adapter is not included in this mouse BOM. Do not fit
external Rd resistors in parallel with integrated Rd without checking the detector
datasheet. A complete schematic will establish reference designators and values.

The coil/magnet/former rows above describe three custom actuators; do not add a
second set of complete actuators when pricing them. There are six button magnets
(three sensing plus three actuator) and one separate wheel encoder magnet.
Custom windings and paddle/magnet assembly are separate from PCB assembly.

## Cost planning

The supplied design analysis estimates USD 2-10 per custom actuator (USD 6-30
for three), excluding its H-bridge, winding/assembly labor, tooling and development.
Its approximate USD 100-150 total electronics/electromechanics target is an
unquoted planning hypothesis, not a verified BOM total. Confirm winding fabrication,
driver package, optical sourcing, motor variant and supplier quantities before
updating the purchasing estimate. PCB fabrication/assembly, shipping and tax are
additional. See the [prototype plan](../../mechanical/button-mechanisms/README.md).
