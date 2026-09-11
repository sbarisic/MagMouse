# Adjustable bench fixture

Rev-A electronics test arrangement, not an ergonomic shell. Dimensions are mm.
Use the [1:1 fixture drawing](bench-fixture.svg) as an assembly layout, not as
a drill template for the PCBs. No motherboard or daughterboard holes are added.

## Support and adjustment

Use a 250 x 260 x 6 nonconductive base with a 10 mm accessory-hole grid, except
within the optical slider window. Fit removable edge saddles to M3 slots in
the base; saddle lips engage no more than 0.3 mm of the board underside.
Support Main at the four clear tab-adjacent sites recorded in the panel
manifest, then inspect both faces before tightening. Nylon clamping caps bear
only on clear board edges, never on components or test pads. Wheel uses its
four clear tab-adjacent sites; Encoder uses the two reserved side clips.

Main top-view origin is (25,20), component side up. Wheel origin is (60.5,160),
component side up, so the signal headers align in X. Use threaded standoffs
and locking nuts to adjust both board undersides from 15 to 35 mm above the
base. Keep at least 5 mm clear beneath non-optical components and permit
removing the base or tilting the carrier for bottom-side probing. All board
supports are removable: these coordinates do not freeze mouse-shell mounts.

The straight header-to-header route in this arrangement is about 74 mm before
insertion allowance. A 50 mm trial FFC does NOT fit this fixture. Reserve a
nominal 150 mm same-side cable and an elevated nonconductive bridge above the
rear Main components; minimum bend radius is determined by its selected
manufacturer, not by this drawing. Longer-cable timing remains a new bench
qualification item. Begin digital bring-up at reduced clock rates and measure
at both ends before using the final SPI3 schedule. Do not change the approved
J8.N to J9.(31-N) contact mapping to accommodate an unsuitable cable.

## Optical slider

Reserve a 50 x 60 opening in the base centred beneath Main's optical datum
(65.5,92.5). A removable, opaque matte target rides on two external slide rails
below the retained LM19-LSI lens. Provide 0-15 mm target-height adjustment in
0.1 mm steps with screws and shims. Set the final lens/target distance from the
received lens and its drawing; the adjustment range is not a claimed optical
operating range. Add a scale to measure target motion. The lens clip contacts
its retention shoulders only and keeps the optical surfaces and sensor
aperture free of adhesive. No PCB hole is inferred from the copper keepout.

## Motor, encoder and button experiments

Reserve the upper-right 100 x 100 base area for an independent slotted motor
bracket. Attach only to the stator mounting pattern of the exact received
GB1806 variant. The supplier provides a [motor drawing](https://islandcloud.co/link/69c5eb717e87e6e5cd073cc6/5299e636-5e71-45ad-96e0-71a6370926ea),
but the motor-only stock and purchased variant are not yet verified. Therefore
the bolt adapter is explicitly unfrozen; do not clamp the rotating bell.

Use an independently adjustable upright Encoder carrier, with axial slide,
height adjustment and tip/tilt shims. Centre U27 on the shaft magnet and set
the gap by the MA735 field indication and magnet specification. Mount the
encoder magnet mechanically before rotation; do not run an unsecured magnet.
Keep this magnet and the motor away from Hall experiments until interference
has been measured.

Each Hall test uses a removable bridge and screw-driven magnet carriage over
its existing sensor position. Add hard stops so neither magnet nor carrier can
strike the 1.1 x 1.4 mm sensor. Mount experimental coils/flexures independently
on the base and connect through J2/J3/J4. Document each coil resistance,
magnet orientation and travel before powered pulses. Final paddles, bearings,
middle-click travel and actuator gaps remain mechanical development work.

**Open before hardware use:** cable qualification, actual motor adapter,
optical lens retention/sample fit, measured support clearances and material
purchasing. This fixture drawing makes the test arrangement reviewable; it
does not certify an unbuilt mechanism.
