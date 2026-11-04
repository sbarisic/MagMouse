# Lower, Upper and Wheel routing review

Baseline commit `3212e2d` was pushed before this revision. The Lower layout
moves C77, R131 and R28. Upper moves R37, R45, R57 and R70. Wheel groups the
ADC spare-input resistors R105 and R106 at the front. Their signal routes total
33.5 mm compared with 47.5 mm previously.

| Board | Power route sections revised | Closest component envelopes |
| --- | ---: | ---: |
| Lower | 31 | 2.003 mm |
| Upper | 23 | 2.025 mm |
| Wheel | 21 | 2.010 mm |

Each selected section replaces a set of mixed-width segments with a uniform-width
route. For example, one Wheel phase A run increased its narrowest width from
0.15 to 0.75 mm by taking a bend that added about 0.50 mm of length. Pin and
via escapes elsewhere still impose width limits. The [geometry
record](layout-review.json) lists the individual routes, widths and lengths.

The first pass put a via hole under each of two moved resistor lands. R131 and
R45 were adjusted and the final independent land-intersection test passed on
all four boards. The Main and Wheel checks cover ERC, DRC, schematic parity,
unconnected items, minimum component gaps, the optical aperture, the antenna
reserve and matched stack power-pad coordinates. Encoder's saved PCB SHA-256
matches the checkpoint. Panel testing compares the translated copper, pads and
fills against all four sources and runs native DRC. The bare STEP solids, panel
aperture, Encoder chamfers, GLB geometry and 3D archive were also checked.

The whole-path resistance model gives 48.4 mΩ for Upper U12 to U13, compared
with 47.7 mΩ at the checkpoint, within the existing 50 mΩ screening budget.
Physical lens and enclosure fit, switching noise, thermal behavior and loaded
voltage drop still require hardware measurements. [Current and ground review](POWER-GROUND.md)
