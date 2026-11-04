# Firmware

Target: ESP32-S3. Status: subsystem plan only; no build, flash command, device
drivers or USB implementation yet. Framework/toolchain selection is pending the
timing feasibility work. The passive-button [GPIO/peripheral allocation](../docs/interfaces.md)
is checked against the schematic; runtime deadlines remain unproven.
Do not interpret this directory as runnable firmware.

The small-batch [button calibration contract](../docs/button-calibration.md)
uses secured magnets with measured released/pressed endpoints and hysteresis.
Precision matching of button magnets is not a Rev-A fabrication prerequisite.

## Planned responsibilities

| Subsystem | Responsibility |
| --- | --- |
| Board support | Validated pin map, rails, safe boot and recovery |
| Device drivers | PMW3360, ICM-42688-P, two ADS7038 devices, MA735 and DRV8316R |
| Input processing | Optical reports, calibrated Hall thresholds/hysteresis and wheel movement |
| Button control | Calibrated Hall thresholds and hysteresis; plastic mechanism supplies click and return |
| Wheel control | Encoder calibration, commutation/FOC and bounded detent torque |
| Power/fault manager | Source capability, total budget, hardware faults and stale-sample shutdown |
| USB HID | Three buttons, relative X/Y and wheel; target 1 ms report interval |
| Configuration | Versioned profiles, validation and persistence |
| Status | Single-data-pin addressable RGB through RMT; exact LED protocol pending |

Reserve MCPWM group 0 for wheel 3-PWM; group 1 is unallocated. SPI2 owns five shared devices; SPI3 serves only the wheel ADC.
Use one bounded owner per bus. Generic per-sample SPI API calls are not proof
of the required motor-current acquisition timing; measure the complete path.
Do not let a motor/LED library silently reallocate these resources.

Bring up USB and Hall sensing with the wheel disabled, then add current-limited
wheel control. Firmware must enforce wheel limits regardless of PC settings.
Define explicit uninitialized, ready, active and fault states with wheel-off
reset behavior. Buttons need no driver, PWM, coil-current feedback or haptic
profile. Calibrate each button's Hall thresholds against its plastic click and
release positions, then check for interference while the wheel runs.

The hardware heartbeat timeout still protects the motorized wheel. Implement
its startup, heartbeat and USB-state contract from [power](../docs/power.md).

When implementation begins, add reproducible builds, host-testable control/power
logic, hardware integration checks and CI. USB VID/PID assignment, report layout,
control-loop rates and configuration transport are unresolved. Check redistribution
rights before adding optical-sensor firmware blobs or third-party motor libraries.

See [interfaces](../docs/interfaces.md), [power](../docs/power.md), and
[roadmap](../docs/roadmap.md). License: GPL-3.0-or-later; see [LICENSE](LICENSE).
