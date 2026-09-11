# MagMouse assembly pricing inputs

**QUOTE ONLY — NOT FOR FABRICATION OR ASSEMBLY.**

Request five assembled Main boards, five Wheel boards and five Encoder boards,
delivered together to Croatia, 43000. These are three separate jobs, one design
per job. No production panel, breakaway tooling, panel BOM or panel-coordinate
CPL is supplied. Quote any assembler handling panels, rails, tooling and fixture
charges separately. The small encoder may require a service panel for assembly.
Do not infer final manufacturing approval from the routed copper or file names.

## Board settings

| Job | Finished outline | Layers | Quote stack and finish | Via treatment |
| --- | --- | --- | --- | --- |
| Main | 125 mm long, 80 mm maximum width, 44 mm front | 4 | Nominal 1.6 mm, JLC041611-2116, 1 oz outer/inner, green solder mask, ENIG | All via holes epoxy-filled and copper-capped |
| Wheel | 55 × 60 mm | 4 | Same JLC041611-2116 stack and finish as Main | All via holes epoxy-filled and copper-capped |
| Encoder | 14 × 18 mm | 2 | Nominal 1.6 mm FR-4, 1 oz copper, green mask, ENIG quote assumption | Ordinary tented vias; see inventory for overlap check |

Main and Wheel preserve the selected four-layer CAD stack: 0.035 mm outer
copper, 0.109 mm 2116 RC54% prepreg, 0.030 mm In1 copper, 1.230 mm core dielectric,
0.030 mm In2 copper, 0.109 mm prepreg, 0.035 mm outer copper. The saved thickness
is 1.578 mm, including two 0.010 mm mask layers. Select the supplier's nominal
1.6 mm JLC041611-2116 option; ask engineering to confirm this exact construction
against the saved stack instead of substituting a generic four-layer stack.

The Encoder source specifies two layers and 1.6 mm, with no detailed saved
dielectric stack or finish. Its copper weight and ENIG above are explicit quote
assumptions. It has not been migrated to the common four-layer panel stack.
The Gerber-job bounding box can include Edge.Cuts line thickness (for example
80.1 × 125.1 mm); finished dimensions are measured at the outline centreline.

## Main USB controlled impedance

Request **90 Ω differential impedance, F.Cu referenced to continuous GND on
In1.Cu**, on Main's USB D+/D− path from J1 through U1 ESD protection and R67/R68
series resistors to U3 ESP32-S3. The selected coupled geometry is **0.1466 mm
trace width / 0.1501 mm edge-to-edge pair gap** on JLC041611-2116. Local pad
launches and component interruptions are present in the routed data path.
Quote the supplier's guaranteed tolerance and impedance coupon/test charge
explicitly; this package does not invent a guaranteed tolerance. Confirm any CAM
width/spacing compensation before production. Do not change the stack or thin
the ground reference to fit a cheaper service. Wheel uses the same stack for
consistency; it has no USB pair or separate controlled-impedance target.

## Via filling and capping

Quote **all actual through vias on Main and Wheel** as epoxy-filled and
copper-capped (planar solderable surface on both outer layers). This deliberately
avoids relying on selective filling to estimate cost. Tenting or solder-mask
plugging alone does not satisfy this request. Do not copper-fill an entire via
unless quoted as a separate alternative; the baseline is nonconductive epoxy
fill with copper caps.

Each job includes `all-vias.csv`, `via-in-pad.csv` and a top-view `via-map.svg`.
The inventory checks intersection of the actual drill disk with SMD pad copper,
including off-centre edge overlaps and bare test pads. Red points are these
overlaps; grey points are other vias. SVG hover text identifies each via and
pad, and the CSV gives UUID, drill/pad diameters, net and exact coordinates.
All Main/Wheel vias are covered by the quote request even if absent from the
smaller overlap table. The overlay is a location aid, not a Gerber machining layer.

**Do not fill component holes, USB shell slots, optical-sensor through holes,
connector holes, or NPTH alignment/mechanical holes.** Excellon X2 tool attributes
distinguish ViaDrill from ComponentDrill; the exporter verifies every via hit
against the CAD inventory. The CSV's Gerber/CPL coordinates use the drill-file
origin. Confirm ambiguous holes by position, not by diameter alone.

The CAD defaults still show tenting with filling/capping disabled; the exported
Gerbers do not by themselves specify the required additional process. These
written notes and the order's filled/capped selection are required for the quote.
Request supplier production-file confirmation of the via map and cap treatment
before any eventual order. Exposed-pad solder coverage, stencil apertures,
cap planarity and paste wicking still require manufacturing review.

## Assembly files and reference coverage

Upload each job's `*-Gerbers-QUOTE.zip`, `*-BOM-QUOTE.csv` and `*-CPL-QUOTE.csv`
as a matched set. They use one common **absolute KiCad origin**, X to the right
and Y upwards: CPL/Gerber Y is negative KiCad Y. Negative coordinates are
intentional. Gerbers, drills and CPL must receive the same translation if CAM
normalizes the outline. Coordinates are millimetres, with no bottom X mirroring.

CPL rotation is KiCad's native footprint rotation normalized to 0–360 degrees.
Supplier-library rotation and centroid corrections are not applied. Inspect the
JLC placement preview against `assembly-F.svg`, `assembly-B.svg`, pad 1 and the
actual footprint before accepting assembly; coverage validation alone cannot
prove feeder orientation. All quoted physical components are on the top side;
back-side copper test pads are not separate assembly parts.

J1 has through-hole shell anchors as well as SMT contacts. Ask the assembler to
include or explicitly exclude anchor soldering. Review connector handling,
exposed pads, MSL/baking, polarity and the custom RGB footprint. No added tooling
holes/fiducials or component substitutions are authorized by this package.

The BOM carries exact schematic MPNs and catalog IDs. **These are matching
requests, not live stock or assembly-service confirmations.** Retain the
manufacturer identity and ratings when matching. `procurement-review.csv`
preserves recorded sourcing status for every physical source component and
lists five-board quantities, excluding any supplier attrition allowance.
`excluded-from-assembly.csv` accounts for every omitted source reference.

Main U35 PMW3360DM-T2QU is excluded from both the uploaded BOM and CPL because
the recorded sourcing decision is customer supply/post-assembly installation.
It remains in the procurement list (catalog C20612443, recorded unavailable).
Ask for a separate sensor-supply/installation line if the assembler can accept
it. Its price is **not included** by the standard SMT quote. The LM19-LSI lens
is a separate optical/mechanical item, not an SMT placement. Copper-only test
pads are also excluded; no other physical component is silently omitted.

## Price scope and remaining release work

Request itemized PCB, setup, stencil, assembly, selected components, special via
processing, impedance testing, any service panel/fixtures, shipping and tax.
Record unpriced or unmatched components explicitly. Five sets means five of
each of the three designs, not five boards total. No current PCBA total has
been obtained from these files merely by generating them.

Keep separate cost lines for sensor/lens, FFC and JST harnesses, GB1806 motor,
shaft/bearings, magnets, wheel, coils, shell, assembly labour and test fixtures.
The old $179.47 five-panel bare-PCB calculator figure applies to a different,
provisional nesting study and is not a quote for these jobs.

Before release: freeze mechanical interfaces and cables, adjust PCBs, repeat
whole-board electrical/thermal/return reviews, migrate Encoder if sharing a
four-layer panel, finalize tooling/tabs and manufacturing details, match parts,
review rotations, regenerate all files and approve supplier production files.
This quote pass changes no board/schematic and starts no panelization.

## Supplier guidance checked 2026-09-11

- [JLCPCB KiCad 10 BOM/CPL export](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad): file columns and native KiCad export workflow.
- [JLCPCB BOM/CPL preparation](https://jlcpcb.com/help/article/advice-for-bom-and-cpl-files-preparation): matching reference designators and component review.
- [JLCPCB via covering](https://jlcpcb.com/help/article/pcb-via-covering): filled/capped options and identifying vias with drawings/order notes.

## Encoder snapshot inventory

3 schematic/PCB references; 3 quoted placements; 0 explicit exclusions.
17 through vias; 0 drill disks intersect SMD pads.
Via drill counts: {'0.3': 17}.

See all-vias.csv, via-in-pad.csv and via-map.svg alongside this archive for exact coordinates and pad references.
