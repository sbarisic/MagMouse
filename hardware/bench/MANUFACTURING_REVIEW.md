# Rev-A manufacturing handoff

Reviewed 2026-09-12. **Local review complete; JLC CAM confirmation pending.**
Five bare three-design panels and one stencil; no PCBA service. The user
authorized submission, and JLC's contact form confirmed receipt on 2026-09-12.
See [submission record](submissions/2026-09-12-jlc-cam/receipt.json) and the
frozen archive beside it. CAM approval is still pending. No order or payment
was made, and the historical price has not been refreshed. Other supplier
communications remain drafts.

## Findings and corrections

- Corrected the exported Gerber-job envelope from 151.05 x 139.05 mm (including
  drawing strokes) to the actual profile centerline size of **151 x 139 mm**.
- Corrected its impedance-service flag to **false**, matching the selected
  economy order. The 90 ohm design target, USB geometry and exact stack remain.
- Removed automatically inferred design-rule metadata, including zero-clearance
  entries that could be mistaken for fabrication permissions. Actual copper and
  all existing DRC/electrical acceptance records are unchanged.
- Generated an explicit open-hole inventory and colour-coded via-treatment map.
  The Excellon round holes and all four USB anchor slots match the board.
- Retained the selected uniform 0.10 mm stencil and the three existing groups.
  No aperture resizing or automatic rearrangement is authorized.

## Published capability screening

JLC lists 2 mm panel separation, at least 5 mm mouse-bite tabs, 0.5–0.8 mm bite
diameters and 0.2–0.3 mm webs. Our panel uses 2 / 5 / 0.6 / 0.3 mm respectively.
Minimum component-hole annulus is 0.20 mm; minimum trace width is 0.1466 mm.
These fit the published multilayer 1 oz ranges. See
[JLC capabilities](https://jlcpcb.com/capabilities/Capabilities).

There are **1,114 vias to fill/cap**: 641 at 0.20 mm, 472 at 0.30 mm and one
at 0.40 mm. All are within JLC's published epoxy-filling diameter guidance.
There are **109 plated component holes/slots and 56 NPTH holes to leave open**.
The 86 new wire holes are included in that 109. The fill selection applies to
actual vias only; use Excellon ViaDrill/ComponentDrill attributes and both CSVs.
[JLC via covering guidance](https://jlcpcb.com/help/article/pcb-via-covering).

JLC offers 0.10 mm as a standard stencil thickness and accepts several designs
in one paste file. The 151 x 139 mm layout fits the requested 220 x 200 mm sheet
with room for the published approximately 8 mm machining-clamp allowance.
Preserve group positions; a global centering translation is acceptable.
[JLC stencil instructions](https://jlcpcb.com/help/article/instructions-for-stencil-order).

Existing native DRC/parity and strict electrical reports match current source
hashes. This pass adds manufacturing checks; it does not repeat electrical
routing work. Small reference text may lose detail in printing; use the
placement and numbered wire-pad drawings during assembly.

## What JLC must check in the production files

1. **Exact construction:** JLC041611-2116, nominal 1.6 mm, nominal 1 oz inner
   and outer copper. STACK_AND_LAYERS.md carries the actual CAD layer table,
   including 0.109 mm outer dielectrics and 0.030 mm modeled inner copper.
   The public stack page did not expose this exact identifier during this
   review; retain the previously quoted selection and require confirmation.
   No substitution to another stack or half-ounce inner copper is authorized.
2. **Routed profile and tabs:** mill the supplied outline, preserve all three
   unit envelopes and ten tabs. Identify any required inside-corner tool-radius
   accommodation before modifying the file. Depanel before population.
3. **Hole treatment:** fill/cap only the listed actual vias. Keep component,
   wire, locating, tooling and perforation holes open. Select production-file
   confirmation so these treatments can be checked before fabrication.
4. **Stencil:** 0.10 mm, top only, supplied apertures as-is. Preserve the three
   groups and their relative orientation. If a rearrangement is unavoidable,
   return final coordinates before the alignment jig is used.

These are the normal manufacturing handoff items. Wire fit, lens mounting,
magnet calibration, practice printing and oven setup are assembly tasks and
do not add further bare-board ordering gates.

## Handoff files

The exact submitted bundle is preserved in
`submissions/2026-09-12-jlc-cam/CAM-review-attachments.zip`. The exported
`package/supplier-drafts/JLC_CAM_REVIEW.md` remains the prepared request;
its draft label and the exported package bytes were preserved after submission.
The contact-form cover requested the same manufacturing review and included
the PCB, stencil and complete bundle hashes. The bundle contains the PCB and
stencil ZIPs, exact settings, layer/stack table, profile drawing, hole-treatment
map and inventories, and stencil/jig review files. Its internal hash manifest
identifies each attachment; `package/file-sha256.json` identifies the complete
repository export. No supplier reply or approval is implied by this package.
