# Rev-A printable bench fixture

These are adjustable bench supports, not mouse-shell or final mechanism CAD.
Use `build_fixture.py` with build123d 0.11.1. The editable dimensions are in
`PARAMS`; an optional JSON `--config` overrides them. Run `python
mechanical/bench/build_fixture.py` to regenerate STEP, STL, assembly views and
validation. Print the dimensioned SVG at 100% and check its 100 mm scale.

Print PETG parts separately, with the broad flat face on the bed. Use a nozzle
and line width that can resolve the 0.3 mm saddle lip (for example a 0.25 mm
nozzle); do not assume a 0.4 mm extrusion reproduces that feature. Start with
0.2 mm layers and four perimeters; orient the lever on its side so the thin
flexure is not printed as an unsupported cantilever. Inspect the flexure and clamp sample before
printing the complete set. These are trial print settings, not a strength or
fatigue qualification. The largest pieces are 125 × 130 mm, below 180 × 180.

Build one fixture from four base tiles. Join the vertical seam with four
`tile_joiner_x` bridges centred at x=127.5 and grid y coordinates clear of
boards; join the horizontal seam with four rotated `tile_joiner_y` bridges
centred at y=130 and grid x coordinates. Confirm all chosen holes align before
tightening. Use M3 screws, washers and nuts. Keep the optical window unobstructed.

Use eight saddles/caps for Main and Wheel at the coordinates in
`generated/assembly-clearance.json`. M3 threaded rods, paired nuts and washers
set board height from 15 to 35 mm above the base top. Use nonconductive caps
with no more than 0.3 mm edge engagement. Verify copper/component clearance
against `package/support-clearances.csv`; never clamp a solder joint. The STEP
assembly includes board-outline envelopes and supports; it does not model all
real component heights. Measure underside parts and retain at least 5 mm free
below the lowest part or joint. Solder protrusions must remain below 1.5 mm.

The motor plate has general-purpose slots, a shaft clearance hole and an
optional measured bolt circle. `motor_bolt_circle=None` means no motor pattern
is claimed. Mount only the stationary motor structure. The upright carrier
supports a separately adjusted Encoder board using removable side clips; fit
clips to clear edge regions and leave the sensor face unobstructed. Verify
shaft/magnet alignment and gap after receiving parts. Do not run an unsecured
magnet. Lens retention width is likewise unset until the Ploopy lens is measured.

Print one lever/stop sample, then three after checking passive return and travel.
The magnet pocket's 5 mm diameter / 2 mm thickness defaults are editable trial
dimensions. Bond the magnet securely after polarity checks. Position the holder
over the unchanged Hall sensor, add shims and a hard stop that prevents contact,
then calibrate in software. The printed flexure requires fatigue and return-force
tests; it is not a production paddle. See `docs/button-calibration.md`.

Use a clamp at each end: two ribbon clamp pairs, two encoder clamp pairs and
eight compact pair clamps for power and coils. Shim the channel to grip insulation without
crushing it; the channel is deliberately adjustable for the selected wire.
Allow slack between clamp and board. Install wires after reflow and before
optical fitting. No clamps or new mounting holes are added to the PCBs.

Hardware purchasing starts with 150 M3 nuts, 150 washers, 100 M3×16/25 screws and
twelve 60 mm M3 threaded rods, plus any measured motor-adapter fasteners. These
are a provisional kit allowance, not an exact priced BOM. Wire, PETG, adhesive,
fastener and mechanism prices remain unquoted in EUR. Assembly tools are excluded.

Open physical checks: wire insulation/strand fit, encoder clip fit, lens stack
and retention, motor pattern, probe-barrel approach, actuator/coil attachment,
flexure performance, thermal behaviour and complete assembly interference.
CAD solid validity and board-envelope checks do not close these checks.
