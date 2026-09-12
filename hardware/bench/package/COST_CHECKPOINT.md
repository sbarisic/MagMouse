# Bench prototype cost checkpoint

Fabrication checked 2026-09-11; supplier delivery reviewed 2026-09-12. **Quotes only; no order submitted or payment made.**
Destination Croatia 43000. Five bare complete sets plus one 0.10 mm unframed
stencil. Components, cables and mechanisms are excluded from this first table.

| Fabrication option | PCB fabrication, EUR | Stencil, EUR | Delivered total, EUR (converted) |
|---|---:|---:|---:|
| Five three-design panels, fixed stack, no paid impedance test | 138.11 | 6.59 | 224.55 |
| Same panels, paid 90 ohm impedance service | 166.34 | 6.59 | 252.46 |
| Five each separate Main/Wheel/Encoder, fixed stack, no paid impedance test | 232.25 | 6.59 | 335.96 |

The cart displayed EUR; checkout displayed USD. Delivered figures above are
converted using the ECB 2026-09-11 rate, EUR 1 = USD 1.1592; they are not a
new EUR-denominated checkout guarantee. They include DHL Express DDP and
JLC's calculated duties/taxes. The economy panel saves about EUR 27.91 against
guaranteed impedance and EUR 111.40 against separate boards.
All options retain ENIG, filled/capped vias and the specified four-layer stack.
These historical quotes predate the soldered-wire revision and its drill/paste changes; the regenerated
files have not been uploaded or accepted by CAM in this draft-only task.
The saved separate quotes are Main Y11, Wheel Y12 and Encoder Y13. The panel
is Y10 and the shared stencil is SO12609120215.

## One population of electronics

The generated purchasing list covers 282 populated component references, grouped into
63 MPN/footprint lines. U32 is the only deliberately omitted functional IC.
Sixty-two lines retain public stock/quantity pricing observations, including L1:

| Supplier | Parts subtotal | Scope |
|---|---:|---|
| LCSC | EUR 41.67 | 51 lines; supplier multiples and inexpensive spares included |
| DigiKey | EUR 28.12 | 8 lines, including both ADCs, MA735 and three button drivers |
| Mouser | EUR 4.04 | 3 lines, including three Hall sensors and Main L1 |
| Optical sensor/lens | Separate below | Ploopy consumer candidate; exact identity remains unqualified |

These are **catalogue subtotals, not delivered component quotes**, converted
at the ECB rate above. Priced component lines total approximately EUR 73.84.
The previous sensor/lens estimate is excluded after the failed Croatia/EU
checkout check. Stock is not reserved. See `package/one-set-purchasing.csv`
for original supplier currencies, exact MPNs, quantities and evidence.

Main L1 has now been replaced in CAD by Bourns SRP4020CC-3R3M, using the
recorded Mouser Croatia price of EUR 0.671 for one, included in the historical
priced-electronics subtotal of approximately **EUR 73.84**, before supplier
freight/tax. The generated checkpoint contains 62 priced MPN lines out of 63.
These are the earlier catalogue observations, not a refreshed checkout. CODICO
business-only offers remain excluded.

Ploopy now provides a consumer import candidate: one PMW3360 sensor/optic set
plus tracked shipping to Bjelovar 43000 totals approximately **EUR 29.26**,
before import VAT and handling. The cart quoted CAD 47.01, converted at
EUR 1 = CAD 1.6064 (ECB 2026-09-11). Exact sensor suffix/lens identity still
need confirmation, so this is separate from the qualified parts subtotal.

## Required costs still unverified

- Component shipping/import taxes from the suppliers above; Ploopy's Croatia
  shipping quote is recorded, but optical identity and import charges remain open.
- Fresh stock reservation and delivered quote for L1 and the other component lines.
- AWG28 ribbon and encoder wiring, AWG22 power pair and AWG24 coil pairs:
  exact consumer products, minimum purchases and delivered EUR prices pending.
  No internal connector, housing, contact or FFC purchases remain.
- GB1806 motor: an approximately EUR 10.87 listing has contradictory availability indicators;
  it is excluded from the confirmed subtotal.
- Magnets, coil wire, flexures, bearings/shaft as needed, removable fixture
  supports and fasteners, solder paste, flux, wick and cleaning consumables.

Tools are excluded as requested. No core feature was removed to meet the
target. The **complete delivered total and gap to EUR 400 remain unknown**.
The fixed-stack economy panel is the supported fabrication choice, subject
to CAM acceptance; buying it now would precede the unresolved supplier and
bench-fit checks. Public listing evidence and the separate cost categories
are recorded in `sourcing-observations.json` and `quote-observations.json`.

The connector removal reduces the earlier priced component subtotal by about
**EUR 8.07**, before replacement wire costs. This is a recalculation from saved
observations, not a new supplier checkout. Historical economy fabrication plus
recalculated electronics plus the recorded Ploopy delivery quote sum to
**EUR 327.65**. That is an incomplete planning subtotal, not a delivered project
quote: new fabrication pricing, component freight/tax, optical import charges,
wire, motor, magnets, coils, PETG, fasteners, adhesive and consumables remain open.
Do not treat the apparent EUR 72.35 remainder to the EUR 400 target as savings.
