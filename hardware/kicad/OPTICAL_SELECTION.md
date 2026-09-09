# Optical sensor alternatives for V1

Research checked 2026-09-09. **Recommendation: PMW3360DM-T2QU with LM19-LSI
for the first wired prototype.** PAW3395DM-T6QU remains the stronger performance
alternative if its supplied lens and initialization documentation are confirmed.
This records selection research. Revision 0.7 now implements PMW3360 in the
[optical circuit](OPTICAL_DESIGN.md), using the original GPIO allocation.
No sensor or lens has been ordered.

## Fit to MagMouse

The [architecture](../../docs/architecture.md) targets a wired ESP32-S3 mouse
with a 1ms USB HID report interval. The sensor must track planar mouse-pad/desk
motion while haptic buttons and the wheel operate. Battery life and 8kHz USB
reports are outside V1. Glass tracking is not an established requirement.

The assessment below is an engineering recommendation from specifications and
procurement evidence, not measured performance in this mouse. Sensor frame rate,
SPI transfer rate and USB report rate are different quantities. Changing the
sensor does not itself improve the host report interval.

| Candidate | Manufacturer specification | Assessment |
| --- | --- | --- |
| [PMW3360DM-T2QU](https://www.pixart.com/products-detail/10/PMW3360DM-T2QU) + LM19-LSI | 12,000 CPI; >250ips on product page; 50g; 4-wire SPI; 23.4mA run current | Best documented and sourced exact pair found for V1. Lower tracking-speed ceiling and greater power consumption than PAW3395. |
| [PAW3395DM-T6QU](https://www.pixart.com/products-detail/129/PAW3395DM-T6QU) + supplier-confirmed lens | 26,000 CPI; 650ips; 50g; 4-wire SPI; 1.7mA HP / 1.3mA LP run current on product page | Higher performance alternative. Retail kit found, but exact included lens is unnamed. |
| [PMW3389DM-T3QU](https://www.pixart.com/products-detail/4/PMW3389DM-T3QU) + LM19-LSI | 16,000 CPI; 400ips; 50g; 4-wire SPI; approximately 21mA run current | Suitable on paper, but no better verified supply route found than PMW3360. |
| [PMW3610DM-SUDU](https://www.pixart.com/products-comparison/cn/7/Optical_Mouse_Sensor) | 3,200 CPI; 30ips; 10g; 0.6mA run current | Not the preferred substitute for a gaming-capable wired mouse. Its power benefit does not justify the reduced tracking envelope here. |

Run-current figures are manufacturer headline values under different operating
conditions, not interchangeable USB current budgets. Use maximum rail currents,
illumination, regulator losses and operating modes when completing the design.
The PMW3360 datasheet gives 250ips typical; use that conservative figure when
planning tests rather than treating the product-page value as a guarantee.

## Concrete supplier leads

### PMW3360 and the exact lens

[Yushakobo sensor/lens set](https://shop.yushakobo.jp/en/products/11274),
SKU **A080040-01-1**, explicitly offers **PMW3360DM-T2QU / LM19-LSI**. The live
selected variant showed **35 sets in stock** with Add to cart enabled.
The localized browser showed **JPY2,900**, while the public English page showed
**JPY3,190 including Japanese tax**. The retailer says it buys through a domestic
authorized distributor; this is its provenance claim, not an independent audit.
Select LM19-LSI, not the separately offered `L0AE-LSI` variant.

The [tax FAQ](https://shop.yushakobo.jp/en/pages/faq) says Japanese consumption
tax is removed for overseas orders. Its
[shipping guidance](https://yushakobo.zendesk.com/hc/ja/articles/360048472334-%E6%B5%B7%E5%A4%96%E7%99%BA%E9%80%81%E3%81%AB%E5%AF%BE%E5%BF%9C%E3%81%97%E3%81%A6%E3%81%84%E3%81%BE%E3%81%99%E3%81%8B-Do-you-offer-international-shipping)
limits service to eligible countries. Delivery to Croatia and landed cost have
not been verified at checkout. Shipping, destination taxes and any forwarding
cost are additional; these prices are not an assembled-board quote.

### PAW3395 kit

[EFOG.TECH PAW3395 upgrade](https://efog.tech/products/paw3395-upgrade) showed
**EUR31.50, In Stock**, with the **Not soldered** option and enabled Add to cart.
The kit contains two sensors, two lenses, two daughterboards and two FPC cables:
EUR15.75 per sensor/lens share of the kit, but the purchase unit is the whole kit.
The soldered option advertises EUR5 extra. Do not select the EUR5
**daughterboards-only** option expecting sensors.

The page does not specify the lens MPN or the complete sensor suffix. Its
linked [firmware](https://github.com/efogtech/endgame-trackball-config/tree/paw3395)
targets the seller's trackball. Neither the FPC pinout nor that firmware has
been qualified for MagMouse. Shipment eligibility and final taxes are unverified.
This is a useful sample lead; it is not yet a repeatable production supply chain.

### Listings that are not available stock

[LCSC C20612443](https://www.lcsc.com/product-detail/C20612443.html) for PMW3360
shows out of stock; its approximately USD2.43 reference price is not a usable
purchase quote. The canonical
[Joe's Sensors and Sundry breakout page](https://lectronz.com/products/pmw3360-motion-sensor)
also shows out of stock. A search-engine/CDN copy advertised stock, so the
canonical page was used. Do not base procurement on those cached results.

## Circuit, optics and firmware evidence

Inspected Figures 4, 6 and 10 of the
[PixArt PMW3360 datasheet, revision 1.50, 26 September 2016](https://datasheet.lcsc.com/datasheet/pdf/c018c3e1d470821feefadd37e2f785d5.pdf?productCode=C20612443).

| Item | Verified starting point from that datasheet |
| --- | --- |
| Supply | VDD 1.80-2.10V; VDDIO 1.80-3.60V, at least VDD. Nominal 1.9V core gives tolerance margin. |
| Serial interface | 2MHz maximum; 35us motion-burst delay; up to 12 data bytes. |
| Optical height | Lens flange to surface: 2.4mm nominal, 2.2-2.6mm range. Distinct from PCB height and lift-off distance. |
| Mechanical envelope | Lens: 21.15 x 18.85mm. Illustrated 1.6mm PCB top: 7.40mm above surface. |
| Assembly | No-wash soldering; fixture protects apertures and controls seating. Lens/base features establish alignment. |
| Initialization | Host SROM upload required; redistribution provenance remains open. |

The [QMK pointing-device documentation](https://docs.qmk.fm/features/pointing_device#pmw-3360-and-pmw-3389-sensor)
provides an existing PMW3360/3389 driver integration reference. This is evidence
of an implementation path, not an ESP32-S3 port or permission to relicense every
embedded firmware payload. Review the chosen code and SROM provenance before
adding either to the GPL firmware tree.

PAW3395's [manufacturer product page](https://www.pixart.com/products-detail/129/PAW3395DM-T6QU)
names LM19-LSI and L0AE-LSI1; its
[general datasheet](https://datasheet.lcsc.com/lcsc/2504101957_PixArt-PAW3395DM-T6QU_C41346211.pdf)
directs readers to separate lens drawings. Do not infer EFOG's supplied lens
from that compatibility list, or assume the differently written lens suffixes
in other shops are interchangeable.

### Impact on the existing allocation

The reserved signals can support a PMW3360 circuit without an extra MCU GPIO:

| Existing net | ESP32-S3 GPIO | Intended PMW3360 use |
| --- | --- | --- |
| SPI_MOSI / SPI_MISO / SPI_SCLK | 11 / 13 / 12 | Shared SPI2 with per-device configuration |
| CS_PAW | 2 | Optical chip select; retain the net name for now |
| PAW_MOTION_N | 39 | Motion interrupt |
| OPT_CTRL | 26 | Reset/control; verify boot bias and supply sequencing in the circuit review |

Calculated full-burst time: `13 x 8 / 2MHz + 35us = 87us`, or 8.7% of 1ms,
before guards/software overhead. Reserve SPI2 throughout, including the delay.
Combined optical, ADC1, IMU, angle and driver traffic still needs measurement.

The sensor footprint, power circuit, reset behavior and firmware differ from
PAW3950. Renaming its reservation is not a circuit substitution. Mechanical
placement must also isolate optical alignment from button flex and wheel vibration.

## JLCPCB assembly route

The live [PMW3360 consignment entry C9900151196](https://jlcpcb.com/partdetail/JLCPCBAssembly-PMW3360DMT2QU/C9900151196)
shows zero stock, unavailable for purchase and **Consign Part**. It lists wave
soldering and Economic/Standard assembly. Its tiny estimated price is not the
cost of buying a sensor. Exact part acceptance, fixture and process still need
an assembly quote; the lens is a separate mechanical item.

Two workable prototype routes are:

1. Have JLC assemble the ordinary components; fit the sourced through-hole
   sensor and lens during controlled final assembly.
2. Supply accepted sensors through JLC's
   [consignment process](https://jlcpcb.com/help/article/how-to-consign-parts-to-jlcpcb),
   with optical protection and seating requirements included in the quote.

Overseas consignment adds shipping, import processing and handling. For a small
prototype batch it may cost more than fitting the sensor locally. No verified
stocked, all-from-JLC sensor-and-lens solution was found in this review.

## Implementation and remaining acceptance

- Revision 0.7 implements PMW3360DM-T2QU + LM19-LSI; retain PAW3395 as the
  higher-performance alternative pending exact kit identity.
- Confirm sample delivery and obtain the exact lot, matching lens and usable
  initialization/SROM information. No supplier message or purchase was made.
- The [optical sheets and footprint](OPTICAL_DESIGN.md) are now added, including
  switched local power and SPI isolation. Qualify them on hardware.
- The [lens datums](../../mechanical/optical/README.md) are documented; verify
  samples before cutting the aperture or freezing mounting locations.
- Measure tracking, lift/reacquisition, startup/suspend and 1kHz reports on
  intended surfaces, with each actuator separately and all actuators together.

The comparison, initial circuit and sample leads are complete. Procurement
acceptance, firmware-data clearance and physical validation remain open.
