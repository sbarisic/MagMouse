# Draft sourcing and symbol review

Checked 2026-09-08. Identifiers below were matched to catalog manufacturer part
numbers. Only the driver and regulator were also verified on direct JLCPCB
catalog pages; other entries were checked at LCSC. Recheck JLCPCB assembly stock,
package, price and service eligibility before freezing the BOM. No stock is reserved.

| References | Manufacturer part number | Catalog |
| --- | --- | --- |
| U4-U6 | TI DRV8231ADSGR | [JLC C5139865](https://jlcpcb.com/partdetail/TexasInstruments-DRV8231ADSGR/C5139865) |
| U2 | TI TLV62569DBVR | [JLC C141836](https://jlcpcb.com/partdetail/TexasInstruments-TLV62569DBVR/C141836) |
| U3 | Espressif ESP32-S3-MINI-1-N8 | [LCSC C2913206](https://www.lcsc.com/product-detail/C2913206.html) |
| J1 | Korean Hroparts TYPE-C-31-M-12 | [LCSC C165948](https://www.lcsc.com/product-detail/C165948.html) |
| 10 kOhm resistors | UNI-ROYAL 0603WAF1002T5E | [LCSC C25804](https://www.lcsc.com/product-detail/C25804.html) |
| 3.3 kOhm resistors | UNI-ROYAL 0603WAF3301T5E | [LCSC C22978](https://www.lcsc.com/product-detail/C22978.html) |
| R5, R6, 33 Ohm | UNI-ROYAL 0603WAF3300T5E | [LCSC C23138](https://www.lcsc.com/product-detail/C23138.html) |
| 100 nF capacitors | YAGEO CC0603KRX7R9BB104 | [LCSC C14663](https://www.lcsc.com/product-detail/C14663.html) |
| 10 uF / 25 V capacitors | Samsung CL21A106KAYNNNE | [LCSC C15850](https://www.lcsc.com/product-detail/C15850.html) |

Use the schematic fields as the editable source of truth. `LCSC` and
`JLCPCB Part #` contain the same identifier. `Sourcing Status`, `Checked`,
`Manufacturer`, `MPN` and `Supplier URL` preserve the extent of verification.
Do not substitute parts by value alone: voltage, tolerance, capacitor bias,
inductor saturation, package and pin mapping matter.

## Unresolved sourcing

| References | Selection still required |
| --- | --- |
| U1 | TPD2EUSB30DRTR sourcing; SOT-3 candidate footprint assigned |
| U7-U9 | TMAG5253BA2IQDMRR sourcing; tiny X2SON assembly/package review |
| U10 | ADS7038IRTER sourcing; WQFN assembly/package review |
| C4, C19-C21 | Exact 1 uF / 16 V 0603 capacitors and bias/tolerance review |
| R1, R2 | Exact 100 kOhm and 22.1 kOhm 0603 resistors |
| L1 | 2.2 uH shielded power inductor; saturation, DCR, thermal rating and footprint |
| SW1, SW2 | Tactile switches and matching footprints |
| J2-J4 | Coil connector family, current rating, orientation and footprints |

These 17 component instances have no LCSC number. L1, SW1/SW2 and J2-J4 also
have no footprint. Subsystems absent from the schematic are additional future
BOM items. This partial BOM is not a total mouse electronics cost estimate.

## Symbol and package provenance

Standard symbols and assigned footprints come from the installed KiCad 10.0
libraries. The project-local [MagMouse.kicad_sym](MagMouse.kicad_sym) contains:

- `DRV8231ADSG`: derived from KiCad's `Driver_Motor:DRV8231ADSG`. Changed pin 8
  OUT2 from power-input to output, matching the
  [TI datasheet](https://www.ti.com/lit/ds/symlink/drv8231a.pdf). Pins 6/8 are
  outputs, 5 VM, 7 ground, 9 exposed pad, 3/2 IN1/IN2, 4 VREF and 1 IPROPI.
- `TMAG5253BA2IQDMRR`: newly drawn from the
  [TI datasheet](https://www.ti.com/lit/ds/symlink/tmag5253.pdf). Pins 1 VCC,
  2 GND, 3 EN, 4 OUT; pad 5 EP is connected to ground. DMR0004A uses a
  1.1 x 1.4 mm body, 0.5 mm pitch and 0.8 x 0.6 mm exposed pad.
- `ADS7038IRTER`: newly drawn from the
  [TI datasheet](https://www.ti.com/lit/ds/symlink/ads7038.pdf). AIN0-AIN7 map
  to pins 15,16,1,2,3,4,5,6. AVDD 7, DECAP 8, GND 9, DVDD 10, CS 11,
  SDO 12, SCLK 13, SDI 14 and EP 17. RTE0016C uses a 3 x 3 mm body,
  0.5 mm pitch and 1.68 x 1.68 mm EP. The assigned footprint is
  `Package_DFN_QFN:WQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm`.

The standalone `MagMouse.kicad_sym` library is distributed under
CC-BY-SA-4.0 with the KiCad libraries exception. Attribution: KiCad library
contributors for the DRV8231ADSG source; MagMouse contributors for the correction
and new Hall/ADC symbols. See [the included upstream notice](KICAD-LIBRARY-LICENSE.md)
and [the license text](https://creativecommons.org/licenses/by-sa/4.0/legalcode).
The electronic design remains under the repository's CERN-OHL-S-2.0 license.

Datasheet mapping and footprint existence checks are preliminary review evidence;
they do not establish land-pattern, stencil or assembly sign-off. In particular,
inspect exposed pads and USB shield mounting in the eventual layout.
