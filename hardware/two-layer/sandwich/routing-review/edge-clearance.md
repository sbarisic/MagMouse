# Copper-to-edge clearance revision — 2026-11-06

The integrated-encoder revision removes the Encoder board and bottom test pads.
See [current encoder design](../ENCODER_INTEGRATION.md) and
[current acceptance checks](../encoder-review.json). Earlier measurements below
describe their recorded source revisions.

All four active boards and the derived panel use a 0.5 mm minimum copper
clearance to outer board edges. Lower's internal optical aperture retains
0.4 mm clearance, as explicitly approved. A custom rule identifies only the
edges in the `Optical aperture` group; the panel preserves that exception.

Lower's affected signal routes were moved inward and locally rerouted without
reducing trace widths. MCU_EN uses two additional 0.30 mm vias to bypass an
obstructed edge corridor. Encoder's left-side GND trace was moved inward;
its signal copper is unchanged. Both GND layers were refilled on all boards.

Validation:

- Fresh ERC, DRC and schematic parity checks: zero findings on all four boards.
- Panel DRC: zero findings and zero unconnected items; unit copper is copied exactly.
- All five harness pairs retain matching pin assignments.
- Component positions, pad sizes, board outlines, mounting holes, optical aperture,
  antenna keepouts and USB routing match the pre-change boards.
- Minimum component body/land spacing remains 2.003 mm Lower, 2.025 mm Upper,
  2.010 mm Wheel and 2.500 mm Encoder.
- The six reviewed capacitor paths are unchanged, including their widths and layers.
- Via drills remain 0.30 mm; no via holes overlap SMD lands.

`edge-clearance.json` records source hashes, measured outer-edge copper distances
and the before/after via counts. Individual fabrication packages, the panel,
routing previews and 3D exports are refreshed for this revision.

These are digital geometry and connectivity checks. Existing hardware and RF
bench-validation limitations remain unchanged.
