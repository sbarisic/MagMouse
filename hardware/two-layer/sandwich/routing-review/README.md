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

TP28 moved to (34,69.5) mm and TP29 to (38,78) mm to clear the USB corridor.
All other component origins and angles retain the approved placement, allowing
Specctra coordinate rounding of at most 0.000051 mm. The
70 × 100 mm tapered outlines, optical and 5 mm antenna reserves, fixed Hall
positions, four mounting positions and both 19-wire harnesses are retained.

The front/back copper SVGs are native KiCad exports. Lower front/back and Upper
front/combined copper views were visually screened; the generated Main routing
overview was also inspected. Per-net track-width/length tables are provided for
electrical review; lengths include all branches and are not propagation-delay
measurements. The long USB trunks are 58.987 mm (DP) and 58.991 mm (DM), excluding
fanouts and series-resistor-to-MCU routing. No impedance or signal-quality
measurement is claimed.

The quote package contains 248 fitted BOM components per mouse, plus listed
manual wire-pad features and separately priced mechanics. Lower/Upper/Encoder
have no detected via-hole intersections with SMD lands. The standard-via Wheel
also has no detected intersections; the exporter rejects any remaining overlap.
All via drills are at least 0.30 mm. L1 has a purchasing MPN but no saved LCSC ID.

Routing is complete. Physical fit, the final optical aperture, supplier CAM and
assembly review, and electrical/thermal/radio validation remain open before a
manufacturing release. The files support supplier pricing without claiming
hardware acceptance or an order.
