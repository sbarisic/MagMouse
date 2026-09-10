# Development roadmap

## New mechanical and modular-board direction

The user confirmed a shaped PCB envelope of 125 mm length, 80 mm maximum
width and approximately 44 mm at the narrow end; the shell will be larger.
The requested manufacturing target is an assembled panel whose modules can
be separated at prepared tabs after delivery. See the
[modular panel brief](../hardware/pcb/MODULAR_PANEL_PLAN.md).

The [modular planning package](../hardware/modular/README.md) now contains native
125/80/44 mm main-board and daughterboard envelopes, a 147 x 135 mm provisional
panel nesting study, complete proposed reference ownership and a logical cable
pin map. Fresh netlists account for 241 main, 76 wheel and 3 encoder footprints;
all 17 main/wheel boundary nets are covered. The requested quote is for five
assembled sets delivered to Croatia 43000. Only a provisional bare-panel price
has been obtained; assembly and shipping remain unquoted.

Independent [main and wheel schematics](../hardware/modular/INTERFACE_REVIEW.md)
now include JLCPCB-listed signal/power headers and local disconnect bias. Both
pass ERC; the migration preserves 988 baseline pin connections and checks all
32 cable contacts. Counts including the added interface/local power are 246 main and 87
wheel footprints, plus the existing 3 encoder footprints.

Wheel-local [bulk storage, secondary TVS and discharge](../hardware/modular/LOCAL_POWER_REVIEW.md)
are now added: 140.4 uF nominal locally, with the 47 uF effective requirement
still subject to measured qualification. Nominal connected capacitor-only
startup load is 42.14 mA. Ten circuit regression tests pass.
The user accepts child-board damage after an internal cable disconnect for this
prototype. Assume fully connected internal cables; disconnect, partial-insertion
and open-return survival are outside acceptance. No extra wheel-feed protection
is required solely for these cases.
The [cable review](../hardware/modular/CABLE_REVIEW.md) corrected the physical
contact order: J8.N to J9.(31-N) for facing bottom-contact headers and a flat
same-side FFC. The candidate's mating tolerances still need closure before order.
The [wheel power and analog routing](../hardware/modular/WHEEL_ROUTING.md) now
connects local supplies, phases, autonomous brake and ADC2 sensing/reference
paths. All 87 footprints remain front-side on 55 x 60 mm. Filled In1 ground,
local returns and thermal vias are present. Native DRC/parity report zero issues
and 61 unconnected items, down from 233. Current-sense channels are front-only,
with complete saved In1 shadows and at least 1.785 mm from checked switching
copper. Five routing and four placement regression tests pass. These geometric
checks do not establish noise, thermal or regenerative-response acceptance.
Next, route ADC2 SPI3, configuration SPI, PWM/control/fault signals and remaining
logic supplies. Extend the board-specific checks before routing the larger main
PCB. SPI3's 20 MHz target still requires sampling validation.
Keep driver, ADC2 and autonomous brake together on the wheel board. A shared
panel requires a common stackup, including conversion of the encoder board.
The current 60 x 95 mm PCB and its review results remain the working baseline;
the copper split and manufacturing panel have not yet been implemented.
The outline-only planning files remain separate from the new editable wheel PCB.
Existing electrical and mechanical acceptance tasks below remain applicable
and must follow their circuits into the new boards.

## Current execution order

The actuator distribution, driver/brake current loops and interlock copper are
connected. Their electrical and thermal acceptance remains open. Use this order
for the remaining motherboard work:

1. Route/review analog current sensing: ADC2 SOA/SOB/SOC filters, button IPROPI,
   Hall outputs, VREF and power telemetry. Keep Hall and button-interface
   placement provisional; review local returns and separation from switching
   copper, and add useful boundary stitching.
   Close the non-mechanical `verify_analog_layout.py --require-reviewed` findings
   before continuing with general routing. Keep Hall geometry explicitly deferred.
   The saved In1 reference-shadow defects on fixed analog nets are corrected;
   wheel sense/phase separation, IPROPI/VREF locality and brake placement remain open.
   Redundant copper is removed from the fixed analog/brake routes, with
   connectivity and length regression checks. Control reroutes/branch cleanup
   remove five fixed proximity findings; 36 fixed findings remain open.
   Guard the cleared SOx/BTN_R_IN2 and SOC/BTN_R_IN1/DRV_INHC separations.
   Decide whether ADC2/filter/bypass placement may use the back side (two-sided
   assembly) before proceeding with that placement option.
2. Complete board-wide +3V3, PWR_5V, switched sensor rails and bypass returns.
   Audit necks, shared vias and shared actuator/logic/analog return paths.
3. Route SPI3/ADC2 first, then SPI2 and interrupts/faults/enables. Check branches
   and stubs for the 2 MHz PMW3360 and 10 MHz MA735 paths.
4. Review the optical layout separately: 3.3/1.9 V supplies, reset/SPI buffers,
   bypassing and the complete aperture/lens envelope. Retain the existing
   supplier/sample and optical-fit gates.
5. Inspect actual return paths on the substantially routed board, especially
   USB, ADC2/SPI3, optical, wheel current sensing, IMU and brake reference.
6. Review heat spreading and thermal vias for both eFuses, buck, motor drivers,
   brake MOSFET/resistors and exposed-pad devices. Measure combined-load heating.
7. Move to mechanical CAD before final placement freeze: mounting holes, GB1806
   support, shaft/bearings, upright encoder support, middle-click travel, cable
   bend/strain relief, lens/baseplate stack, USB opening, paddles, Hall magnets
   and actuator gaps. Avoid repeated refinement of placements that this work
   is likely to change.
8. Review manufacturing and assembled test access. Include VBUS/PWR_5V/ACT_5V,
   +3V3 and optical rails, Hall/ADC references, current outputs, phase pads,
   brake output/gate, USB and important fault/enable signals.

- [ ] Before final routing freeze, perform a whole-board electrical review for
  plane splits/crossings, long current loops, analog/PWM adjacency, power-via
  count, thermal restrictions, SPI stubs, USB reference continuity, test access,
  connector interference and parts covered by future wheel/button structures.
- [ ] Before ordering the final board, start a minimal firmware bring-up branch:
  actuator-off boot, USB HID, source detection, ADC1/Hall, optical X/Y, MA735,
  ADC2 phase readings, low-current commutation, then one bounded button pulse.
  Hardware behavior must be demonstrated on suitable development/prototype
  hardware; compilation alone is not architecture validation.

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
- [x] Widen driver current-path escapes and add local front/back ground spreading;
  screen 27 feed/output paths and protect thermal copper and capacitor inventory
  with [high-current regression checks](../hardware/pcb/HIGH_CURRENT_REVIEW.md).
- [x] Connect the 22 analog nets, including all Hall outputs; put ADC2 input
  filters on F.Cu, reconnect their returns and complete the ACT monitor capacitor
  return. Add [analog connectivity and geometry screening](../hardware/pcb/ANALOG_LAYOUT.md).
- [ ] Close the analog review findings: upstream SOx/phase proximity on In2/B,
  long right IPROPI, middle-button VREF and brake reference/gate placement.
  Fixed front-reference gaps are resolved. Hall geometry remains explicitly
  provisional. The analog `--require-reviewed` gate fails on 36 fixed findings;
  continuity passes.
- [ ] Confirm filled/capped U1/C32/U21 vias and affected lands/stencil with the fabricator;
  qualify current-path necks, combined actuator loading and brake/driver heating.
- [ ] Measure the long brake gate/reference paths, effective ACT capacitance,
  local VM droop and regeneration with the MCU held in reset; retain the
  provisional brake envelope until the measurements pass.
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
