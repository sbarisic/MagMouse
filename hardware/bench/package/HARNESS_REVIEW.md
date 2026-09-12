# Rev-A bench harness and optical compatibility

2026-09-12. The source-derived `package/harness-pin-map.csv` is the pin authority.
Coordinates refer to each PCB's component-side view. Separate mirrored
solder-side drawings identify the same pad numbers. Each harness must pass continuity and adjacent-pin isolation
before connecting power. A visually straight cable does not prove pin order.

| Harness | Termination | Conductors and finished length | Verification |
|---|---|---|---|
| Main J10 to Wheel J11 | 1×2 PTH, 1.1 mm holes / 2.2 mm pads | Paired AWG22, 150 mm, pin 1 to 1 ACT_5V and 2 to 2 GND | Solder and continuity inspection required |
| Main J6 to Encoder J7 | 2×4 PTH, 0.8 mm holes / 1.8 mm pads | AWG28, 150 mm, all eight pins straight through including three grounds | Numbered pad mapping; no connector fitted |
| Main J2/J3/J4 to coils | 1×2 PTH, 1.1 mm holes / 2.2 mm pads | Paired AWG24, 200 mm per lead | Both leads are bridge outputs, neither is GND |
| Main J8 to Wheel J9 | 2×15 PTH, 0.8 mm holes / 1.8 mm pads | 150 mm, 30-way AWG28 ribbon; J8.N to J9.(31-N) | Retain every conductor including grounds; no FFC contact orientation applies |

All arrays use 2.54 mm pitch and are hand soldered after reflow.
The requested finished PTH diameters are 0.8 mm for signals and 1.1 mm for
power/coils; CAM must confirm drill compensation after plating. The KiCad and
Excellon nominal hole values are 0.8/1.1 mm, not a request to fill those holes.
Feed wires
from the component side, keep bare wire above the board below 1 mm, and trim
solder-side ends to less than 1.5 mm. Inspect for strands, bridges and insulation
damage. Clamp insulation to the fixture before flexing the cable; do not load
the solder joints. Verify actual stripped/tinned wire fits without forcing.
Use stranded insulated copper; wire product, insulation thickness, minimum bend
radius and consumer delivery price remain to be selected. No crimp contacts,
housings or FFCs are purchased. Connector removal does not increase power limits.

With power disconnected, check all 46 conductors against the generated map,
including every ground, and check isolation to adjacent unlike nets. Mark
conductor 1 at both ends before separating ribbon conductors. A ground-to-ground
short is expected only where the schematic joins grounds; it cannot prove that
each required physical ground wire is present. Inspect those wires individually.
Use a meter with both harness ends disconnected from power; never use live
continuity mode. Start SPI slowly and measure waveforms at both ends before
accepting intended clock rates over the new 150 mm wire harness.

The Würth follow-up is superseded and must not be sent. All 86 new termination
holes are component holes: exclude them from epoxy filling and copper capping.

## Ploopy optical comparison

Ploopy remains the selected private-consumer supplier. Its sales description
does not establish the exact sensor suffix, lens MPN or dimensional stack.
The current target is **PMW3360DM-T2QU + LM19-LSI**, with Main optical datum
(40.5,72.5) mm in unit coordinates, corresponding to fixture (65.5,92.5).
The nominal LM19 flange-to-tracking-surface distance is 2.4 mm, range 2.2-2.6 mm;
this is not PCB height or software lift-off distance. See the retained
[optical selection review](../kicad/OPTICAL_SELECTION.md).

`supplier-drafts/PLOOPY_COMPATIBILITY.md` requests suffix, lens identity,
terminal/body dimensions, locating features, sensor seating and lens stack
drawings, plus the supported firmware/SROM source. Compare those to U35 and
the actual aperture/keepout before approving the optics. No alternate sensor,
new hole or aperture resizing is justified without that evidence. The lens
clip and sample fit remain adjustable bench-fixture work.
