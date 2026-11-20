# Routing rebuild review — 2026-11-06

The 2026-11-20 lower-board update moved 17 footprints and test points to
give the USB pair continuous opposite-layer GND while keeping the buck and
optical-buffer feeds short. The lower buck feed now screens at 19.56 mΩ after trace cleanup.
See the [USB comparison](lower-usb-placement.png), [ground coverage](lower-usb-ground.png)
and [measured before/after paths](lower-usb.json).

The remaining narrative and table below record the routing-rebuild checkpoint. The subsequent
[0.5 mm edge-clearance revision](edge-clearance.md) changes local Lower routing
and Encoder ground routing; the accompanying JSON now contains those current
measurements. Encoder is no longer byte-identical to this earlier checkpoint.

Lower, Upper and Wheel now use fixed-width power routes, explicit short pin
escapes, and renewed GND pours and stitching on both copper layers. Encoder's
PCB is byte-identical to the starting file. Component placement, outlines,
mounting holes, optical aperture, connectors, antenna keepouts and the original
USB copper are preserved (2 nm tolerance for coordinate serialization).

## Routing changes

- 5 V trunks: 1.0 mm; main 3.3 V distribution: 0.5 mm; motor phases: 0.75 mm.
- Local analogue and optical supplies: 0.35 mm; main buck switch route: 0.6 mm.
- Signal routes: 0.15 mm. Existing USB escapes and the two Upper current-limit
  pin exits retain their necessary 0.127 mm sections. The Upper exceptions
  are approximately 0.73 mm per pin.
- Power pin exits use short 0.15/0.25 mm sections where land pitch requires
  them. Wide trunks retain their width through bends. The input-capacitor
  branch uses 0.6 mm after its short pin exit.
- The six reviewed capacitor connections remain on F.Cu with zero vias and
  pad-centre distances below 5 mm. U21–C47 remains directly connected on F.Cu.
- Wheel's AVDD connection crosses to the bottom layer to free the driver pin
  exits; its local decoupling connection remains on the component side.
- Lower's obstructed pin exits were moved outward. The final signal cleanup
  converted 244 Lower and 61 Wheel segments to clear 45-degree bends.
- Redundant GND tracks covered by filled copper were removed. Required ground
  bridges and local returns remain. The small C22/C77/C83/R77 ground lands use
  solid local zone connections to avoid starved thermal spokes.

All vias retain 0.30 mm drills; there are no via-hole/SMD-land intersections.

## Measured comparison

Before means the saved circuit-correction boards immediately before this
routing rebuild, not an older Git layout. Length includes all signal, supply
and explicit GND tracks; filled planes are not counted. Angle counts exclude
segments shorter than 0.1 mm.

| Board | Track length mm, before / after | Vias, before / after | Non-45-degree segments, before / after | Minimum body/land gap mm |
| --- | ---: | ---: | ---: | ---: |
| Lower | 5380 / 6455 | 536 / 615 | 291 / 88 | 2.003 |
| Upper | 2882 / 2335 | 134 / 143 | 44 / 0 | 2.025 |
| Wheel | 4493 / 3305 | 435 / 264 | 1405 / 53 | 2.010 |

Lower remains the densest board. Its total routed length and via count
increased while Upper and Wheel decreased in length. These measurements are
retained in [routing-rebuild.json](routing-rebuild.json), including compact
baseline geometry and placement data so large routing snapshots are unnecessary.

The Lower regulator feed screens at 27.7 mOhm, down from 82.9 mOhm immediately
before this rebuild. The Wheel input-to-driver path screens at 36.2 mOhm,
versus 18.5 mOhm before this rebuild: its regular 1.0 mm route has a higher
resistance than the preceding irregular, locally widened route. At the
separate 2 A screening case this is approximately 72.5 mV and 144.9 mW.
The local undervoltage sense branch shares approximately 1.50 mm of driver
pin-escape copper, with an 8.35 mV screened shared-feed error at 2 A/125 C.
See [the power review](../circuit-review/power-paths.json) for assumptions,
all paths, current budgets and limitations.

## Validation

- Fresh ERC, DRC and schematic-to-PCB parity: zero findings and zero
  unconnected items on all four individual boards.
- The rebuilt four-board panel passes native DRC with zero findings and zero
  unconnected items. Copied copper, pads and drilling are checked against units.
- All 1,028 schematic pins and five harness pairs match. Encoder is unchanged.
- Minimum 2 mm body-and-land spacing, two copper layers, 0.30 mm via drills,
  no via-in-pad, and unchanged geometry/keepouts pass independent checks.
- An additional geometry check finds no track/via copper outside the PCB
  material or inside the optical aperture.
- All six reviewed capacitor placements meet their <=5 mm target and all six
  selected connections use F.Cu with zero vias.
- Ground pours are filled and connected; no ignored DRC categories or
  exclusions were added for this work.

[Top routing](../all-routing-top.png) and [bottom routing](../all-routing-bottom.png)
show traces without pours. The [top](../all-routing-top-ground.png) and
[bottom](../all-routing-bottom-ground.png) ground views include filled copper.
Both sides are shown from the component side for positional comparison.

Resistance calculations are screening estimates, not measured ampacity or
thermal acceptance. SPI back-powering, actual shutdown timing, rail ripple,
motor transients, ground bounce and physical assembly remain **UNVERIFIED**
until bench tests are performed. The existing
[bench test plan](../circuit-review/README.md) remains applicable.
No firmware, supplier quote, purchase, commit or push is part of this routing task.

Saved KiCad files are authoritative. Use `validate_circuit_fixes.py`,
`assembly_spacing.py verify`, and `export_quote.py` for checks/exports.
`rebuild_routes.py prepare` intentionally clears routing and is not a routine
validation command.
