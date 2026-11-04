# MagMouse four-board prototype — quotation package

This package requests pricing, not production authorization. It describes the
current passive-plastic-button design, not the older three-board coil design.
One complete mouse needs one of each board:

This revision replaces 193 small resistors and ceramic capacitors with 1206
parts. Electrical values are retained. The later spacing revision provides
2 mm between separate component envelopes, chamfers Encoder's two upper corners,
and adds Lower's 17.26 × 8.60 mm optical opening. Replacement MPNs
are in the BOM; their supplier stock and assembly availability have not been
checked, so superseded small-package supplier IDs are blank. The saved JLCPCB
prices predate this revision.

| Board | Size | Copper layers |
| --- | --- | ---: |
| Lower | 70 × 100 mm, tapered | 2 |
| Upper | 70 × 100 mm, tapered | 2 |
| Wheel | 70 × 67 mm, clipped Main profile | 2 |
| Encoder | 14 × 18 mm, two 4 mm upper chamfers | 2 |

For comparison with the earlier project budget, request five of each PCB and
one complete component population. Quote assembly separately if desired; the
previous plan was self-assembly. These are four individual designs, not a panel.
Supplier panelization, rails and tooling are not included in the board outlines.

Use 1.6 mm nominal FR4 and 35 µm outer copper as the quote target, with the
fabricator's final stack and tolerances confirmed before production. Quote the
actual minimum traces, 0.30 mm via drills and at least 0.45 mm via lands in the
supplied files. The earlier 0.20 mm drill quotation is historical.

## Files

- `Lower-gerbers.zip`, `Upper-gerbers.zip`, `Wheel-gerbers.zip`,
  `Encoder-gerbers.zip`: separate PCB uploads with copper, mask, silkscreen,
  paste, outline, plated and non-plated drill data.
- Each board folder contains its BOM, placement CSV and manual-items list.
- `combined-BOM.csv` and `component-inventory.csv` identify the complete set.
- `validation.json` identifies the checked source PCBs and rule settings.
- `SHA256SUMS.json` identifies the exact exported files.

Placement coordinates are millimetres from the KiCad absolute origin, with Y
inverted to the Cartesian convention; rotations are KiCad degrees and sides
are explicit. Check every supplier placement preview, particularly IC pin 1,
connectors and LED polarity. These files do not claim supplier rotation approval.
No-MPN wire arrays, test access and other manual items are kept out of the
pick-and-place BOM and listed separately. Empty LCSC fields require manual
sourcing or a supplier-supported part match. Saved catalog IDs are not a stock
reservation or a current-price quotation.

## Items the quote must address

Quote ordinary tented vias. The standard-via revision removes all detected
via-hole intersections with SMD lands, including the Wheel's former thermal
and signal via-in-pad placements. Confirm stencil apertures and exposed-pad
assembly from the actual design.
USB trace geometry needs the chosen fabricator stack checked before production;
the CAD clearance result does not establish controlled impedance or USB testing.

The via-hole/pad intersection lists must be empty on all four boards; the
exporter rejects overlaps or via drills smaller than 0.30 mm. Ground returns
and heat spreading use copper pours and off-pad stitching; assembled motor
driver thermal performance still requires measurement.
Lower's Edge.Cuts includes the 17.26 × 8.60 mm optical opening from PixArt's
PMW3360 R1.50 Figure 3, rotated with the sensor. Include this internal milling
in pricing. Internal corners are R1 mm for the nominal 2 mm router. Confirm
physical lens fit with these corners and the separate lens retention.

Include setup, stencil, panelization if needed, freight and destination taxes
in a delivered total. Sensing magnets, plastic click mechanisms, shell, optical
lens, wheel motor/mechanics and inter-board wires must be priced separately
where they are not represented by a purchasing BOM line.

The Main stack and Wheel each use 19 wires with three shared grounds. Wire
gauge, lengths and stack height still depend on the mechanical assembly.
Mechanical fit, physical electrical performance and assembled-radio performance
have not been validated. No fabrication order has been placed.
