# Two-set prototype quote

**Historical price:** the [corrected fabrication quote](CORRECTED_QUOTE.md)
supersedes this price with USD 774.51 delivered (approximately EUR 665.85)
for the same priced population. The original observed quote is retained below.

JLCPCB's live checkout on 2026-09-11 prices **two assembled sets without the
optional IMU at USD 859.98 delivered by DHL DDP**, approximately **EUR 739.32**.
That is EUR 281.44 / 27.57% less total spending than the original five-set
quote, but approximately EUR 369.66 per assembled set rather than EUR 204.15.
Fewer units reduce the cash outlay while fixed costs raise the cost per set.
The requested 50% reduction has not been reached.

Five bare PCBs are fabricated for each design, with two assembled and three
bare spares of each design. These are three separate jobs, **not a breakaway
three-board panel**. The original five-set cart jobs remain unchanged. The
new quotes are saved as Main Y7, Wheel Y5 and Encoder Y6. No order or payment
was submitted; checkout stops at the shipping-method stage.

| Job | PCB fabrication, five boards | PCBA including components, two boards | Quote-page total |
| --- | ---: | ---: | ---: |
| Main, U32 IMU omitted | EUR 152.24 | EUR 175.06 | EUR 327.29 |
| Wheel | EUR 98.68 | EUR 103.29 | EUR 201.97 |
| Encoder | EUR 17.62 | EUR 12.35 | EUR 29.98 |

The cart's authoritative merchandise total is **EUR 559.25**; rounded line
items differ by a cent. Main was also priced with the IMU before deselecting
U32: EUR 364.90, giving a three-job quote-page sum of EUR 596.85 before
shipping/tax. The IMU omission saves about EUR 37.60 at this quantity.
The full-IMU version did not receive a separate delivered checkout quote.

| Selected DHL DDP checkout | USD |
| --- | ---: |
| Merchandise | 650.52 |
| Shipping | 30.89 |
| Customs duties and taxes | 178.57 |
| **Delivered total** | **859.98** |

EUR comparisons use this cart's merchandise ratio, EUR 559.25 / USD 650.52.
Checkout is in USD; these are approximate EUR equivalents, not a guaranteed
payment-currency amount. No coupons were applied. The quote uses the already
authorized saved address for Croatia 43000; personal contact data is not
included in these files.

## Population and specification checks

The original validated Gerber/BOM/CPL files were uploaded independently for
all three designs. Main was first matched with 205 priced references; J2,
J3, J4, SW1 and SW2 were restored after the matching UI initially unchecked
them. U32 was then deliberately unchecked in this quote, leaving 204 priced
references. Wheel prices 81 references and Encoder two. No substitute parts
were selected. CAD and the original BOM/CPL files remain unchanged.

These are **partial-population electronics quotes**. R25 (C23259), U31
(C139302) and MA735 U27 (C17233427) still have stock shortages. PMW3360 is
separately sourced/installed. Lens, cables, motor, coils, magnets, bearings,
wheel and shell are excluded. An Encoder with only its connector and bypass
capacitor populated is not a functional encoder. Firmware must tolerate the
deliberately absent IMU until one is fitted.

Main and Wheel retain the selected four-layer JLC041611-2116 stack, 1 oz
inner/outer copper, ENIG, filled/capped vias and 0.20 mm drill tier. Main
retains controlled impedance for the selected 90-ohm USB geometry. Encoder
remains two-layer. Main/Wheel use Standard assembly; Encoder uses Economic.
Wheel's fabrication line is EUR 0.90 below the baseline because this draft
lacks the baseline production-file-confirmation fee. That small difference
is not a quantity saving, and this quote is not permission to manufacture
without review. Production-file confirmation is still required at release.

## Recommended next work

First reconcile the premium via option with JLCPCB's published diameter-based
pricing rule; see the [fabrication review correction](FABRICATION_REVIEW.md).
The existing 0.20 mm holes have 0.45 mm pads and may qualify without that
premium option. No corrected live price is recorded yet.

Keep this as the lower-cash-outlay prototype option. The
[fabrication review](FABRICATION_REVIEW.md) found that blanket via enlargement
or simply dropping fill/cap is incompatible with current routing. Do not
commit to a broad six-layer or larger-via redesign for modest calculator
savings before the mechanical interfaces are defined.

Develop the baseplate, mounts, wheel/encoder supports, lens stack and cable
envelopes next. Once those are stable, migrate the encoder to the selected
common stack and quote a properly designed breakaway panel against these
separate jobs. Keep panel savings unclaimed until the supplier prices the
actual panel, combined BOM/CPL and different-design handling.

[Machine-readable prices and job IDs](two-set-live-quote.json) accompany the
read-only audit. Source hashes were verified against the exported snapshot;
no CAD edit, new electrical acceptance or production release is implied.
