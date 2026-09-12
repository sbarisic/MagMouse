# Rev-A stencil and assembly review

2026-09-12. **0.10 mm — selected for Rev-A prototype.** Use one uniform,
unframed stainless-steel stencil with three identifiable board groups.
The current aperture geometry passes the prototype design screens. This is
an engineering selection, not measured paste transfer or manufacturer process
qualification. Paste selection, oven setup and practice reflow are assembly
tasks; they do not prevent ordering the bare boards.

`paste_variant.py` reproducibly applies the bench-only paste changes to copies
of the source boards and derived panel. Copper and individual-board routing
are not changed by this variant. U32 and the separately soldered optical part
have no paste. The fabrication ZIP does not contain the assembly paste layer;
use the separately identified stencil ZIP.

## Package dispositions

`package/package-review-register.csv` covers every populated SMT reference,
including its footprint and datasheet. `paste-shape-measurements.csv` measures
actual rounded-pad polygons at 0.001 mm approximation tolerance, area/perimeter
ratio at 0.10 mm and nominal wet-paste volume. `paste-land-coverage.csv` maps
paste to copper by intersection, including unnamed thermal apertures.
`stencil_policy.py` defines thickness, the 0.66 minimum area ratio and geometric
tolerances for both measurements and export acceptance. The encoder minimum
is approximately 0.7752 at 0.10 mm; it would become 0.6202 at 0.125 mm and fail
this screen. The threshold is a screening criterion, not measured print acceptance.

Measurements use actual polygon area/perimeter and nominal wet-paste volume.
J1 has four pairs of named contacts sharing physical lands; each is counted
once. Each eFuse has four compound openings formed from overlapping primitives;
those are measured as their exact union, preserving the existing outline.
All other overlaps are rejected. Copper coverage is reported separately per
land; no physical opening or deposited volume is counted twice.

| Package / references | Review disposition |
|---|---|
| Bourns L1 | Recommended 1.5 x 2.4 mm lands; full-size paste, rounded corners. Keep exact footprint identity. |
| TI DSG0008A: Main U2/U4/U5/U6 | Replace generic ~62% pattern with two 0.9 x 0.7 mm windows at +/-0.45 mm, R0.05; measured coverage ~87%. TI example uses 0.125 mm thickness. |
| TI DMR0004A: Main U7/U8/U9 | Replace generic ~61% centre paste with 0.76 x 0.57 mm, R0.05; ~90% coverage, matching TI's 0.10 mm example. |
| TI RTE0016C: Main U10 / Wheel U23 | Replace generic ~62% grid with the 1.55 mm square, R0.05 manufacturer example, ~85% coverage. TI example uses 0.125 mm. |
| TI RPW0010A: Main U12/U13 | Retain custom split-pad apertures; measured large pads 5/6 are ~82%, consistent with TI's 0.10 mm example. Small-pad coverage remains in the per-land table. |
| TI RGF0040E: Wheel U21 | Retain twelve windows, ~69% coverage. TI example uses 0.125 mm. Filled/capped thermal vias remain mandatory in this design. |
| ESP32-S3-MINI-1: Main U3 | Retain separate ground deposits and module pad geometry. Inspect centre-pad transfer and module seating in practice; one board reflow only. |
| MPS UTQFN14: Encoder U27 | Retain exact land pattern; datasheet lacks a complete stencil/reflow recipe. Obtain package process guidance and received-lot MSL; 260 C lead absolute maximum is not a reflow profile. |
| TUSB320 X2QFN / TPD2EUSB30 DRT | Fine-pitch perimeter release and bridges need practice-print inspection; generic ratio pass does not replace package process evidence. |
| Other SO/SOT logic, analog and MOSFETs | Retain perimeter apertures. Match actual MPN/finish and received packaging MSL/peak limits; inspect polarity and pin one. |
| J1 USB-C; SW1/SW2 | SMT pads remain in stencil; shell/through-hole joints are soldered separately as required. Exact supplier process limits remain open. |
| D5 OPSCO SK6805-EC15 | Retain polarity and apertures. Obtain the exact supplied revision's reflow/MSL requirements; do not use another SK68xx part's limits. |
| C90 Panasonic 16SVPC100M | Retain lands and polarity. Obtain the C6-case SVPC reflow conditions; the series electrical table alone does not establish the profile. |
| MLCC/resistor/TVS population | Retain apertures; avoid capacitor flexure and temperature shock. Use exact supplier package soldering guidance and received lot information. |

Geometry sources: [TPS62162 DSG](https://www.ti.com/lit/ds/symlink/tps62160.pdf),
[DRV8231A DSG](https://www.ti.com/lit/ds/symlink/drv8231a.pdf),
[TMAG5253 DMR](https://www.ti.com/lit/ds/symlink/tmag5253.pdf),
[ADS7038 RTE](https://www.ti.com/lit/ds/symlink/ads7038.pdf),
[TPS25947 RPW](https://www.ti.com/lit/ds/symlink/tps25947.pdf),
[DRV8316 RGF](https://www.ti.com/lit/ds/symlink/drv8316.pdf).

## Accepted prototype volume tradeoff

Retain the WSON, ADC and motor-driver patterns without enlarging their
already reviewed exposed-pad coverage. TI's 0.125 mm examples are reference
processes. At the selected 0.10 mm, the **same openings have 20% less nominal
wet-paste volume**: area x 0.10 / (area x 0.125) = 0.80. This is a deliberate
Rev-A process choice, not evidence that a joint is defective. Actual transfer,
flux loss and final joint/void geometry cannot be inferred from that ratio.

The thinner sheet maintains release margin on the encoder and retains the
Hall/eFuse examples based on 0.10 mm. No stepped stencil or blanket aperture
enlargement is required for this prototype. Keep the existing ESP32, LED and
C90 apertures; keep U32, optical and hand-soldered wire/anchor exclusions.

The stencil can now proceed to manufacturing review. Practice printing and
reflow on representative hidden-pad parts remain required before populating
the prototype; they are not prerequisites for ordering bare PCBs.

## Reflow envelope and outstanding process information

[Espressif](https://www.espressif.com/sites/default/files/documentation/esp32-s3-mini-1_mini-1u_datasheet_en.pdf)
specifies a single module reflow, 235-250 C peak and 60-90 s above 217 C with
SAC305; follow its complete profile. This caps the Main candidate peak at 250 C,
not the 260 C limits often listed for small ICs. Bourns permits 260 C peak,
60-150 s above 217 C, preheat 150-200 C for 60-120 s and ramp-up <=3 C/s;
its limits do not constrain that Main candidate further.

The nine internal connectors are removed. Their replacement plated wire holes
have no paste on either side and are soldered after reflow. No Hirose/JST
connector profile or stencil-volume requirement applies to this variant.
Panasonic links the exact 16SVPC100M to its
[soldering-condition and land-pattern table](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000COL10.pdf);
verify the applicable condition and complete time limits before programming
the Wheel profile. Its operating-temperature limit is not a soldering limit.

This is only a **partial intersection**, not an approved oven recipe. The exact
connector, LED, polymer capacitor, MPS and received-lot constraints listed above
must be intersected with the selected paste instructions. No profile is frozen
while any of those limits is unknown. Record moisture exposure and applicable
bake instructions before assembly. Wheel and Encoder can have separate measured
profiles because units are depanelled before reflow.

Keep the optical sensor/lens out of board reflow and inappropriate cleaning.
Practice with representative fine-pitch/hidden-pad parts, verify printed deposits,
measure temperature at both small ICs and large thermal masses, and investigate
bridging, insufficient paste or tilt before using the actual electronics.

## Completed design verification

The selected export contains 962 physical openings across 281 reflowed
references. The earlier count of 974 counted twelve shared/compound pad
primitives twice; no opening was deleted or resized. Minimum actual-polygon
area ratio is 0.775229, above the configured 0.66 threshold.

All 25 bench/panel/stencil regressions pass, including negative cases for
excluded paste, missing deposits, overlaps and incorrect full-shape panel
transforms, and the encoder at 0.125 mm. Copper, drill and component-coordinate
preservation is checked on all three units. Maintained boards and derived
Panel remain byte-identical to the pre-review snapshot. The emitted paste
Gerber differs from its pre-review version only in creation timestamps.

Visual review covered forty local copper/paste views (including all populated
ICs, C90, RGB and a wire-array exclusion) and the three-group overview. Source
hashes and the result are recorded in evidence/stencil-finalization.json;
the complete export is identified by file-sha256.json. CAM communications
remain drafts only. No printing, reflow or hardware performance is claimed.
