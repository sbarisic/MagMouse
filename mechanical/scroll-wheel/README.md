# Scroll wheel mechanics

Use the GB1806 with its integrated AS5048A magnetic encoder. The separate
magnet-axis PCB, independent encoder magnet and upright mount are removed.
The motor, wheel, shaft and bearings still need physical fit confirmation.

Reserve editable CAD here. Obtain the selected encoder-equipped motor drawing
and check its shaft, overall length, mounting holes, wheel clearance and cable
strain relief. Do not use encoder-free motor dimensions as an assembly envelope.

Wire motor phases to Wheel J5 and encoder signals to Lower J6 as specified in
[encoder integration](../../hardware/two-layer/sandwich/ENCODER_INTEGRATION.md).
Verify direction, seven pole pairs, electrical zero, full-turn angle continuity
and diagnostics before applying haptic torque. A built-in encoder removes the
separate alignment fixture; it does not establish measured system performance.
