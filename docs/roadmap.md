# Development roadmap

## 0. Repository foundation

- [x] Preserve original ideas and document the selected V1 direction.
- [x] Establish electronics, mechanical, firmware and host-software areas.
- [x] Record preliminary components, interfaces, power questions and license scope.

## 1. Schematic-level feasibility (next)

- [ ] Obtain exact datasheets/reference circuits and confirm part availability.
- [ ] Validate PAW3950 optics, circuit, initialization and redistribution rights.
- [ ] Choose Type-C detection and complete input-power/protection design.
- [ ] Characterize one voice coil and wheel motor on a current-limited bench supply.
- [ ] Assign every GPIO and confirm SPI, ADC, PWM and interrupt resources/timing.
- [ ] Choose firmware/CAD tools and document versions and reproducible workflows.
- [ ] Complete rail, connector, current-sense and fault-control schematics.

Exit: reviewed schematics, a verified pin/resource budget, and measured evidence
that the actuators can operate within the intended power and thermal envelope.

## 2. Mechanical and PCB prototype

- [ ] Model optical height, button travel/stops and actuator mounting.
- [ ] Validate magnet geometry and separation from motor/voice-coil fields.
- [ ] Design shaft, bearings, encoder alignment and middle-click mechanism.
- [ ] Produce reviewed layout, ERC/DRC results, BOM and fabrication exports.

Exit: editable designs and a documented assembly/inspection procedure.

## 3. Firmware bring-up

- [ ] Establish build, tests and CI; verify recovery and actuator-off boot.
- [ ] Enumerate USB HID and validate optical X/Y and all three button inputs.
- [ ] Calibrate Hall sensing and coil current measurement one channel at a time.
- [ ] Bring up wheel sensing, commutation and bounded torque control.
- [ ] Integrate source-aware power allocation and fault/suspend paths.
- [ ] Measure report timing and control latency under combined load.

Exit: a usable mouse with documented calibration and measured fail-safe behavior.

## 4. Profiles and host configuration

- [ ] Define a versioned configuration protocol and validated parameter ranges.
- [ ] Implement persistence and a PC application with firmware-enforced limits.
- [ ] Document calibration, assembly, supported power sources and release checks.

Wireless, batteries, custom power-adapter hardware and additional features are
deferred until the wired prototype works.
