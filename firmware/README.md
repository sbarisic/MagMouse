# Firmware

Target: ESP32-S3. Status: subsystem plan only; no build, flash command, device
drivers or USB implementation yet. Framework/toolchain selection is pending the
pin and timing feasibility work. Do not interpret this directory as runnable firmware.

## Planned responsibilities

| Subsystem | Responsibility |
| --- | --- |
| Board support | Validated pin map, rails, safe boot and recovery |
| Device drivers | PAW3950, ICM-42688-P, ADS7038, MA735, DRV8874 and DRV8316R |
| Input processing | Optical reports, calibrated Hall thresholds/hysteresis and wheel movement |
| Button control | Position/current feedback and bounded force effects |
| Wheel control | Encoder calibration, commutation/FOC and bounded detent torque |
| Power/fault manager | Source capability, total budget, hardware faults and stale-sample shutdown |
| USB HID | Three buttons, relative X/Y and wheel; target 1 ms report interval |
| Configuration | Versioned profiles, validation and persistence |
| Status | RGB indication for operating state and faults |

Bring up USB and sensing with actuators disabled first. Add one current-limited
coil, then the wheel, then combined power allocation. Firmware must enforce
limits regardless of values supplied by the PC application. Define explicit
uninitialized, ready, active and fault states with actuator-off reset behavior.

When implementation begins, add reproducible builds, host-testable control/power
logic, hardware integration checks and CI. USB VID/PID assignment, report layout,
control-loop rates and configuration transport are unresolved. Check redistribution
rights before adding optical-sensor firmware blobs or third-party motor libraries.

See [interfaces](../docs/interfaces.md), [power](../docs/power.md), and
[roadmap](../docs/roadmap.md). License: GPL-3.0-or-later; see [LICENSE](LICENSE).
