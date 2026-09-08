# Preliminary V1 component inventory

Planning inventory transcribed from `ideas.md`, not a purchasing or assembly BOM.
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
| 3 | Axial NdFeB magnet, TBD | Button position magnets; dimensions/grade TBD |
| 1 | ADS7038 | Eight-channel ADC; six assigned inputs |
| 3 | LVCM-013-008-02 | Button voice coils; force/stroke/thermal validation needed |
| 3 | DRV8874 | Bidirectional coil drivers with current feedback/regulation |
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
| TBD | Current-setting/scaling/filter components | DRV8874 IPROPI/current reference and wheel feedback |
| TBD | Input protection and power monitoring | Inrush, current limits, reverse current and VBUS sensing |
| TBD | Connectors and mounting hardware | Motor, voice coils, mechanical assembly |

The external powered hub/adapter is not included in this mouse BOM. Do not fit
external Rd resistors in parallel with integrated Rd without checking the detector
datasheet. A complete schematic will establish reference designators and values.
