# Rev-A bench PCB order readiness

Status reviewed 2026-09-12. This is a self-assembled electronics prototype:
five bare three-board panels, one component population, one stencil, U32 DNP.
The user intends to purchase the optical sensor/optic from Ploopy later.
No purchase is authorized. Final shell and ergonomic paddles are a later revision.

## Completed CAD work

Main, Wheel and Encoder are routed. The saved acceptance record reports zero
unrouted, physical DRC and schematic-parity issues on all three units. Encoder
uses the common four-layer stack. The derived panel has separate board nets,
routed separation geometry and perforated tabs. Main's strict analog, USB,
power, control and return-path checks passed on the recorded source hashes.
See CAD_REVIEW.md and package/evidence/acceptance.json. These results establish
CAD checks only, not assembly yield, thermal behavior or working hardware.

## Work before freezing the fabrication files

1. **Implement and validate Main L1's available replacement.** The Bourns
   SRP4020CC-3R3M candidate requires its recommended land pattern, a local
   buck-routing review and consistent schematic/BOM/footprint identity.
   Preserve the short switching and capacitor-return loops. Rerun affected
   power checks and native DRC/parity; rebuild the derived panel and stencil.
   The original Sunlord part remains in the current CAD and is not sourced.
2. **Close interfaces that could still change copper or holes.** Qualify the
   150 mm Main-Wheel FFC against the Hirose connector drawing and reverse
   J8.N to J9.(31-N) mapping. Confirm power/encoder/coil mating connectors and
   cable access. The Wurth enquiry is pending. Confirm Ploopy's exact sensor
   suffix and lens MPN against Main's footprint, aperture and optical datum.
   Supplier choice does not establish lens compatibility.
3. **Review the stencil by package.** Check exposed-pad windowing and paste
   volume, fine-pitch release, connector paste and part reflow limits against
   manufacturer guidance. Retain U32 paste exclusion and separate optical
   hand-soldering. Current 0.10 mm aperture-ratio screening is only a first pass.
4. **Finish the bench access and physical review.** Verify removable supports
   clear underside copper/components, and that cables, lens retention and
   probes can reach the required pads. Confirm rail, fault/enable, brake,
   current-sense and motor-phase test access. Review local thermal copper and
   returns at close scale, including any L1 or connector changes. Keep Hall
   positions provisional and use adjustable magnet/coil fixtures. Final
   wheel bearings, paddles and enclosure mounts are not required for this order.
5. **Regenerate and audit one consistent release snapshot.** Require zero
   unrouted/physical DRC/parity on the units, rerun strict electrical checks
   after changes, and verify panel transforms, copper isolation, tab clearance,
   layer mapping and via-fill inventory. Recheck population/stencil coverage,
   source hashes and rendered copper/paste/mechanical outputs. Retain an
   explicit Rev-A bench label and record unresolved hardware-test assumptions.

## Supplier review before fabrication approval

Obtain JLC CAM acceptance of the three-design panel, routed slots/tabs,
minimum drills and selective epoxy-filled/copper-capped vias. Component and
mechanical holes must remain unfilled. Confirm JLC041611-2116, copper weights,
ENIG and the selected economy impedance option without substituting the
stack or USB geometry. Approve the stencil group arrangement before making
the alignment jig. A website price or zero DRC is not CAM acceptance.

The existing exports remain QUOTE ONLY until the applicable file reviews
are closed. Complete component/consumable pricing is a budget decision, not
proof of PCB readiness. Do not represent unknown prices as zero.

## Before assembly and powered tests

Obtain the required components and harnesses, practice fine-pitch reflow,
prepare supports and secure motor/magnets. Hidden-pad joint quality cannot
be established by visual inspection alone. Prepare minimal bring-up firmware
with actuator-off defaults and bounded test commands while boards are made.
Use ASSEMBLY_AND_BRINGUP.md: unpowered checks, current-limited logic power,
USB, ADC1/Hall, optical tracking, encoder/ADC2, low-current motor/brake, then
one button actuator at a time. Hardware measurements close electrical,
thermal and signal-timing questions; CAD cannot close them in advance.
