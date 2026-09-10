# Actuator enable and power-fault/reset routing

Review stage, 2026-09-09, KiCad 10.0.6. This follows the
[U13 local power pass](ACTUATOR_POWER_LAYOUT.md). The complete board and
interlock circuit remain partially routed; these connections alone do not
establish working protection or a usable mouse.

The subsequent [distribution pass](ACTUATOR_DISTRIBUTION_LAYOUT.md) completes
the remaining interlock copper and records the current counts. Results below
describe this earlier control-routing stage.

## Completed copper

- U16's ACT_DRIVE_EN output reaches D3's cathode, R49/R84 pull-downs, all four
  U17 enable inputs, both U18 enable inputs, U22's wheel gate input, U21's sleep
  input and TP13. Both pull-down ground returns are connected.
- U13 ACT_FAULT_N reaches R45. The existing U12 USB_FAULT_N connection to R44
  is retained. Both resistors' reset sides now reach the ESP32 MCU_EN pin.
- MCU_EN also reaches R28's power-good isolation branch, R3/C4, SW1, U18's
  sensor-enable gate input and TP6. R3 reaches the protected +3V3 rail; C4 and
  SW1 have ground returns. This completes the schematic's MCU_EN copper net.

R45 moved from (109.5, 113.5), rotation 0 degrees, to **(142, 145.75), rotation
90 degrees**, beside U13. C48 moved 0.25 mm right to **(147.25, 153.75)**,
retaining its 90-degree rotation, to leave room for U21's sleep-pin escape.
One CC_OUT2_INV bend was rerouted around U16's new enable escape; the existing
input-layout checker verifies that source-control connection still reaches U16.

The schematic, BOM, circuit values, outline, stackup and mechanical datums are
unchanged. There are still **317 motherboard footprints / 273 BOM parts**.
The common In1 ground reference remains filled. These are slow control routes;
full return-path, interference and powered fault-response review remain due.

## Verification

- Native connectivity: **651 unrouted connections**, down from 677.
- Physical DRC: **zero violations**, schematic parity: **zero issues**, with
  no new exclusions. The DRC JSON's 499 entries are not the full native count.
- Expanded actuator checker: all local power and control connections pass.
  Ten tests include deliberate opens in the input feed, output bypass, ILM,
  both sides of the disable clamp, actuator fault, MCU reset, reset pull-up
  supply and enable pull-down return, plus the passing baseline.
- Eight input and three buck tests also pass: **21 routing tests total**.
- The 33 new vias passed a sampled pad-intersection review on the saved board.
  This is a CAD review aid, not stencil or assembly acceptance.

Run the commands in [the U13 power review](ACTUATOR_POWER_LAYOUT.md#verification)
with KiCad's bundled Python. Also run `export_pcb_review.py`,
`verify_input_layout.py` and `verify_buck_layout.py`. Generated reports under
`build/pcb-review` contain the reviewed board hash.

## Remaining work

ACT_5V distribution to storage, TVS, button drivers, wheel driver and brake still
needs routing and power/thermal review. Complete the remaining interlock inputs,
gate supplies, watchdog, command and sensing connections before claiming the
hardware shutdown chain is complete. USB data, other signals and mechanical
fit remain open. No manufacturing files or assembly order were produced.
