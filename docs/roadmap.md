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
- [x] Resolve the starter's 17 missing catalog selections and six missing
  footprints; all 60 present BOM components now have MPNs, catalog IDs and
  footprints (revision 0.2; stock refresh and final circuit review remain).
- [ ] Obtain exact datasheets/reference circuits and confirm part availability.
- [ ] Validate PAW3950 optics, circuit, initialization and redistribution rights.
- [x] Implement Type-C detection and input/actuator power-control schematic
  (revision 0.3); see [power review](../hardware/kicad/POWER_REVIEW.md).
- [ ] Validate USB startup/configuration/suspend, source transitions, inrush,
  voltage/current limits, timeout/reset, reverse current and regeneration on hardware.
- [ ] Build one elastic-paddle/custom-coil fixture using the
  [button prototype plan](../mechanical/button-mechanisms/README.md).
- [ ] Measure passive return, bidirectional force/travel/current, winding properties,
  pulse response, heating and sensor crosstalk on a current-limited 5 V supply.
- [ ] Characterize the wheel motor at 5 V and validate its feedback acquisition.
- [ ] Demonstrate bounded button pulses and driver-off reset/timeout on development
  hardware before freezing the button schematic and magnetic placement.
- [x] Allocate all V1 GPIOs and static SPI/PWM/interrupt resources (revision 0.4):
  3-PWM wheel, dedicated second-ADC SPI and one-data-pin RGB; see [interfaces](interfaces.md).
- [ ] Prove PWM-to-ADC timing, valid low-side sampling windows, angle age and
  concurrent USB/button/optical operation on the selected firmware path.
- [x] Draw DRV8316 + ADC2 + MA735 + GB1806 wire interface, hardware output-disable,
  power-domain SPI isolation and a provisional autonomous brake (revision 0.5);
  see [wheel review](../hardware/kicad/WHEEL_REVIEW.md).
- [ ] Measure returned wheel energy and brake startup/overshoot/temperatures;
  validate or revise the resistor, capacitance and threshold selections.
- [ ] Obtain a verified optical sensor/lens source and exact PAW3950 circuit/optics
  evidence; see [optical review](../hardware/kicad/OPTICAL_REVIEW.md). JLC listing
  C9900186384 currently needs supplied parts; it is not purchasable stock.
- [x] Draw ICM-42688-P and addressable RGB with enabled supply and level buffer
  (revision 0.6); see [peripheral review](../hardware/kicad/PERIPHERAL_REVIEW.md).
- [ ] Qualify IMU shared-SPI/vibration and RGB voltage, timing and USB suspend current.
- [x] Select KiCad and add a reproducible schematic review-export workflow.
- [ ] Choose firmware tools and document versions and reproducible workflows.
- [ ] Complete rail, connector, current-sense and fault-control schematics.

Exit: reviewed schematics, a verified pin/resource budget, and measured evidence
that the actuators can operate within the intended power and thermal envelope.

## 2. Mechanical and PCB prototype

- [x] Start an editable motherboard PCB with the existing schematic footprints,
  provisional outline, four copper layers and subsystem reservations;
  see [placement draft](../hardware/pcb/README.md). Routing remains open.
- [x] Synchronize the wheel schematic to the PCB as 89 off-board staging footprints;
  preserve the original 183 placements. Mechanical fit is not established.
- [x] Stage 18 IMU/RGB footprints without moving the previous 272 placements.
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
