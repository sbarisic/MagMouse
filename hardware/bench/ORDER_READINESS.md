# Rev-A bench PCB order readiness

Reviewed 2026-09-12. **Pending supplier/CAM approval; not approved to order.**
Scope: five bare three-board panels, one component population and one unframed
stencil. U32 remains DNP; all other core features are retained. Final shell and
ergonomic mechanisms are a later revision. No enquiries, orders or payments
were sent during this review; the supplier communications are drafts only.

## Completed in CAD and the review package

- Local manufacturing review is complete: corrected economy-order job metadata,
  checked actual round/slot drill outputs, and prepared a consolidated CAM
  handoff with exact settings and fill/open-hole drawings. See MANUFACTURING_REVIEW.md.
- Main L1 changed to Bourns SRP4020CC-3R3M with manufacturer lands, a local
  rotation/placement adjustment and a 0.15 mm C2 move. Schematics, PCB and
  purchasing identity agree; original LCSC identity removed. See L1_REVIEW.md.
- Main, Wheel and Encoder remain four-layer, routed and individually checked
  for zero unrouted, physical DRC and schematic-parity findings. Panel/native
  and strict Main/Wheel electrical checks refer to the new source hashes.
- Nine internal connectors are replaced by 86 plated solder holes on 2.54 mm
  pitch. Generated pin maps verify all 46 AWG28/AWG22/AWG24 conductors and
  preserve all grounds. Component-side and mirrored solder-side views identify
  every pad. No connector purchasing identity or paste remains on these lands.
- Hall, WSON and ADC paste patterns now follow the cited package geometry.
  Actual polygon area/perimeter/coverage/volume measurements and package
  dispositions replace the earlier rectangle-only screening as review evidence.
- Support contact strips, test-pad access, local ground/thermal inventory and
  copper close-ups are included. Wheel TP34 is obstructed by C90; J11.1/J11.2
  are the designated ACT_5V/return alternative with secured test leads.
- Panel, Gerber/drill and stencil ZIPs, source/transform manifest, via-only
  filling inventory, purchasing list and assembly aids are regenerated together.
  The exported JLC enquiry draft identifies the exact ZIP hashes.

## Manufacturing handoff and later assembly tasks

1. **During assembly — wire selection and bench fit:** consumer-source wire product, stripped
   strand/insulation fit, clamp fit and solder inspection. The Würth enquiry
   requirement is superseded; its follow-up draft must not be sent.
2. **During bench assembly — optical mounting:** use the selected matched
   Ploopy PMW3360/lens kit and adjust the fixture/case to its alignment and
   working height. No incompatibility is currently confirmed; supplier identity
   evidence remains open, but is not an indefinite bare-board ordering gate.
3. **Stencil design complete:** 0.10 mm is selected for Rev-A with the existing
   reviewed aperture patterns and documented volume tradeoff. Manufacturing
   confirmation remains with CAM. Paste choice, reflow limits and practice
   printing/reflow are required before assembly, not before bare-board ordering.
4. **JLC CAM response:** confirm slots/tabs, three designs, drill sizes,
   selective epoxy fill/copper cap, exact JLC041611-2116 stack and final stencil
   groups. A quotation or automatic DRC result is not CAM acceptance. If JLC
   requires an order before formal review, retain this gate as pending.

## Before assembly and powered tests

Purchase one population and specified wire materials, confirm received parts and
lot moisture limits, build adjustable supports and secure motor/magnets.
Measure real wire, clip, cable and optical fit. Inspect cut edges and
hidden-pad practice assemblies; visual appearance alone does not prove joints.
Component freight, mechanisms and consumables still need complete EUR pricing.

Bring up with current-limited power and actuator-off defaults: unpowered checks,
logic rails, USB, ADC1/Hall, optical, encoder/ADC2, low-current motor/brake, then
one button actuator at a time. Firmware, USB compliance, analog noise, actual
torque, temperature and assembly yield require hardware measurements.

Fixed button magnets use software endpoint calibration; precision magnet positioning
is not a fabrication blocker. Printed flexure/stop fit, monotonic unclipped travel
and coil/wheel interference remain hardware tests. Editable PETG fixtures and
STEP/STL/dimensioned views are supplied; no new PCB mounting holes were added.
