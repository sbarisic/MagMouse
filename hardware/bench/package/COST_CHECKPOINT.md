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
The saved separate quotes are Main Y11, Wheel Y12 and Encoder Y13. The panel
is Y10 and the shared stencil is SO12609120215.

## One population of electronics

The generated purchasing list covers 291 populated references, grouped into
67 MPN/footprint lines. U32 is the only deliberately omitted functional IC.
Sixty-five lines retain usable public stock/quantity pricing observations:

| Supplier | Parts subtotal | Scope |
|---|---:|---|
| LCSC | EUR 45.19 | 54 lines; supplier multiples and inexpensive spares included |
| DigiKey | EUR 32.68 | 9 lines, including both ADCs, MA735 and three button drivers |
| Mouser | EUR 3.37 | 2 lines, including three Hall sensors |
| Optical sensor/lens | Unpriced | Yushakobo checkout excludes Croatia and all EU countries |

These are **catalogue subtotals, not delivered component quotes**, converted
at the ECB rate above. Priced component lines total approximately EUR 81.24.
The previous sensor/lens estimate is excluded after the failed Croatia/EU
checkout check. Stock is not reserved. See `package/one-set-purchasing.csv`
for original supplier currencies, exact MPNs, quantities and evidence.

The original Main L1, SWPA4020S3R3MT, remains unsourced at a sensible purchase
quantity. DigiKey lists a 3,000-piece minimum and manufacturer lead time;
Bourns SRP4020CC-3R3M is an available EUR 0.671 candidate from Mouser Croatia,
but requires a footprint/copper/stencil update before substitution. Do not
count L1 as free or as already qualified. CODICO lists a five-sensor/five-lens
kit for EUR 57 before VAT, but restricts sales to businesses and has not
confirmed the exact lens MPN. It is excluded because the user has no business.

Ploopy now provides a consumer import candidate: one PMW3360 sensor/optic set
plus tracked shipping to Bjelovar 43000 totals approximately **EUR 29.26**,
before import VAT and handling. The cart quoted CAD 47.01, converted at
EUR 1 = CAD 1.6064 (ECB 2026-09-11). Exact sensor suffix/lens identity still
need confirmation, so this is separate from the qualified parts subtotal.

## Required costs still unverified

- Component shipping/import taxes from the suppliers above; Ploopy's Croatia
  shipping quote is recorded, but optical identity and import charges remain open.
- L1 availability or a documented electrical/footprint-qualified substitute.
- Conforming 150 mm FFC: Würth compatibility/availability enquiry sent, reply pending.
- Power, encoder and button harnesses with qualified contacts and lengths.
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
