# Rev-A button calibration

This is the bring-up contract, not implemented firmware. Magnets are secured
to their moving levers; their exact field strengths do not need to match.
Keep the Hall IC positions, passive return and physical end stops. Optical
height and wheel encoder alignment are independent mechanical requirements.

## Capture and conversion

With all actuators disabled, calibrate each of the three buttons separately.
Record at least 0.5 seconds of stationary ADC samples at released and fully
pressed positions. Store the mean and standard deviation of each capture,
the raw minimum/maximum, sample count and acquisition settings. Repeat each
endpoint three times to check the mount and stop repeatability.

Let `R` be the released mean and `P` the pressed mean. Calculate
`position = (raw - R) / (P - R)`. Either sign of `P - R` is valid. The
result is normalized sensor travel, not a linear displacement measurement.
Preserve the raw reading and unclamped result for diagnostics; clamp to 0..1
only for normal button processing.

Reject zero/invalid span, ADC or Hall clipping, unstable endpoints and a span
smaller than ten times the larger endpoint standard deviation. Use one ADC
count as the minimum noise estimate when a capture quantizes to a constant.
Endpoint repetitions must agree within 5% of the span. These are provisional
bench acceptance thresholds and should be recorded alongside the calibration.

Sweep the complete physical travel slowly. Reject reversals, saturation or
mechanical contact with the sensor. Two endpoint measurements cannot correct
a non-monotonic field or a loose magnet. Repeat the sweep after the fixture
has been disturbed and after the first heating tests.

## Button state and persistence

Start with press at 0.60 and release at 0.40. Retain the previous state between
thresholds. Initialize to released with haptics disabled until valid readings
and calibration are available. A pressed startup position must not trigger
an automatic haptic pulse.

Persist a versioned record per button and physical unit containing endpoints,
noise, polarity, capture settings and thresholds. Validate finite values,
nonzero span, threshold order and record integrity when loading. An invalid
record leaves that button/haptic channel disabled and reports calibration
required; unrelated optical/USB diagnostics may continue. Recalibration is an
explicit action, never silent adaptation to a held button.

## Powered verification

Verify repeated clicks, slow travel and resting noise first. Then operate one
coil at a time, the wheel alone and the combined mechanisms with bounded
current. Record false transitions and sensor disturbance at both endpoints
and around the thresholds. Static calibration does not cancel time-varying
actuator fields or establish a force/current map. Correct excessive physical
interference before accepting the device; do not hide it by silently moving
thresholds. Verify passive release with power removed.

No firmware implementation, final paddle mechanics or hardware acceptance is
claimed by this procedure.
