# PC configuration software

Status: scope only; no application, dependencies, build or installation workflow.
Choose supported operating systems and an application stack once the firmware
configuration protocol is defined.

Planned functions:

- Discover the mouse and display firmware/protocol compatibility.
- Configure button actuation thresholds and bounded haptic profiles.
- Configure wheel detent behavior and profile selection.
- Guide calibration and display power/fault state.
- Import/export versioned profiles with validation and explicit device writes.

Ordinary mouse input must work without this application. The device remains
responsible for current, thermal and source-power limits. Define units, ranges,
schema versioning, persistence and incompatible-profile behavior before UI work.
Configuration transport is TBD; do not assume a vendor HID or serial protocol yet.

License: GPL-3.0-or-later; see [LICENSE](LICENSE).
