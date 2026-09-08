# Firmware

Target: ESP32-S3. Status: subsystem plan only; no build, flash command, device
drivers or USB implementation yet. Framework/toolchain selection is pending the
timing feasibility work. The revision 0.4 [GPIO/peripheral allocation](../docs/interfaces.md)
is checked against the schematic; runtime deadlines remain unproven.
Do not interpret this directory as runnable firmware.

## Planned responsibilities

| Subsystem | Responsibility |
| --- | --- |
| Board support | Validated pin map, rails, safe boot and recovery |
| Device drivers | PAW3950, ICM-42688-P, two ADS7038 devices, MA735, DRV8231A and DRV8316R |
| Input processing | Optical reports, calibrated Hall thresholds/hysteresis and wheel movement |
| Button control | Position/current feedback and bounded bidirectional click/release pulses; elastic paddle supplies passive return |
| Wheel control | Encoder calibration, commutation/FOC and bounded detent torque |
| Power/fault manager | Source capability, total budget, hardware faults and stale-sample shutdown |
| USB HID | Three buttons, relative X/Y and wheel; target 1 ms report interval |
| Configuration | Versioned profiles, validation and persistence |
| Status | Single-data-pin addressable RGB through RMT; exact LED protocol pending |

Reserve MCPWM group 0 for wheel 3-PWM and group 1 for six independent button
commands. SPI2 owns five shared devices; SPI3 serves only the wheel ADC.
Use one bounded owner per bus. Generic per-sample SPI API calls are not proof
of the required motor-current acquisition timing; measure the complete path.
Do not let a motor/LED library silently reallocate these resources.

Bring up USB and sensing with actuators disabled first. Add one current-limited
coil, then the wheel, then combined power allocation. Firmware must enforce
limits regardless of values supplied by the PC application. Define explicit
uninitialized, ready, active and fault states with actuator-off reset behavior.

The custom actuator needs a measured force/current map across position and both
polarities. Firmware commands only the added haptic force; it does not generate
the paddle's baseline spring force. Account for direction changes, current decay
and valid ADC sampling windows rather than assuming current follows PWM instantly.
Calibrate sensing with coil and wheel interference present.

Use explicit per-effect duration, duty/repeat-rate and current limits, with zero
commanded coil current after an effect and while held at rest. Include driver
wake latency in click timing and use the actual IN1/IN2 controls documented in
[interfaces](../docs/interfaces.md). The revision 0.3 schematic gates commands
with a hardware heartbeat timeout. Implement its startup, heartbeat and USB-state
contract from [power](../docs/power.md); do not assume button-driver fault telemetry
is available.

When implementation begins, add reproducible builds, host-testable control/power
logic, hardware integration checks and CI. USB VID/PID assignment, report layout,
control-loop rates and configuration transport are unresolved. Check redistribution
rights before adding optical-sensor firmware blobs or third-party motor libraries.

See [interfaces](../docs/interfaces.md), [power](../docs/power.md), and
[roadmap](../docs/roadmap.md). License: GPL-3.0-or-later; see [LICENSE](LICENSE).
