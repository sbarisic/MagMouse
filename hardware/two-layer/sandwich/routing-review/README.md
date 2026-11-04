# Split Main routing review — 2026-11-04

Lower and Upper now have independent schematic projects and completed two-layer
routing. All four boards pass native KiCad 10.0.6 ERC, DRC, connectivity and
schematic-parity checks under the saved rules. `summary.json` records the source
hashes and exact checked dimensions. The five inherited PCB ignored categories
remain listed in every report; no exclusions were added to obtain this result.

The exported Lower/Upper netlists were compared pin-for-pin and value-for-value
against `Main-reference.xml`. All 208 retained Main circuit components occur on
their assigned board. The 19-wire Main harness is present in both schematics
with matching pad numbers and net names. Each board adds two solder-wire arrays
and four mounting-hole footprints. The later standard-via revision updates
drills and reroutes Wheel fanouts to eliminate via-in-pad placements.

Freerouting 2.5.0 routed the remaining connections after placing the long USB
pair around the optical reserve. Native minimum widths were restored after
import. Lower's autorouter clearance margin was increased to 165 µm to leave
room for that restoration. The standard-via revision explicitly changes via
annular width to 0.075 mm and hole-to-copper clearance to 0.20 mm using JLCPCB's
published fabrication limits, while preserving the existing copper and
hole-to-hole clearances. Power escapes
were widened where other copper and keepouts allow. Ground was filled and
stitched on both faces, and unused fanout vias were removed.

The later assembly-spacing revision moves components to obtain at least 2 mm
between separate body-and-land envelopes. `../assembly-spacing-review.json`
records the checked gaps, source hashes, moved origins and rotations. USB,
optical, Hall, antenna and mounting datums remain fixed. The matching five-pad
stack power arrays move from y = 11 to 12.25 mm. Both 19-wire pin maps remain.
Encoder has two 4 mm upper chamfers; Lower has the specified 17.26 × 8.60 mm
optical opening. The outer Main dimensions and 5 mm antenna reserves remain.

The front/back copper SVGs are native KiCad exports. Lower front/back and Upper
front/combined copper views were visually screened; the generated Main routing
overview was also inspected. Per-net track-width/length tables are provided for
electrical review; lengths include all branches and are not propagation-delay
measurements. The retained 1.10 mm USB trunks are 58.673 mm (DP) and 58.991 mm (DM), excluding
fanouts and series-resistor-to-MCU routing. No impedance or signal-quality
measurement is claimed.

On Wheel's front copper, the two motor phases and the brake gate take separate
paths into J5. At y = 48 mm, 5 mm above the connector center, the phase B to C
edge gap measures 0.685 mm (previously 0.167 mm). The brake gate to phase B gap
measures 0.925 mm (previously 0.151 mm). These measurements apply to that
cross-section. See the [before and after drawing](Wheel-trace-spacing.svg).

The quote package contains 248 fitted BOM components per mouse, plus listed
manual wire-pad features and separately priced mechanics. Lower/Upper/Encoder
have no detected via-hole intersections with SMD lands. The standard-via Wheel
also has no detected intersections; the exporter rejects any remaining overlap.
All via drills are at least 0.30 mm. L1 has a purchasing MPN but no saved LCSC ID.

Routing is complete. Physical optical/lens fit, supplier CAM and
assembly review, and electrical/thermal/radio validation remain open before a
manufacturing release. The files support supplier pricing without claiming
hardware acceptance or an order.
