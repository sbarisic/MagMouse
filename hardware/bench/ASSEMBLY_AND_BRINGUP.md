# Rev-A self-assembly and bring-up

This is a bench prototype with U32 deliberately omitted. Preserve all power
protection, brake, driver, ADC and interface parts. Match the purchasing variant
to the generated reference map; R25 uses the documented Vishay substitute.

## Equipment and preparation

The user supplies tools: temperature-controlled reflow for at least an
individual 125 x 80 mm board, magnification, fine tweezers, soldering iron,
hot-air rework, temperature probe, multimeter and current-limited bench supply.
A scope is needed for USB reference, rail ramps, SPI timing and brake tests;
it is not replaced by a continuity meter. Fresh paste, flux, wick and cleaning
supplies remain consumables in the project budget. Follow the chosen paste
and each part's moisture/reflow limits, not a universal temperature recipe.

Practice printing, placing and reflowing a fine-pitch/hidden-pad exercise board
first. Inspect the paste before placing expensive parts. Do not rely on an
iron alone for underside joints. Optical inspection cannot prove every hidden
joint is wetted; abnormal current or temperature requires investigation.

## Assembly sequence

1. Support and cut each bare board from the panel. Keep cutting dust away from
   contacts, inspect the cut edge and clean before paste application. Remove
   residual tab material without cutting inside the unit's original outline.
2. Hold each unit flat in a room-temperature stencil jig. Use the matching
   region of the shared stencil and cover the unused regions. Align with pad
   outlines/pin-one drawing; prevent stencil motion during the single print.
3. Inspect for bridges and insufficient deposits. Populate the small hidden-pad
   parts first, then passives and remaining reflow-qualified parts. Keep U32
   empty. Confirm IC/diode/LED/capacitor orientation against the annotated
   drawing and package marking before reflow.
4. Reflow one unit at a time using a measured profile. Verify connectors and
   the polymer capacitor are within their specific reflow limits. Solder USB
   shell anchors and any intended hand-solder joints separately as needed.
5. Fit PMW3360 after other soldering/cleaning. Keep the sensor aperture protected
   until lens fitting; use its specified lead-soldering process. Do not put the
   sensor or lens through a generic board reflow profile. Fit the matching lens
   and clean only by the optical manufacturer's permitted method.

## Bring-up gates

Record supply voltage/current, firmware version, observations and pass/fail
for each gate. Power off before changing internal cables or test wiring.

| Gate | Check and stop condition |
| --- | --- |
| Unpowered | Inspect polarity/hidden-pad alignment, resistance between every rail and GND, cable continuity and no adjacent-contact shorts. Investigate unexpected low resistance before power. |
| Logic supply | Motor and coils disconnected. Feed through the intended protected power entry with a suitable current-limited USB/source fixture. Verify logic rails and actuator-off reset defaults; do not inject a bench supply backwards into an attached host. Stop on current limiting, incorrect rail voltage or rapid heating. |
| USB | Enumerate repeatedly with actuators off. Exercise movement reports and reconnects on more than one host/cable. No paid impedance service means no guaranteed 90-ohm acceptance. |
| ADC1/Hall | Verify references and idle readings, then move one magnet at a time with mechanical stops. Record noise before any PWM activity. |
| Optical | Verify both rail ramps, correct product identity and permitted SROM initialization. Measure X/Y against the slider scale at the received lens's specified working height. |
| Encoder/ADC2 | Confirm angle direction, magnetic-field range, ADC references and idle phase readings. Check buffered SPI at both boards, starting slowly; do not assume the longer bench cable meets the final control-loop schedule. |
| Motor/brake | Secure motor and encoder first. Use bounded low-current commands and the design's source-current budget. Measure phase-current offsets and brake behavior, rail rise and temperatures before increasing torque. Never drive the motor with unverified current feedback. |
| Button pulses | Connect one measured coil at a time. Start with bounded short, low-current pulses and cool-down intervals. Verify current feedback, hard stops and temperature before combining channels. |

Specific operating limits must come from the implemented bring-up firmware,
coil/motor measurements and existing electrical contracts. This document does
not invent a safe drive current or certify the hardware before it exists.
