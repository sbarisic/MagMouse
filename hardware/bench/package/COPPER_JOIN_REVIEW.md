# Complete element/contact review — current revision

Final result: 14 native/electrical acceptance checks, 62 bench/contact tests,
60 modular tests, and 47,426 exported contact checks PASS. Whole-copper
comparison covers 17,819 element/layer instances; no additional repair was required.

The latest review found **no additional copper repair required**. The three
marked Main U16 pad entries (6, 10, 13) already extend to pad centres in the
current source boards. Their screenshot showed earlier geometry. A dedicated
U16 regression and regenerated close-up now make this verifiable.

`contact_review.py` inventories every trace, pad and via on each copper layer,
including saved zone contacts. It distinguishes schematic NC pads, unused via
layers and unused layers of plated pads. An unclassified isolated element is a
failure; these classifications do not replace native DRC/parity/connectivity.
Each distinct zone-contact patch is checked locally, without another contact
elsewhere rescuing it. Routed joins retain the existing narrower-conductor
width minus 0.002 mm. Thermal entries use the actual configured spoke width.
Generic solid land-to-zone entries use the existing 0.15 mm zone feature rule,
limited by the land width; this is a geometry screen, not a power-current
rating. Existing strict power and return-path checks remain mandatory.

The Main ground trace near (57.05, 24.55) enters a thermally relieved pad;
it must retain that pad's intentional thermal geometry. Wheel U24.12 has a
pad-local filled island extending about 0.05 mm around the pad. The inventory
explicitly does not count this island as an external plane return; its via and
other-layer connection are checked independently. Neither detail requires
bridging a clearance or widening unrelated copper.

The exported-copper checker now compares **all source copper on all layers**
with the parsed Gerbers (0.0005 mm polygon/export tolerance), and repeats all
enumerated contact witnesses, in addition to the 2,457 historical repair
witnesses. Non-plated USB locating holes are excluded from the expected copper
model. Separate Excellon, plated-hole, via-fill and layer-transform checks
remain required. No source board, pad/via position, drill, route width, USB
geometry, component placement, board outline or stencil aperture was changed
in this pass.

The gallery displays each source hash and uses revision-qualified image links.
See `Main-U16-pad-via.png` for the reported examples. Current validation results
are in `package/evidence/acceptance.json`, `contact-inventory.json`,
`gerber-joins.json` and `full-contact-*.log`. The revised package is local only;
the submitted 2026-09-12 archive remains byte-for-byte unchanged.

## Previous repair pass (historical)

# Latest full-entry review

Final validation: 56 bench/panel/stencil/contact tests and 60 modular tests
pass, with 13 native/electrical/contact acceptance checks and 2,457 current
exported-Gerber width witnesses. Logs are in package/evidence/full-entry-*.log.

All layers on Main, Wheel and Encoder now pass the expanded contact audit.
It checks near-tangent trace caps (including up to 0.002 mm polygon gaps),
trace-to-pad/via entries, and direct pad/via contacts without a trace.
The required corridor is the narrower participating conductor minus 0.002 mm.
Where a narrower trace already supplies a local path between lands, its width
sets that path requirement; incidental overlap does not require widening it
to the whole pad diameter. Intentional zone thermal reliefs are preserved.

The Main B.Cu example is ENC_MOSI_LOCAL at (20.8,32.2) mm. Its 0.20 mm
rounded ends overlapped by about 1 nm. Polygon approximation made the contact
look disjoint, so the old intersection-only candidate search missed it. A
shared-centerline link now closes it at the original 0.20 mm width.

This pass repaired 303 Main contact observations (two observations share one
new bridge) and four Wheel via entries. Encoder needed no copper repair.
Original supply tracks retain their widths. Four added Main entries use the
existing narrower via-land diameter (0.45/0.60 mm) to preserve clearance;
no original power trace was narrowed. A later 0.60 mm entry bridges two
observations of the same PWR_5V via contact.

The Wheel F.Cu diamond was a redundant ADC2_MISO_LOCAL loop. Thirteen local
segments were removed, one incoming segment shortened, and one 0.15 mm link
added. The replacement runs through (36.8,8.45) -> (37.1,8.75) -> (34.15,11.7).
No pad/via was attached to the removed loop. Its two obsolete historical
Gerber witnesses are retained under superseded_loop_witnesses in the manifest.

All native DRC/unrouted/parity and 13 electrical/contact checks pass. The
negative tests now exercise the actual one-nanometre case, a one-micron gap,
a thin pad entry, land-only contact, and the removed Wheel loop. This extends
the earlier test coverage instead of treating connectivity as width acceptance.
Pad/via locations, drills, board outlines, USB segments and fixture geometry
were compared with the pre-pass boards and are unchanged. Manufacturing files
are regenerated locally; the submitted archive remains unchanged.

Close-ups: copper-images/Main-encoder-MOSI.png and Wheel-ADC2-MISO.png.
The following sections retain the previous review history and checkpoint counts.

---

# Copper joins and panel support — 2026-09-13

Working Rev-A bench revision; revised CAM package prepared locally, not submitted.
The exact 2026-09-12 submitted archive remains unchanged.

## Copper

Main has 2,105 repaired contacts and Wheel has 45. Encoder required no repair.
The audit covers straight-track contacts on every populated copper layer,
including ACT_5V, VBUS, GND and control routes. It checks the saved copper union,
not native connectivity alone. Original widths are retained. Pads, vias,
footprint positions and all 152 Main USB segments are unchanged.

Repairs connect track centerlines. Interior landings are split into explicit
vertices; three unused tails of at most 0.05 mm were removed. Two ACT_5V repairs on In2
use short local bends to preserve SPI_MOSI clearance. No arbitrary copper blobs
or thermal-relief changes were introduced.

A required-width corridor uses the narrower adjoining width minus 0.002 mm.
Where an existing corner supplies an alternative local path, erosion by half
that required width must leave both endpoints connected within a local window.
A long board-wide electrical connection cannot satisfy that local test.
All three final source audits have zero findings. The independent Gerber reader
applies dark/clear primitives in order and checks every repair corridor against
exported panel copper. See `evidence/gerber-joins.json` in the generated package.
`copper-join-repairs.json` records coordinates, widths, bends and source hashes.

## Tabs and fixture

Main's right tab is at local (80,68), panel (87,75) mm. Encoder's replacement
top tab is at local (53,50), panel (95,80) mm. The other eight tabs, 5 mm tab
width, perforations, unit outlines, panel dimensions and spacing are retained.
Each tab must intersect both its intended board and frame across its full
5 mm width; global panel connectivity cannot replace this check.
The Main right fixture saddle moves to fixture (105,88) mm. Printable solids,
assembly drawings and clearance evidence are regenerated.

## Verification and boundaries

Native DRC, unrouted and schematic parity are zero on all units; panel DRC is
zero. Existing strict electrical acceptance limits are unchanged. Regression
negatives cover thin/broken joins, wrong-net bridges, dangling/corner-only tabs
and narrowed tabs. Package source, layer, copper and drill transforms remain
checked by the existing panel tests. These are CAD checks, not hardware tests.

Reproduce: build_panel.py; export_fixture_interfaces.py; build_fixture.py;
verify_bench.py; export_bench.py; bench/modular unittest suites;
export_copper_images.ps1. The Gerber reader needs gerbonara installed under
build/gerber-python. Keep the submitted archive separate from regenerated files.

Validation logs: package/evidence/join-repair-*.log. The 47-test bench suite and
60-test modular suite pass; the final focused join suite passes all 10 tests,
including two added local-bend/distant-bypass cases. Final Gerber witnesses:
615 F.Cu, 601 In2.Cu and 934 B.Cu; no In1 repair was needed.

Visual inspection covered the pictured corner beside the OPT_RESET_N via near
Main (51.05,66.75), both replacement tabs and the revised fixture overview.
See the copper-images gallery for labelled close-ups.

## U6.6 via entry follow-up

The original track-to-track audit did not cover the narrow entry to the
BTN_R_COIL_P via at Main (64.9,45.05). A 0.30 mm track now connects the
existing endpoint (64.5,45.25) to the via center. The via and pad stay fixed.
A negative test reproduces the old thin overlap; a board regression checks
the full-width repaired entry. This adds one Gerber witness (2,151 total).
It does not claim a completed board-wide pad/via-entry audit.
