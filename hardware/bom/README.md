# Preliminary V1 component inventory

Planning inventory updated for the elastic-paddle/custom-coil direction selected
on 2026-09-08; not a purchasing or assembly BOM. `ideas.md` is historical.
Quantities are per mouse; alternatives are not additive. Confirm exact orderable
parts, packages, footprints, ratings and availability before procurement.

The [KiCad starter BOM](../kicad/README.md) is the source of truth for circuits
already drawn: revision 0.4 has 150 component instances with complete MPN,
catalog ID and footprint fields. The broader inventory below also includes
subsystems that have not been implemented. See [sourcing evidence](../kicad/SOURCING.md).

| Qty | Candidate | Purpose / unresolved detail |
| --- | --- | --- |
| 1 | ESP32-S3-MINI-1-N8 | GPIO/resource allocation recorded; firmware timing validation pending |
| 1 | PAW3950DM-T5QU | Optical X/Y tracking; exact reference implementation required |
| 1 | LOAE-LSI1 | Optical lens; confirm mechanical stack |
| 1 | TLV74318 | Proposed local optical 1.8 V LDO |
| 1 | ICM-42688-P | Supplementary accelerometer/gyro |
| 3 | TMAG5253BA2 | Left, middle and right analog Hall sensing |
| 3 | Axial NdFeB sensing magnet, TBD | Separate button position magnets; dimensions/grade set by Hall gap/range |
| 2 | ADS7038 | ADC1 drawn for buttons/system; ADC2 selected for wheel on dedicated SPI3, circuit pending |
| 3 | Custom stationary wound-copper coil | One per moving-magnet button actuator; prototype OD 6-8 mm, height 2-4 mm; winding TBD |
| 3 | N52 actuator magnet, prototype diameter 4-5 mm x 1.5-2 mm | Moves with paddle; separate from sensing magnet; size/grade not frozen |
| 3 | Printed coil former/mount | Stationary coil support; integrated or separate bobbin TBD |
| 0-3 | Soft-steel yoke/back iron, experimental | Optional magnetic-circuit trial; geometry and effect on passive return TBD |
| 3 | Elastic paddle/flexure assembly | Passive return, mechanical stops and magnet mounts; replaceable-part design target |
| 3 | DRV8231ADSGR | Bidirectional coil drivers with current feedback/regulation; C5139865 |
| 1 | MA735 | Absolute wheel-angle sensor |
| 1 | Diametric magnet, TBD | Dedicated coaxial encoder magnet |
| 1 | SteadyWin/TSL GB1806 (PM1806), no encoder | Scroll motor; verify exact winding and variant |
| 1 | DRV8316R | SPI-configurable BLDC driver; 3-PWM with analog current outputs selected |
| 1 | Single-data-pin addressable RGB LED, MPN TBD | Selected by user; RMT data on GPIO45 |
| TBD | RGB supply/data interface | Select exact LED, level shifting/isolation and suspend behavior |
| 1 | TPS62162DSGR | Selected fixed 3.3 V buck; C40256 |
| 1 | TYPE-C-31-M-12 | Data and VBUS; C165948 |
| 0 | External CC Rd resistors | TUSB320 integrates Rd; do not populate extra parallel terminations |
| 1 | TUSB320LAIRWBR | CC sink/current detector; C132554; GPIO mode |
| 1 | TPD2EUSB30DRTR | USB data ESD protection; C97502 |
| 2 | 33 ohm USB series resistors | Draft value per ESP32 implementation |
| 1 | TS-1088-AR02016 reset/EN button | Recovery; C720477 |
| 1 | TS-1088-AR02016 boot button | Download-mode recovery; C720477 |
| 1 set | Programming/test pads | 3V3, GND, EN, GPIO0, UART and measurements |
| TBD | Decoupling and bulk capacitors | Device-specific, logic and driver transients |
| TBD | Pull-ups/pull-downs | Boot, control and fault states |
| 1 set | SWPA4020S3R3MT and local output capacitors | 3.3 uH filter and 30 uF nominal capacitance; see KiCad BOM |
| TBD | Optical passives | Exact PAW3950 reference circuit |
| TBD | Current-setting/scaling/filter components | DRV8231A IPROPI/VREF and wheel feedback |
| 1 set | TPS259470LRPWR x2, TVS clamps, TLV9001 and passives | Input/actuator protection and telemetry; see power review |
| 3 | B2B-PH-SM4-TBT(LF)(SN) | Two-pin SMT coil headers; C265003; harnesses separate |
| TBD | Other connectors and mounting hardware | Wheel motor and mechanical assembly |
| 1 set | SN74LVC1G123, SN74LVC08A x3 and SN74LVC2G04 | Heartbeat timeout, source/reset qualification, sensor enable and six drive gates |

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
