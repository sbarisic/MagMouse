# Button mechanisms

Selected direction as of 2026-11-04: three passive plastic click mechanisms,
with Hall sensors and sensing magnets. No button coils, powered actuators or
separate actuator magnets are required. The motorized scroll wheel remains.

Each left, middle and right assembly needs:

- A plastic mechanism that creates the tactile click and returns on release.
- One secured moving sensing magnet aligned with a fixed TMAG5253 Hall sensor.
- Mechanical travel stops and clearance from the sensor and PCB.

The click force and feel come from the plastic geometry. Firmware reads the
Hall position through ADS7038 and applies calibrated press/release thresholds
and hysteresis. Software does not change the physical click force.

The active Upper board retains U7/U8/U9 and ADC U10. J2/J3/J4 and the three
DRV8231A circuits have been removed. Existing Hall positions remain the layout
anchors; plastic travel, magnet spacing and stack height still need dimensioned
CAD and physical fitting. The middle mechanism must also clear the wheel assembly.

Next model one plastic mechanism around these interfaces and establish its
travel, snap/release points and stops. Use the [calibration procedure](../../docs/button-calibration.md)
to align electrical button transitions with the physical click. Check return,
repeatability and Hall readings with the wheel running before duplicating it.
No dimensioned plastic mechanism or physical validation is claimed yet.

The [previous electromagnetic concept](archive/electromagnetic-concept.md) is
retained as historical reference only.

Hardware/mechanical: CERN-OHL-S-2.0. Documentation: CC-BY-SA-4.0.
