# JLCPCB quote packages

**Latest comparison:** the [corrected fabrication quote](cost-reduction-2026-09-11/CORRECTED_QUOTE.md)
is **USD 774.51 DHL DDP delivered, approximately EUR 665.85 for two assembled
sets**, without the optional IMU. Five PCBs per design are fabricated and two
assembled. This removes an unnecessary small-via pricing tier while retaining
the actual CAD, fill/cap and Main USB impedance specification. The price is
about EUR 73.47 below the earlier two-set quote. Stock/optical/mechanical
exclusions remain; no order was submitted. Main/Wheel consolidation has a
[placement assessment](cost-reduction-2026-09-11/COMBINED_BOARD_ASSESSMENT.md),
not a finished combined layout or supplier quote. Earlier observations follow.

The [2026-09-11 snapshot](2026-09-11/validation.json) exports the current routed
Main, Wheel and Encoder boards from CAD commit `743d7f1`. It is **for pricing
only**, not a fabrication or assembly release. The boards and schematics are
unchanged. All three Gerber/BOM/CPL jobs have been uploaded and priced in the
signed-in JLCPCB workflow. With the user-provided shipping address for Croatia
43000, checkout quotes **USD 1,187.35 delivered by DHL DDP for five sets**:
USD 907.11 merchandise + USD 36.20 shipping + USD 244.04 customs duties/taxes.
This is **USD 237.47 per set**, approximately **EUR 1,021 total / EUR 204 per set**.
The EUR conversion uses the same cart's EUR 779.84 / USD 907.11 merchandise
values; checkout itself displays USD, so this is not a guaranteed EUR payment
amount. **The stock and optical/mechanical exclusions below still apply.**
No order or payment was submitted; the payment step was not entered.
See the [itemized live quote](jlcpcb-live-2026-09-11.json).

The [cost-reduction study](cost-reduction-2026-09-11/README.md) contains an
independent Main quote with U32 omitted, at EUR 411.26 for five boards, and
six-layer manufacturing comparisons. The original CAD and baseline cart are
unchanged. The measured changes suggest about 19% delivered savings for the
half-ounce six-layer/no-IMU case, subject to redesign and a fresh checkout;
they do not establish the requested 50% reduction.

The later [two-set quote](cost-reduction-2026-09-11/TWO_SET_QUOTE.md) is
**USD 859.98 DHL DDP delivered, approximately EUR 739.32**, with U32 IMU omitted.
It fabricates five of each design and assembles two, leaving three bare spares
per design. This reduces total spending by about 28%, while increasing the
cost per assembled set. It retains the stock/optical/mechanical exclusions.
The new three cart jobs are separate from the preserved five-set baseline;
neither is a breakaway panel. No order or payment has been submitted.

| Five-board job | PCB | Components | PCBA including components | Quote-page total |
| --- | ---: | ---: | ---: | ---: |
| Main | EUR 152.24 | EUR 233.19 | EUR 351.06 | EUR 503.29 |
| Wheel | EUR 99.58 | EUR 77.18 | EUR 145.99 | EUR 245.57 |
| Encoder | EUR 17.62 | EUR 1.50 | EUR 13.35 | EUR 30.97 |

The PCBA column includes the components column; do not add them again. The cart
rounds individual PCB/PCBA lines separately and is EUR 0.01 above the sum of
the three quote-page totals. Component purchases total EUR 311.87, including
the supplier's attrition quantities. Main/Wheel use Standard PCBA; Encoder
uses Economic PCBA and remains two-layer.

**Stock exclusions:** Main R25 / C23259 (887k resistor), Wheel U31 / C139302
(LM4040AIM3-2.5/NOPB), and Encoder U27 / C17233427 (MA735GGU-P). Exact-MPN
encoder search also found zero public and idle stock. No substitutes were
selected. The priced population is 205 Main + 81 Wheel + 2 Encoder references
per set, rather than the requested 291. Main J2/J3/J4 and SW1/SW2 were initially
unchecked by matching and were explicitly included before pricing.

These are partial-population quotes, not functional complete sets. The optical
sensor and mechanical/cable exclusions below also remain. The earlier
country-level shipping estimate of EUR 23.09 gave EUR 802.93 before tax.
The later address-specific DDP quote above supersedes that delivered-cost
estimate. The user authorized entering the address and phone for this quote.
Those personal details are not stored in repository artifacts. Supplier
placement rotation, small-board handling and manufacturing review are not
approved by obtaining this price.

Quote five of each design (five complete electronic sets) for Croatia, 43000.
Upload each row as a separate job, using its matching Gerber archive, BOM and
CPL. Supply the [manufacturing notes](2026-09-11/MANUFACTURING_NOTES.md) and each
board's via map/inventory with the quote request.

| Job | Gerbers/drills | BOM | CPL | Quoted components per board |
| --- | --- | --- | --- | ---: |
| Main | [ZIP](2026-09-11/Main/Main-Gerbers-QUOTE.zip) | [BOM](2026-09-11/Main/Main-BOM-QUOTE.csv) | [CPL](2026-09-11/Main/Main-CPL-QUOTE.csv) | 206 |
| Wheel | [ZIP](2026-09-11/Wheel/Wheel-Gerbers-QUOTE.zip) | [BOM](2026-09-11/Wheel/Wheel-BOM-QUOTE.csv) | [CPL](2026-09-11/Wheel/Wheel-CPL-QUOTE.csv) | 82 |
| Encoder | [ZIP](2026-09-11/Encoder/Encoder-Gerbers-QUOTE.zip) | [BOM](2026-09-11/Encoder/Encoder-BOM-QUOTE.csv) | [CPL](2026-09-11/Encoder/Encoder-CPL-QUOTE.csv) | 3 |

These files request **291 placements per set, 1,455 across five sets**. Main U35
PMW3360 is separately sourced/installed and is excluded from both assembly input
files. Its existing catalog ID and status remain in Main's procurement list.
The 44 copper-only test points are excluded explicitly. Lens, motor, coils,
cables, magnets, bearings, wheel and shell need separate cost lines.

## Validation

All **336 schematic/PCB references** are accounted for: 291 assembly components,
44 copper test points and one separately installed sensor. BOM and CPL have
identical population sets and no duplicates. Component values, footprints,
DNP/exclusion flags, connected pin/net assignments, native placement positions,
rotations and board sides are checked against current CAD.

Fresh native DRC/parity and connectivity checks pass on all three boards:
zero physical violations, parity issues and unrouted connections. All required
copper, mask, paste, silkscreen, outline and separate PTH/NPTH drill files were
generated. Every exported via drill hit matches CAD diameter/position, allowing
0.000501 mm for the 1 µm Excellon coordinate precision. Gerbers use 4.6 metric
coordinates; all manufacturing files share the absolute origin.

| Board | CAD vias | Vias whose drill overlaps an SMD pad | Quote treatment |
| --- | ---: | ---: | --- |
| Main | 875 | 102 | Fill/cap all 875 actual vias |
| Wheel | 196 | 36 | Fill/cap all 196 actual vias |
| Encoder | 17 | 0 | Ordinary tented vias |

Component holes and USB shell slots must remain open. The overlap list includes
partial drill/pad intersections; it is broader than a list of vias centred in
exposed pads. [Main map](2026-09-11/Main/via-map.svg),
[Wheel map](2026-09-11/Wheel/via-map.svg) and exact per-board CSV coordinates
identify the locations. Main/Wheel use the selected four-layer JLC041611-2116
stack; Main requests the existing 90 Ω USB geometry. Encoder stays two-layer.

Eight exporter fault-injection tests pass, including missing/duplicate references,
wrong quantities, mirrored coordinates and an off-centre drill/pad overlap.
Native assembly and via-map SVGs were visually inspected. Source hashes were
checked unchanged after export; each snapshot contains output checksums and
fresh netlist/DRC/position/drill evidence. This validates the pricing inputs;
it does not establish stock, JLC rotation conventions, mechanical fit or production
process acceptance. The existing 59 routing tests were not rerun because no CAD
or routing code changed.

## Generate a new snapshot

Use KiCad 10's Python interpreter and a **new** output directory:

```powershell
& 'C:/Users/cartm/AppData/Local/Programs/KiCad/10.0/bin/python.exe' hardware/quotes/export_quote_packages.py --output build/new-pcba-quote
& 'C:/Users/cartm/AppData/Local/Programs/KiCad/10.0/bin/python.exe' -m unittest discover -s hardware/quotes -p 'test_quote_exports.py'
```

The exporter does not overwrite existing snapshots or save/refill CAD sources.
It aborts on coverage/DRC/parity/source-change failures and leaves an
`INCOMPLETE_DO_NOT_UPLOAD.txt` marker. Do not use incomplete output. Read
`validation.json` and verify the current source hashes before reusing an older
snapshot. The generated CSVs are CAD machine inputs, not a cost spreadsheet.

## Next pricing and release steps

Resolve the three stock shortages and optical sourcing, then reprice with full
population. Inspect supplier placement rotations and confirm via processing,
stackup, 90 Ω tolerance/testing, connector soldering and assembler handling
panels. Reprice final production files and population before payment. The earlier
$179.47 bare-panel estimate is a different scope.

Final production panel work remains after mechanical freeze, PCB adjustments,
whole-board review, encoder stack migration and manufacturing closure.
