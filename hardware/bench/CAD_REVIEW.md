# Bench panel review evidence

Review snapshot: 2026-09-12, KiCad 10.0.6. **Pending supplier/CAM approval.**

Main L1 now uses the reviewed Bourns pattern and local routing described in
L1_REVIEW.md. Main/Wheel/Encoder now have soldered-wire arrays with local routing repairs. The derived panel
has been rebuilt from the individual boards.

`package/evidence/acceptance.json` records exact source/panel hashes and native
DRC/connectivity/parity plus strict Main analog, routing, USB/ESD, power,
interlocks and Wheel electrical checks. The modular and bench regression logs
include negative checks for wrong L1 lands and underprinted Hall paste.
Read the generated records for current results, not a historical count.

`package/panel-validation.json` checks transformed source pads, track/via
objects, saved fill vertices, independent net namespaces and tab clearance.
`all-vias.csv` contains only vias; component, mechanical and tab holes are
excluded from filling. The exact stack and USB geometry are unchanged.

The population contract retains 282 component references (281 SMT plus the
hand-fitted optical sensor), excludes nine connector purchases and retains all
86 bare wire lands. U32 remains the only omitted functional IC. `detail-review.json` and paste tables record actual polygon screening,
thermal-land coverage and source hashes. Unit paste is compared against every
translated panel aperture during export. U32 and optical paste remain absent.
Manufacturer geometry is separate from transfer efficiency and reflow approval.

Close-scale copper review covers the changed buck, button/ADC area, wheel/brake
and optical area; full copper/paste/panel views and connector pin views accompany
the package. Support-strip and probe-envelope screens are recorded separately.
The C90/TP34 obstruction has a documented accessible connector alternative.

Visual inspection covered the panel/slot overview, saved In1 plane, full stencil,
adjustable fixture, buck/button/ADC/wheel/optical copper and local paste overlays
for U2, U7, U10, U12, J8, U21 and U27. The overlays show red deposits on grey
copper. Overlapping constituent RPW pad shapes merge in the Gerber; aperture
records count source pad objects, not necessarily distinct laser-cut openings.
Wire migration also changes termination copper, removes connector paste and
adds local return stitching. Read current source hashes and regenerated images.

Open findings are in ORDER_READINESS.md and STENCIL_REVIEW.md. No saved check
establishes USB operation, ADC noise, motor/brake performance, thermal limits,
assembly yield, actual fixture fit or external CAM approval.

The Main wheel-power termination moved to (71,42) mm to keep its feed short.
The resistance screen is below the unchanged 50 mΩ ceiling. Its 1.1 mm plated
wire hole replaces the former SMT pad plus three 0.3 mm transition vias; barrel
circumference is greater at the same plating thickness. Copper resistance is
not a hardware ampacity or temperature qualification. All limits remain in
the electrical checkers. USB width/gap and Hall/optical coordinates are retained.
