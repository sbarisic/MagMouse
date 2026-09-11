# Cost-reduction quote study

**Latest result:** [corrected Main/Wheel fabrication pricing](CORRECTED_QUOTE.md)
brings two assembled sets to approximately **EUR 665.85 DHL DDP delivered**,
without CAD changes. See also the [combined-board placement assessment](COMBINED_BOARD_ASSESSMENT.md).
The historical six-layer estimates below used the earlier small-via fee tier
and must not be compared with the corrected four-layer quote as equal-specification
savings. Reprice their via settings before considering a stack change.

Quote-only alternatives to the five-set baseline in
[the live quote](../jlcpcb-live-2026-09-11.json). No CAD, panel or production
release changes are made by this study. Prices were read from JLCPCB on
2026-09-11. Baseline delivery is approximately EUR 1,020.76, using the same-cart
currency conversion documented there. The 50% target is EUR 510.38 delivered.

## Population variant

The Main BOM/CPL files in this folder omit **only U32, ICM-42688-P**. All other
fields and placements match the baseline CSVs. Both files contain the same
205 requested references, without duplicates. Independent CSV comparison
confirms every surviving field is unchanged. Use the original Main Gerber ZIP.
The original BOM/CPL and schematic still include U32.

The IMU supports supplementary lift/orientation experiments; PMW3360 remains
the cursor sensor. Firmware must tolerate an absent IMU. The variant leaves
IMU support passives populated. It does not substitute a different sensor.
The baseline R25 stock shortage remains separate from this deliberate omission.

JLC priced the independent [no-IMU draft](https://cart.jlcpcb.com/smt-order/?pcbFileNo=c697b7b2bc104c47b2c85b15c37c49b3)
at **EUR 411.26 for five Main boards**, versus EUR 503.29 on the original quote
page. PCB fabrication remains EUR 152.24; PCBA drops from EUR 351.06 to
EUR 259.03. The new component charge is EUR 149.62, feeders EUR 67.08,
SMT EUR 5.81 and X-ray EUR 7.05. Other assembly charges are unchanged.
The observed saving is EUR 92.03, including a small component repricing delta.
The original cart remains unchanged; the new draft was not added to it.

The later [two-set comparison](TWO_SET_QUOTE.md) adds three independent jobs
to the cart while preserving the original five-set jobs. Its Main variant
also omits only U32. The [read-only fabrication review](FABRICATION_REVIEW.md)
screens larger vias against the actual routed boards. Filled/capped vias remain
necessary in this quote; the later calculator verification established that
the premium small-via fee can be removed without enlarging the existing holes.
All 204 available references were selected, including J2/J3/J4 and SW1/SW2,
which matching initially left unchecked. See [the recorded quote](no-imu-live-quote.json).

## Combined cost comparison

Only the baseline is an address-specific delivered quote. The alternatives
below use measured quote/calculator deltas, hold shipping and other board
assembly charges fixed, and apply the baseline effective duties/tax ratio.
They are estimates until repriced through checkout; six-layer PCBA eligibility
has not been verified with revised production files.

| Five-set case | Merchandise EUR | Estimated delivered EUR | Reduction |
| --- | ---: | ---: | ---: |
| Baseline, actual checkout converted to EUR | 779.84 | 1,020.76 | — |
| U32 omitted; current boards | 687.81 | 904.92 | 11.3% |
| U32 omitted + half-ounce six-layer Main/Wheel | 622.30 | 822.47 | 19.4% |
| Above + 0.30 mm minimum drills | 592.36 | 784.78 | 23.1% |

The 50% goal is **not achieved**. On the same shipping/tax assumptions,
merchandise must fall to about EUR 374.36. Even the larger-drill redesign case
is EUR 218 above that threshold before delivery costs. Do not migrate the
working layout solely on an assumption that six layers halve the order price.

## Manufacturing calculator observations

These six-layer figures are **bare-board calculator estimates without uploaded
six-layer Gerbers**, not accepted PCBA jobs. Each price is for five boards.
Dimensions include the baseline Standard-assembly handling allowance. Encoder
is held unchanged and is not included in this table.

| Specification | Main 90 x 125 mm | Wheel 71 x 70 mm |
| --- | ---: | ---: |
| Current four-layer JLC041611-2116, 1 oz inner | EUR 152.24 | EUR 99.58 |
| Six-layer JLC061611-2116, 1 oz inner | EUR 155.33 | Not measured |
| Six-layer JLC06161H-3313, 0.5 oz inner | EUR 112.19 | EUR 74.12 |
| Same half-ounce six-layer stack, 0.30 mm minimum drill | EUR 96.89 | EUR 59.48 |

All measured six-layer rows retain green mask, white silk, 1 oz outer copper,
ENIG 1 microinch, epoxy filled/capped vias and production-file confirmation.
Main includes controlled impedance +/-10%; Wheel has no impedance requirement.
The first two six-layer cases keep 0.20 mm minimum drills. The 0.30 mm case
requires via/pad/routing redesign and is not compatible with the current files.
The selected material is FR4 TG155 and the calculator retains the Kelvin test.
No coupons, assembly savings, shipping or tax are included in these figures.

JLC061611-2116 is marked as a special stack, unavailable for Economic assembly.
JLC06161H-3313 has a displayed actual thickness of 1.5384 mm +/-10% rather than
nominal 1.6 mm. It has 0.0994 mm outer prepreg and 0.0152 mm inner copper.
Any migration needs explicit layer mapping, revised 90-ohm USB geometry,
reference-plane checks, power-resistance/thermal revalidation and mechanical
thickness review. Do not select a different stack against existing Gerbers.

The half-ounce six-layer pair saves EUR 65.51 in fabrication. The larger-drill
version saves EUR 95.45, but entails additional routing changes. Merely adding
layers while preserving 1 oz inner copper does not save money on Main.

JLC's [six-layer page](https://jlcpcb.com/resources/6-layer-pcbs) advertises free
ENIG and low starting prices. The live calculator for these options actually
charged ENIG, material, small-drill and Kelvin-test fees. Switching Main to
2 microinch ENIG increased its half-ounce estimate from EUR 112.19 to
EUR 127.10. This study uses the observed totals, not the advertisement.

## Component audit

These are extended component purchase prices in the saved JLC cart, including
supplier attrition where applicable, for five sets. They exclude feeder fees.

| Board / refs | Part | EUR for five sets |
| --- | --- | ---: |
| Main U32 | ICM-42688-P | 83.5848 |
| Main U10 | ADS7038IRTER | 30.0474 |
| Wheel U23 | ADS7038IRTER | 30.0474 |
| Main U3 | ESP32-S3-MINI-1-N8 | 20.0925 |
| Wheel U21 | DRV8316RRGFR | 19.5401 |
| Main U4/U5/U6 | DRV8231ADSGR | 14.3669 |
| Main U7/U8/U9 | TMAG5253BA2IQDMRR | 7.9488 |
| Main U12/U13 | TPS259470LRPWR | 7.8585 |
| Main U15 | SN74LVC1G123DCUR | 7.0263 |
| Main U25/U29/U37 | SN74LVC125APWR | 5.3903 |
| Main U16/U17/U18 | SN74LVC08APWR | 5.1486 |
| Main J2/J3/J4 | B2B-PH-SM4-TBT(LF)(SN) | 5.0344 |
| Main U2 | TPS62162DSGR | 4.7473 |
| Main U11 | TUSB320LAIRWBR | 4.6003 |
| Wheel U30 | TLV1811DBVR | 4.4954 |
| Main J8 + Wheel J9 | FH12-30S-0.5SH(55), combined | 7.3968 |

The IMU is the clearest optional cost reduction. ADCs and actuator drivers are
central to the current architecture. Removing them is not an equivalent BOM
optimization. Exact manufacturer/MPN alternatives need electrical, footprint,
firmware and JLC-stock validation before substitution. Catalog stock or a
similar part name alone does not establish assembly availability.

## Remaining route to a 50% saving

The baseline contains EUR 311.87 components, EUR 269.44 fabrication and
EUR 198.53 assembly/overheads. Only EUR 8.52 is actual SMT soldering. Reducing
placement count alone has little impact; recurring setup/feeder charges matter.

Economic assembly must be compared with the actual BOM. Its lower setup fee
is offset by higher extended-part fees; Basic parts have different feeder
treatment. Do not assume it is universally cheaper. See JLC's
[assembly fee table](https://jlcpcb.com/help/article/pcb-assembly-price).

Further candidates are a standard-stack four-layer redesign with fewer special
processes, validated cheaper sourcing for the optional IMU, and consolidation
of setup/feeder operations after mechanical freeze. Keep via filling where
required by SMD overlap. Panelization remains postponed until interfaces are
stable, and a mixed-design panel is not priced as one repeated design.

All comparisons retain the baseline missing R25, U31 and MA735 parts and exclude
PMW3360 installation, lens, cables, motor, coils, magnets, bearings and shell.
They must not be described as complete working mice or final order prices.
