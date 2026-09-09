# Optical component placement

2026-09-09, KiCad 10.0.6. The complete optical group is now provisionally on
the motherboard: U35 plus 25 support footprints. The 22 BOM components are on
F.Cu; TP40..TP43 are on B.Cu after the 60 mm placement pass. The LM19-LSI
assembly occupies space below the PCB. The sensor centre
remains X=125.5, Y=157.5mm, with its front toward USB.

| Group | Placement and purpose |
| --- | --- |
| U37, U39, C80, C87 | Above the sensor, keeping the SPI interface together |
| U36, U38, C77–C82 | Right of the sensor; switched input supply and local core regulation |
| C83, C86, C85 | Beside VDD, VDDIO and VDDPIX pins respectively |
| C84 | Beside the VDDPIX bypass capacitor |
| R131–R136 | Along the left lead row for CS, SPI bias, motion and illumination |
| TP40–TP43 | Accessible from above, outside the proposed opening |

The supply-side pad centres of C83, C86 and C85 are each 2.175mm from their
respective sensor pin centres. These distances are placement checks, not routed
trace lengths. Route short bypass connections and ground returns first when
the optical section is cleared for routing. C84 shares the local VDDPIX return;
keep this internal regulator output isolated from other supplies.

The initial optical pass placed U36/U38 in the former wheel-electronics
reservation and U37 in the former IMU reservation. The later
[60 mm motherboard pass](PLACEMENT_60MM.md) relocated U36/U38 and their local
capacitors to the left of the sensor to give the wheel driver and ADC2 room
on the right. U35, C83..C86 and the mechanical datums remain fixed. The wheel's
mechanical keepout and the underside lens envelope remain present.

The aperture is still a drawing and copper/pad keepout, not an Edge.Cuts hole.
The lens envelope is below-board clearance guidance; it does not prohibit the
front-side support parts. Check actual lens, retention, base and feet together
before turning these assumptions into manufacturing dimensions.

## Verification

The first optical-support pass moved 25 footprints and preserved the other
291. The subsequent 60 mm pass intentionally rearranged circuit groups; it
preserved all 316 footprint identities, schematic paths and pad net assignments.
Native physical DRC and schematic parity pass with no new exclusions. No tracks,
vias or actual optical opening were added. See the
[current placement review](PLACEMENT_60MM.md) for counts and remaining work.
