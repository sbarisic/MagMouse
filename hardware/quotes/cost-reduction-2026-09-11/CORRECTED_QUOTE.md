# Corrected fabrication quote

JLCPCB checkout on 2026-09-11 quotes **USD 774.51 delivered by DHL Express
DDP to Croatia 43000**, approximately **EUR 665.85 for two assembled sets**
or **EUR 332.92 per set**. It fabricates five Main, five Wheel and five Encoder
PCBs and assembles two of each, leaving three bare spares per design.
These remain three separate designs, not a combined board or breakaway panel.
No order or payment was submitted.

| Job | Fabrication, five PCBs | Assembly including components, two PCBs | Quote-page total |
| --- | ---: | ---: | ---: |
| Main, optional U32 IMU omitted | EUR 122.18 | EUR 175.06 | EUR 297.24 |
| Wheel | EUR 70.55 | EUR 103.29 | EUR 173.84 |
| Encoder, existing quote | EUR 17.62 | EUR 12.35 | EUR 29.98 in cart |

The cart merchandise total is **EUR 501.06 / USD 582.83**. Checkout adds
USD 30.21 shipping and USD 161.47 customs duties/taxes. EUR delivery figures
use the same cart's merchandise conversion ratio; checkout itself displays
USD. Rounded item sums can differ from the cart by one cent.

This saves approximately **EUR 73.47 / 9.94%** against the earlier EUR 739.32
two-set delivered quote, with the same priced population. Relative to the
original EUR 1,020.76 five-set quote, spending falls about 34.8%, but that
comparison also reduces assembled quantity and omits the optional IMU.
The requested 50% reduction has not been reached.

## What changed

The earlier small-via pricing option was unnecessarily restrictive. JLC's
[via capability rules](https://jlcpcb.com/capabilities/pcb-capabilities) and
the calculator help allow 0.20 mm holes without the extra small-via charge
when multilayer via pads are at least 0.45 mm. The current boards meet that
geometry. New Main/Wheel quote jobs use the standard fee tier and explicitly
state the actual drill/pad sizes in their PCB remarks. No CAD or drill sizes
were changed. The calculator also removed its associated Kelvin-test fee;
flying-probe electrical testing remains selected.

The quote retains four layers, JLC041611-2116, nominal 1.6 mm thickness,
1 oz inner/outer copper, TG155, ENIG, filled/capped vias and Main's 90-ohm USB
impedance requirement. Production-file confirmation is included for both
new jobs. This online price does not replace production engineering review.

The new saved cart jobs are Main Y9 / SMT026091163758 and Wheel Y8 /
SMT026091163753, with existing Encoder Y6 / SMT026091163656. Earlier cart
jobs were preserved. See the [machine-readable quote](corrected-via-live-quote.json)
for exact identifiers, settings and checkout evidence.

## Remaining cost and placement work

The [combined-board assessment](COMBINED_BOARD_ASSESSMENT.md) finds no empty
Main-board rectangle large enough for the intact Wheel component group.
A combined Main/Wheel board therefore needs new placement and rerouting.
Keep the upright Encoder separate. Consolidation could remove Wheel's
EUR 70.55 fabrication job, EUR 29.03 setup/stencil and some duplicated feeder
charges, but a final combined BOM and layout are needed to obtain that price.
Those savings must not be treated as an already-quoted combined board.

**Population exclusions:** Main R25, Wheel U31 and Encoder MA735 U27 remain
unavailable. U32 IMU is deliberately omitted from this quote variant only.
PMW3360 sourcing/installation, lens, cables, motor, coils, magnets, bearings,
wheel and shell are excluded. This prices partially populated electronics,
not complete working mice. CAD and the existing routed-board validation
remain unchanged; obtaining a quote does not establish mechanical fit.
