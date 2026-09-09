# Draft sourcing and symbol review

Revision 0.7, checked 2026-09-09. All 272 components in the present schematic
have manufacturer part numbers, catalog identifiers and assigned footprints.
New USB-C power parts, changed regulator/inductor, package evidence and assembly
constraints are documented in [POWER_REVIEW.md](POWER_REVIEW.md). The historical
revision 0.2 selections below identify retained parts and superseded decisions.
Recheck assembly stock, prices and service eligibility before ordering; none is
reserved. Optical sensor availability remains separate from its catalog identity.
Wheel part identities, pinouts, custom packages and brake tolerances are in
[WHEEL_REVIEW.md](WHEEL_REVIEW.md).

Revision 0.4 adds R72-R80 using the existing 10 kOhm C25804 selection and
TP16-TP33 as copper test pads, excluded from the assembly BOM. The second ADC
and addressable RGB were allocated interfaces in that revision. Revision 0.5
implements ADC2 and the wheel subsystem. Revision 0.6 adds IMU/RGB; see
[PERIPHERAL_REVIEW.md](PERIPHERAL_REVIEW.md) for catalog and package evidence,
and [OPTICAL_REVIEW.md](OPTICAL_REVIEW.md) for optical sourcing gaps. The subsequent
[sensor selection review](OPTICAL_SELECTION.md) records in-stock retail sample
leads for PMW3360/LM19-LSI and a PAW3395 kit, plus JLC consignment limitations.
Revision 0.7 adds PMW3360 and its supporting circuit to the schematic/BOM;
see [optical design](OPTICAL_DESIGN.md). The lens remains an external purchase.

Revision 0.5 also corrects R5/R6/R58 sourcing: the intended 33 ohm value now
uses **0603WAF330JT5E / C23140**. C23138 is a **330 ohm** resistor and is now
used for the 330 ohm current filters R102–R104 and RGB series resistor R128. Intended USB and
current-limit resistance values are unchanged.

| References | Manufacturer part number | Catalog |
| --- | --- | --- |
| U4-U6 | TI DRV8231ADSGR | [JLC C5139865](https://jlcpcb.com/partdetail/TexasInstruments-DRV8231ADSGR/C5139865) |
| U2 | TI TPS62162DSGR | [JLC C40256](https://jlcpcb.com/partdetail/TexasInstruments-TPS62162DSGR/C40256) |
| U3 | Espressif ESP32-S3-MINI-1-N8 | [LCSC C2913206](https://www.lcsc.com/product-detail/C2913206.html) |
| J1 | Korean Hroparts TYPE-C-31-M-12 | [LCSC C165948](https://www.lcsc.com/product-detail/C165948.html) |
| 10 kOhm resistors | UNI-ROYAL 0603WAF1002T5E | [LCSC C25804](https://www.lcsc.com/product-detail/C25804.html) |
| 3.3 kOhm resistors | UNI-ROYAL 0603WAF3301T5E | [LCSC C22978](https://www.lcsc.com/product-detail/C22978.html) |
| R5, R6, R58, 33 Ohm | UNI-ROYAL 0603WAF330JT5E | [LCSC C23140](https://www.lcsc.com/product-detail/C23140.html) |
| 100 nF capacitors | YAGEO CC0603KRX7R9BB104 | [LCSC C14663](https://www.lcsc.com/product-detail/C14663.html) |
| 10 uF / 25 V capacitors | Samsung CL21A106KAYNNNE | [LCSC C15850](https://www.lcsc.com/product-detail/C15850.html) |

Use the schematic fields as the editable source of truth. `LCSC` and
`JLCPCB Part #` contain the same identifier. `Sourcing Status`, `Checked`,
`Manufacturer`, `MPN` and `Supplier URL` preserve the extent of verification.
Do not substitute parts by value alone: voltage, tolerance, capacitor bias,
inductor saturation, package and pin mapping matter.

## Historical selections resolved in revision 0.2

R1/R2 and the 2.2 uH L1 below are superseded in revision 0.3. Their resistor
part types remain used elsewhere; L1 is now the 3.3 uH variant. The associated
TLV62569 calculations are historical, not the current regulator design.

| References | Selected manufacturer part number | JLCPCB catalog | Library type |
| --- | --- | --- | --- |
| U1 | TI TPD2EUSB30DRTR | [C97502](https://jlcpcb.com/partdetail/TexasInstruments-TPD2EUSB30DRTR/C97502) | Extended |
| U7-U9 | TI TMAG5253BA2IQDMRR | [C35414983](https://jlcpcb.com/partdetail/37150530-TMAG5253BA2IQDMRR/C35414983) | Extended |
| U10 | TI ADS7038IRTER | [C2871580](https://jlcpcb.com/partdetail/C2871580) | Extended |
| C4, C19-C21 | Samsung CL10A105KB8NNNC, 1 uF / 50 V, X5R, 10%, 0603 | [C15849](https://jlcpcb.com/partdetail/16531-CL10A105KB8NNNC/C15849) | Basic |
| R1 | UNI-ROYAL 0603WAF1003T5E, 100 kOhm, 1%, 0603 | [C25803](https://jlcpcb.com/partdetail/C25803) | Basic |
| R2 | UNI-ROYAL 0603WAF2212T5E, 22.1 kOhm, 1%, 0603 | [C25961](https://jlcpcb.com/partdetail/26704-0603WAF2212T5E/C25961) | Extended |
| L1 | Sunlord SWPA4020S2R2MT, 2.2 uH, 20% | [C83423](https://jlcpcb.com/partdetail/Sunlord-SWPA4020S2R2MT/C83423) | Extended |
| SW1, SW2 | XUNPU TS-1088-AR02016 | [C720477](https://jlcpcb.com/partdetail/XUNPU-TS_1088AR02016/C720477) | Basic |
| J2-J4 | JST B2B-PH-SM4-TBT(LF)(SN) | [C265003](https://jlcpcb.com/partdetail/JST-B2B_PH_SM4_TBT_LF_SN/C265003) | Extended |

The Hall and ADC listings were verified in the live browser because indexed
searches did not expose the exact entries. The Hall sensor and its pinout stay
unchanged. Capacitor values now show their selected 50 V rating instead of the
earlier 16 V minimum. No signal connections or resistor ratios changed.

## Newly assigned footprints

All six assignments use installed KiCad 10 libraries. No downloaded EasyEDA
footprint is required.

| References | KiCad footprint | Drawing comparison |
| --- | --- | --- |
| L1 | `Inductor_SMD:L_Sunlord_SWPA4020S` | 4 x 4 x 2 mm body; pads 1.1 x 3.7 mm at x = +/-1.5 mm; 1.9 mm inner gap |
| SW1, SW2 | `Button_Switch_SMD:SW_SPST_TS-1088-xR020` | 3.9 x 3 x 2 mm body; two 1.05 x 2 mm pads at x = +/-2.225 mm; 3.4 mm inner gap, 5.5 mm outer span |
| J2-J4 | `Connector_JST:JST_PH_B2B-PH-SM4-TB_1x02-1MP_P2.00mm_Vertical` | Two contacts on 2 mm pitch, 1 x 5.5 mm pads; two mechanical retention lands, 1.6 x 3 mm |

L1 was checked against the [Sunlord SWPA datasheet, revision 2021/05/15](https://atta.szlcsc.com/upload/public/pdf/source/20210916/AC798BA7E846B7D0B6818F45CD84DB0B.pdf),
dimensions on page 2, ratings on page 7 and definitions on page 16. The tabulated
values are 52 mOhm maximum DCR, 3.4 A saturation current (3.7 A typical) and
1.85 A heat-rating current (2.8 A typical). Saturation means approximately 30%
inductance reduction; heat rating uses a 40 C rise from 20 C ambient. These are
distinct limits. Use a provisional **1 A continuous logic-rail target** pending
thermal validation; the regulator's 2 A capability is not board-level acceptance.
At 5 V input, 3.315 V output, 2.2 uH and typical 1.5 MHz switching, calculated
ripple is approximately 0.34 A peak-to-peak and peak current approximately 1.17 A
at 1 A load. Temperature, tolerances, transients and fault current still need review.

SW1/SW2 were checked against [XUNPU TS-1088-AR drawing, revision A](https://datasheet.lcsc.com/datasheet/pdf/0475ac02febf455ca9ddcfb380b0df0d.pdf?productCode=C720477).
The drawing specifies the two-terminal normally-open circuit and 50 mA / 12 V
contact rating. These switches only provide reset/boot recovery. Their rating
exceeds the roughly 0.33 mA through the 10 kOhm pull-up at 3.3 V.

J2-J4 were compared with the [JST PH series drawing](https://datasheet.lcsc.com/datasheet/pdf/91225f8a61c6f7b7821281d8757bf5b1.pdf?productCode=C2941743),
pages 1 and 3 (no revision printed). The SMT body is 7.95 mm wide and 6.6 mm
high, approximately 8.6 mm when mated. Reserve space above it for wire exit.
The series rating is 2 A with AWG24 wire; select contact/wire combinations for
the eventual harness rather than applying that rating to every wire gauge.
The mating housing is PHR-2 with compatible PH crimp contacts. Harnesses remain
separate assembly items. Pin 1 is COIL_P and pin 2 COIL_N; neither is ground.
Both retention pads marked MP are mechanical and intentionally have no signal net.

The 1 uF capacitor has the same 0603 outline as the draft and a higher voltage
rating. Effective capacitance at operating bias, tolerance and temperature still
needs checking during ADC/power validation. Catalog selections are complete for
this draft; live stock checks, circuit, stencil and enclosure sign-off remain separate.

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
contributors for the DRV8231ADSG and D_Schottky sources; MagMouse contributors
for corrections, new Hall/ADC symbols and the power symbols listed in
[POWER_REVIEW.md](POWER_REVIEW.md), and the wheel symbols in
[WHEEL_REVIEW.md](WHEEL_REVIEW.md). See [the included upstream notice](KICAD-LIBRARY-LICENSE.md)
and [the license text](https://creativecommons.org/licenses/by-sa/4.0/legalcode).
The electronic design remains under the repository's CERN-OHL-S-2.0 license.

Datasheet mapping and footprint existence checks are preliminary review evidence;
they do not establish land-pattern, stencil or assembly sign-off. In particular,
inspect exposed pads and USB shield mounting in the eventual layout.

## Revision 0.7 optical components

See [OPTICAL_DESIGN.md](OPTICAL_DESIGN.md) for PMW3360, TLV75519, TPS22918 and
buffer identities. U35 catalog C20612443 is out of stock and is not a turnkey
assembly commitment. Plan customer-supplied or post-SMT sensor fitting; the
LM19-LSI lens is an external mechanical purchase. New passives reuse catalog
parts except C79 ([C1588](https://www.lcsc.com/product-detail/C1588.html)),
C84 ([C1705](https://www.lcsc.com/product-detail/C1705.html)) and R132
([C23154](https://www.lcsc.com/product-detail/C23154.html)). Refresh all stock and
JLC service eligibility before ordering. The prepared [supplier inquiry](../../docs/optical-sample-inquiry.md)
has not been sent.
