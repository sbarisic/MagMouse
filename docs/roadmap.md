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
- [ ] Validate selected PMW3360/LM19-LSI optics, circuit, initialization and SROM usage rights.
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
- [x] Compare alternative optical sensors and identify retail sample leads;
  [selection review](../hardware/kicad/OPTICAL_SELECTION.md) recommends
  PMW3360DM-T2QU + LM19-LSI, with PAW3395 as a higher-performance alternative.
- [x] Implement PMW3360 local supplies, buffered SPI/reset and custom footprint
  (revision 0.7); document lens stack and startup/scheduling requirements in
  [optical design](../hardware/kicad/OPTICAL_DESIGN.md).
- [ ] Confirm sample delivery, sensor/lens identity, authorized SROM and assembly
  acceptance; [supplier inquiry](optical-sample-inquiry.md) is prepared but not sent.
- [ ] Measure optical supply ramps, startup/suspend current, power-off isolation,
  tracking and bounded motion-burst scheduling between encoder reads.
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
- [x] Add PMW3360/LM19-LSI [vertical datums and aperture dimensions](../mechanical/optical/README.md).
- [x] Stage 26 optical footprints while preserving all previous 290 placements.
- [x] Adopt PCB-first mechanical development and provisionally place U35; the
  shell will follow the board, lens height and wheel/button interfaces.
- [x] Place all 25 optical support footprints around U35; preserve other components
  and pass physical DRC/parity. See [placement review](../hardware/pcb/OPTICAL_PLACEMENT.md).
- [x] Widen the provisional motherboard to 60 x 95 mm and place the remaining
  motherboard electronics (314 footprints); retain U27/C62 as encoder-board
  planning parts. See [placement review](../hardware/pcb/PLACEMENT_60MM.md).
- [x] Select a separate upright MA735 encoder board for the horizontal wheel axle.
- [x] Implement the [encoder board/interconnect](../hardware/encoder/README.md):
  JST SH headers, separate schematic/BOM, checked harness and fully routed
  provisional 14 x 18 mm board; ERC/DRC/parity and connectivity pass.
- [ ] Verify encoder support, shaft/magnet alignment, connector/cable clearances,
  power-off behaviour and 10 MHz cable waveforms on the actual assembly.
- [x] Refine and route the local 3.3 V buck, output sense and ground returns;
  [native copper checks](../hardware/pcb/BUCK_LAYOUT.md), physical DRC and parity pass.
- [x] Route USB-to-U12 and U12-to-buck power, add local output bypass C88,
  route local protection/current-limit and source-selection logic; see
  [input copper checks](../hardware/pcb/INPUT_POWER_LAYOUT.md).
- [x] Route [Type-C CC/ESD/VBUS inputs, local returns and detector/source-logic
  supplies](../hardware/pcb/TYPEC_LAYOUT.md); native copper and DRC checks pass.
- [ ] Finish remaining board supplies/signals; quantify ILM parasitics and
  switching pickup, and review power necks and heat.
- [x] Select the [JLCPCB stackup and USB geometry](../hardware/pcb/STACKUP.md):
  JLC041611-2116, 1 oz inner/outer, calculated 90-ohm pair dimensions.
- [x] Compact U12 ILM settings and buffer/test branch; route buffered input-current telemetry.
- [x] Route [USB with ESD return and continuous In1 reference](../hardware/pcb/USB_LAYOUT.md);
  add saved-copper continuity, geometry, plane-void and ESD regression checks.
- [ ] Obtain manufacturer acceptance of the exact stackup, 90-ohm impedance and
  filled/capped U1, C32 and U21 vias; validate USB electrically on hardware.
- [x] Route U13's local feed, bypass, voltage dividers, ramp, current limit and
  D3 anode; see [actuator power review](../hardware/pcb/ACTUATOR_POWER_LAYOUT.md).
- [x] Route actuator enable fanout, U13 fault and the power-fault/reset network,
  including reset pull-up and enable pull-down returns; see
  [control routing review](../hardware/pcb/ACTUATOR_CONTROL_LAYOUT.md).
- [x] Route actuator distribution/storage, button/BLDC current loops, sensing
  and brake power; complete remaining interlock inputs and gate supplies. See
  [distribution routing and checks](../hardware/pcb/ACTUATOR_DISTRIBUTION_LAYOUT.md).
- [ ] Confirm filled/capped U1/C32/U21 vias and affected lands/stencil with the fabricator;
  qualify current-path necks, combined actuator loading and brake/driver heating.
- [ ] Complete signal routing, ground stitching and return-path review.
- [ ] Refine complete-board placement for routing, thermal paths and analog/SPI
  return paths; verify physical assemblies and allocate mounting holes.
- [ ] Fit optical samples/coupon and freeze lens retention, base/feet, PCB opening
  and mounting heights; model button travel/stops and actuator mounting.
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
