# Development roadmap

## 0. Repository foundation

- [x] Preserve original ideas and document the selected V1 direction.
- [x] Establish electronics, mechanical, firmware and host-software areas.
- [x] Record preliminary components, interfaces, power questions and license scope.
- [x] Select custom moving-magnet button actuators, elastic paddle return and
  DRV8231A drive in place of industrial actuators (2026-09-08; validation pending).

## 1. Schematic-level feasibility (next)

- [x] Start a KiCad 10.0.6 schematic with MCU, buck, button drivers, Hall/ADC
  circuits and catalog sourcing fields; see [the draft](../hardware/kicad/README.md).
- [ ] Obtain exact datasheets/reference circuits and confirm part availability.
- [ ] Validate PAW3950 optics, circuit, initialization and redistribution rights.
- [ ] Choose Type-C detection and complete input-power/protection design.
- [ ] Build one elastic-paddle/custom-coil fixture using the
  [button prototype plan](../mechanical/button-mechanisms/README.md).
- [ ] Measure passive return, bidirectional force/travel/current, winding properties,
  pulse response, heating and sensor crosstalk on a current-limited 5 V supply.
- [ ] Characterize the wheel motor at 5 V and validate its feedback acquisition.
- [ ] Demonstrate bounded button pulses and driver-off reset/timeout on development
  hardware before freezing the button schematic and magnetic placement.
- [ ] Assign every GPIO and confirm SPI, ADC, PWM and interrupt resources/timing.
- [x] Select KiCad and add a reproducible schematic review-export workflow.
- [ ] Choose firmware tools and document versions and reproducible workflows.
- [ ] Complete rail, connector, current-sense and fault-control schematics.

Exit: reviewed schematics, a verified pin/resource budget, and measured evidence
that the actuators can operate within the intended power and thermal envelope.

## 2. Mechanical and PCB prototype

- [ ] Model optical height, button travel/stops and actuator mounting.
- [ ] Validate separate sensing/actuator magnets and separation from wheel/coil fields.
- [ ] Select flexure material/print process and measure creep, fatigue and stop loads.
- [ ] Design shaft, bearings, encoder alignment and middle-click mechanism.
- [ ] Produce reviewed layout, ERC/DRC results, BOM and fabrication exports.

Exit: editable designs and a documented assembly/inspection procedure.

## 3. Firmware bring-up

- [ ] Establish build, tests and CI; verify recovery and actuator-off boot.
- [ ] Enumerate USB HID and validate optical X/Y and all three button inputs.
- [ ] Calibrate Hall sensing and coil current measurement one channel at a time.
- [ ] Calibrate force/current mapping by position and polarity; implement bounded
  press/release effects with no holding current and measured sleep/wake latency.
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
