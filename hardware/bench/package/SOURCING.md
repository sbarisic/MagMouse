# One-set sourcing checkpoint

**Purchasing constraint (2026-09-12): private-consumer suppliers only.** The
user has no business. CODICO sample-shop offers are excluded from selection,
not pending business credentials. Prefer EU stock; identify imports explicitly.

## Consumer optical candidate with Croatia shipping quote

The user selected Ploopy as the intended supplier on 2026-09-12 and will
place the order themselves later. Supplier selection is settled; exact part
identity and optical fit remain engineering checks. No order is authorized.

[Ploopy replacement PMW3360 sensor and optic](https://ploopy.co/shop/replacement-pixart-pmw-3360-mouse-sensor/),
SKU PLMKMOPMW001, is offered individually to consumers from Canada. On
2026-09-12 its cart accepted one set and calculated tracked shipping to
Bjelovar, 43000, Croatia: CAD 24.99 parts + CAD 22.02 shipping = CAD 47.01.
At the ECB 2026-09-11 rate EUR 1 = CAD 1.6064, these are approximately
EUR 15.56 + EUR 13.71 = EUR 29.26 (convert the unrounded total). The cart
displayed zero collected tax; import VAT and any handling fees are additional
and unquoted. Transit estimate is 12-32 business days, excluding dispatch time.
This confirms a shipping service quote, not stock reservation or an order.

The listing names 'PMW3360 sensor' and 'PMW3360 optic', but does not state
the exact sensor suffix and lens MPN. Confirm PMW3360DM-T2QU / LM19-LSI and
SROM availability before counting it as a qualified purchase for Main U35.
The candidate is kept separate from the qualified purchasing subtotal.
No personal street address, phone, email or payment information was entered;
no order was placed. This is an import option, not EU stock.

The EU consumer option checked, Keycapsss KC10125 (PMW3360 assembled module
with lens, EUR 29.90 displayed including VAT), has zero stock. It is also a
module rather than loose parts for Main U35. No immediately available EU-stock
consumer sensor/lens pair has been confirmed.

Wheel R113 also has an unavailable original listing, UNI-ROYAL 0603WAF3482T5E.
The bench purchasing variant uses Vishay **CRCW060334K8FKEA**, 34.8 kohm,
1%, 100 ppm/C, 0603, 0.125 W. It retains the resistance/tolerance and fits the
same non-polarized 0603 lands. R113 is in the BRAKE_DIV_TOP-to-BRAKE_SENSE
divider; even a conservative 6 V across it dissipates only 1.04 mW. The
75 V working-voltage rating and power rating exceed this use. The divider
values and existing threshold tolerance calculation are unchanged. Recheck
the received part marking/packaging before assembly; source CAD identity is
retained and the purchase substitution is explicit in `population.csv`.
[Manufacturer data](https://www.vishay.com/docs/20035/dcrcwe3.pdf),
[DigiKey exact part](https://www.digikey.com/en/products/detail/vishay-dale/CRCW060334K8FKEA/1174842).

Public listings checked 2026-09-11. The project has switched to one manually
assembled bench prototype, with five bare sets as fabrication spares. Reflow
tools are supplied by the user and are excluded from the project price.

The exact MA735GGU-P is available in cut tape at DigiKey (253 shown, USD 4.23
at quantity one). The exact LM4040AIM3-2.5/NOPB is also available there (14,529
shown, USD 2.51 at quantity one). These resolve supplier candidates for the
JLC-unavailable ICs, but not delivered pricing or reserved inventory. Sources
and observed quantities are in [the evidence record](sourcing-observations.json).

**2026-09-12 delivery correction:** Yushakobo's checkout for A080040-01-1
(PMW3360DM-T2QU with LM19-LSI) offers neither Croatia nor any EU country.
The earlier approximately EUR 17.87 catalogue estimate is not a directly
deliverable option and is excluded from the purchasing subtotal. No forwarding
service has been qualified or priced. SROM supply remains unconfirmed.

CODICO Austria lists [PMK3360IS Sample Kit (CDC)](https://www.codico.com/en/pmk3360is-sample-kit-cdc),
code 261681: five PMW3360DM-T2QU sensors plus five lenses for EUR 57.00 before
VAT. Its shipping page advertises worldwide free delivery, but its
[sample-shop terms](https://www.codico.com/en/gtc-sample-shop) restrict sales to
businesses. Availability says 'Deliverable in short time', not a firm stock
count or delivery date. Exact included lens MPN, buyer eligibility and final
Croatia checkout were not confirmed. This historical candidate is excluded
under the user's private-consumer-only purchasing constraint.

## R25 purchasing substitution

Original UNI-ROYAL 0603WAF8873T5E is out of stock, minimum 100. Select Vishay
CRCW0603887KFKEA for the bench purchasing variant: 887 kohm, 1%, 0603,
100 ppm/K, 75 V, 0.125 W versus the original 0.100 W. Its unchanged resistance,
tolerance, voltage rating and temperature coefficient preserve the divider
calculation; the package fits the existing 0603 lands. This is a nonpolar
two-terminal resistor, so there is no pin-map change. The higher power rating
does not authorize raising the circuit operating limits.

The [Vishay manufacturer specification](https://www.vishay.com/docs/20035/dcrcwe3.pdf)
and [DigiKey listing](https://www.digikey.com/en/products/detail/vishay-dale/CRCW0603887KFKEA/1175004)
support this substitution. The listing showed USD 0.10 at quantity one. Retain
the original CAD identity and record both original and purchase MPNs in the
variant BOM; do not silently change the JLC baseline or its regression checks.

## Unresolved procurement and interface items

Main L1 replacement candidate: **Bourns SRP4020CC-3R3M**. Mouser Croatia's
live listing on 2026-09-12 showed 1,784 available, MOQ/multiple one, and
EUR 0.671 each in cut tape, before tax/freight. Croatia service is explicitly
supported; most orders above EUR 75 qualify for free shipping. This is country
service confirmation, not a completed delivered cart or reserved stock.
[Exact Croatia listing](https://hr.mouser.com/ProductDetail/Bourns/SRP4020CC-3R3M?qs=1Kr7Jg1SGW9l5g8vkQq9zA%3D%3D),
[Croatia delivery policy](https://hr.mouser.com/).

The shielded Bourns part retains 3.3 uH +/-20%, reduces maximum DCR from
91 to 76 milliohms, and specifies typical 3.5 A heating / 4.0 A saturation
currents under its stated test conditions. These support its electrical
candidacy for U2 TPS62162's 3.3 V / 1 A supply. It is **not a drop-in purchase**:
its recommended solder lands differ from L_Sunlord_SWPA4020S. The existing
L1 pads measure 1.1 x 3.7 mm at 3.0 mm centre spacing; a local footprint,
copper and stencil update plus repeated power/DRC/parity checks is required.
No source-board or BOM substitution has been made. Converter heating and
noise still need bench verification. The earlier Eaton stock figure is stale
and is not used as current purchasing evidence.
[Bourns specification](https://www.bourns.com/docs/product-datasheets/srp4020cc.pdf),
[TI regulator guidance](https://www.ti.com/lit/ds/symlink/tps62160.pdf).

- The Wurth FFC still has stripped-length and width/pitch-span tolerance
  differences from the Hirose drawing. A Molex Type-A lead was investigated,
  but its public page did not supply the required mating tolerances. Neither
  is declared a qualified replacement. Keep the existing reverse contact map
  J8.N to J9.(31-N); no wiring or buffer changes are made.
- The SteadyWin motor-only listing shows USD 12.60 but ambiguous availability.
  Confirm the motor-only variant and its drawing before freezing a bolt-on
  adapter. Do not use an encoder-equipped price for a motor-only BOM.
- Power, encoder and button harnesses need matching housings, contacts or
  precrimp leads, in addition to the headers already in the PCB BOM.
- Magnets, coil materials, adjustable fixture materials and consumables remain
  explicit open purchasing lines. Tools are excluded, not these materials.

No complete delivered component total is claimed. Unknown costs remain blank,
never zero. The authorized Wurth enquiry was sent; see WURTH_ENQUIRY.md.
No orders or payment have been submitted.
