# Housing

Reserve editable CAD and reviewed exports here. Define grip dimensions, optical
aperture and lens-to-surface height, PCB mounts, cable strain relief, feet, and
access for assembly/recovery. Check actuator packaging and heat paths before
freezing the enclosure. Dimensions and material are TBD.

The user selected a PCB-first approach on 2026-09-09: develop the motherboard
and mechanical interfaces, then design the outer shell around them. An existing
shell CAD model is not a prerequisite for provisional component placement.
The [motherboard](../../hardware/pcb/README.md) starts at 50 x 95mm with front
USB-C. Adjust it if component packing or the hand/wheel/button arrangement needs
more space; the current outline is not a proven fit for the whole assembly.

U35 now anchors the optical centre at board X=125.5, Y=157.5mm: 25.5mm from the
left edge and 57.5mm behind the front USB edge. Its body stays above the PCB,
with the LM19-LSI lens below. Design the base, lens retention and feet around
the [optical height datums](../optical/README.md). Samples must verify the fit
before the opening, posts and seating height become manufacturing dimensions.
Reserve wheel/magnet envelopes, mounting points and connector openings during
placement; designing the shell later does not remove those space requirements.

Provide stationary mounts for three custom wound coils and clearance for separate
actuator and sensing magnets on the elastic paddles. Design replaceable paddle
attachments and mechanical stops; verify middle-click clearance with the wheel
assembly. Coil heating must not compromise flexure stiffness or housing stability.
