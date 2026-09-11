# MagMouse Rev-A bench prototype

**QUOTE AND REVIEW ONLY. Do not order from this directory yet.**

Purchasing is limited to private-consumer suppliers; the user has no business.
CODICO business-only offers are excluded. Distinguish EU-stock items from
imports with Croatia shipping; see SOURCING.md for current evidence.

This variant targets five bare panels, one populated Main/Wheel/Encoder set,
and one unframed stencil. Main and Wheel remain the maintained routed source
boards. Encoder now shares their four-layer construction. U32 is omitted only
from the bench purchasing and paste variant; its schematic and footprint remain.

## Review files

- `Panel.kicad_pro` / `Panel.kicad_pcb`: derived 151 x 139 mm, three-design panel.
- `panel-mechanical.svg`: printable outline and component-boundary review.
- `panel-manifest.json`: source hashes, board/reference mapping and translations.
- `package/Panel-Gerbers-QUOTE.zip`: copper, mask, silkscreen, routed edges and drills.
- `package/Stencil-QUOTE.zip`: top paste with U32 and hand-fitted parts excluded.
- `package/one-set-purchasing.csv`: exact MPN groups, references, quantities,
  minimum purchases, spares and public supplier observations.
- `package/all-vias.csv`: via-only fill/cap inventory. Never fill component holes,
  tooling holes or perforation holes.
- `BENCH_FIXTURE.md`, `bench-fixture.svg`: adjustable bench arrangement; no shell claim.
- `ASSEMBLY_AND_BRINGUP.md`: preparation, practice assembly and staged hardware tests.
- `SOURCING.md`, `WURTH_ENQUIRY.md`: supplier evidence and unresolved interfaces.
- `ORDER_READINESS.md`: remaining PCB work for a testable bench revision.
- `COST_CHECKPOINT.md`, `quote-observations.json`: live bare-board comparisons
  and the incomplete one-population cost estimate.
- `package/evidence/acceptance.json`: fresh native and strict electrical checks.
- `package/copper-review/`: exported copper and reference-plane views.

## Construction for both quotes

Order quantity five panels, **three different designs per panel**. Use FR4 TG155,
nominal 1.6 mm, four layers **JLC041611-2116**, 1 oz outer and 1 oz inner copper,
green mask, white silkscreen, ENIG 1 microinch and epoxy-filled/copper-capped vias.
The smallest vias are 0.20 mm drill / 0.45 mm pad; retain the source drill sizes.
The website's drill selection bucket does not authorize enlarging these holes.
Require CAM confirmation of the drill and fill specification.

The guaranteed variant requests 90 ohm differential USB, tolerance +/-10%.
The economy variant omits paid impedance control/testing only. Both retain
F.Cu width 0.1466 mm, gap 0.1501 mm and In1 ground reference. Do not accept a
stack substitution without a fresh impedance and return-path review.

All functional copper belongs to an individual board. No electrical connection
crosses a tab. The panel uses 2 mm separation clearance, ten 5 mm tabs with
five 0.6 mm perforations each, 0.9 mm pitch and 0.3 mm webs. Cut while supported
and **before population**. Do not bend populated boards to depanel them.

Stencil quote: one 220 x 200 mm unframed stainless sheet, 0.10 mm thick,
three identifiable TOP aperture groups. Preserve each board's paste geometry
1:1, including existing exposed-pad windows. JLC's multi-board option requires
permission to rearrange groups: approve the final CAM group positions before
building the alignment jig. A reordered stencil requires a regenerated jig.

## Reproduce and verify

Run with KiCad 10.0.6 Python, Shapely 2.1.2 and NumPy 2.4.6. The builder searches
`build/bench-python` for the latter libraries; dependencies are not vendored.

```powershell
& '<KiCad>/bin/python.exe' hardware/bench/build_panel.py
& '<KiCad>/bin/python.exe' hardware/bench/verify_bench.py
& '<KiCad>/bin/python.exe' hardware/bench/export_bench.py
& '<KiCad>/bin/python.exe' -m unittest discover -s hardware/bench -p 'test_*.py'
```

Two native panel builds were byte-identical. Export ZIP hashes change with KiCad
timestamps; the package hashes identify each exported snapshot. Copper/pad/via
and saved ground-fill transforms are checked against the individual source
boards. Source modification requires rebuilding and rerunning checks.

## Gates still open

Start with the L1 replacement and interface checks in ORDER_READINESS.md.
Ploopy is the user's selected optical supplier; exact lens/part confirmation
remains open. Final ergonomic shell development is not a bench-order gate.

1. Supplier-confirmed FFC dimensions and delivered price. The authorized Würth
   enquiry was submitted successfully; a reply is pending.
2. Complete delivered parts/harness/mechanism/consumables pricing. Catalogue
   stock is not a reserved order; missing lines are not zero-cost parts.
3. Received lens/motor dimensions and practical bench fixture fit. Final shell,
   paddle geometry, optical retention and ergonomic wheel support remain open.
4. Package-by-package paste-volume/profile review, stencil CAM confirmation,
   practice reflow and inspection of hidden joints. Aperture ratio screening
   alone does not close this gate.
5. Fabricator acceptance of tab support, routability, minimum vias and selective
   fill/cap instructions. Zero native DRC is not manufacturing approval.
6. Complete delivered project total. The identical-stack separate-board
   comparison is complete and favors the panel. Never treat a partial subtotal
   as the €400 target.

CAD connectivity, DRC and regression results do not establish USB operation,
motor/brake behavior, analog noise, thermal performance or assembly yield.
