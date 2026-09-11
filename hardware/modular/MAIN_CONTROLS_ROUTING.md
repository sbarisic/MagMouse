# Main source controls, actuator power and interlocks

2026-09-11. The shaped [Main PCB](main/Main.kicad_pcb) now has its Type-C/source
controls, U13 actuator distribution, button commands/coil outputs and main-side
interlocks routed. This original subset pass reduced native unrouted count
from **564 to 257** without moving footprints. The subsequent
[signal/return pass](MAIN_SIGNAL_ROUTING.md) brings the board to **zero unrouted**,
with zero physical DRC/parity issues. Its analog/test-pad placement changes are
recorded separately; Hall/button mechanical interfaces remain provisional.

## Completed copper

- J1 CC1/CC2 reach U20 protection and U11 detection. CC2 uses In2 for the
  connector-to-protection crossing, leaving the front USB data corridor free.
  Source capability, VBUS detection and source/current-limit controls are
  connected. Both R25 sensing and R65 monitor supply connect to USB VBUS.
- U13's local UVLO/OVLO, ILM and dVdt networks are connected. ACT_5V reaches
  all three button drivers and J10, the wheel power header. The J10 branch has
  a 2 mm B.Cu trunk, local 0.8 mm header copper and three 0.60/0.30 mm vias at
  each power/ground header handoff. The local C40 output handoff also has three.
- Button-driver front/back ground spreaders and four local thermal vias per
  driver are retained. All six coil-output connections reach J2/J3/J4. Their
  routing remains subject to future actuator/connector placement changes.
- Reset, source qualification, arm/request, watchdog heartbeat, permit and
  button command/enable logic are connected. Main-side wheel enable, run request
  and fault return reach J8/U25. All fifteen J8 ground contacts have returns;
  its logic supply is connected. SPI and PWM header signals are now complete in the signal-routing pass.
- The MCU exposed ground lands are joined by a front copper mesh with a return
  to In1. No tracks occupy In1; its saved ground fill remains one connected
  outline around the mechanical and antenna keepouts. This is a connectivity
  result, not acceptance of every signal's reference path.

Matching local copper from the monolithic board was reused selectively. Branches
that conflicted with the moved ADC1, outline or headers were removed and rerouted.
The earlier input-power and buck checks still pass. Neither the wheel PCB nor
the original monolithic PCB changed.

## Screening and regression checks

[verify_main_controls.py](verify_main_controls.py) checks 51 complete nets,
134 ground pads, 25 logic-supply pads, eleven resistance paths, local power-via
arrays and driver ground spreading. The [saved report](main-controls-review.json)
records the exact board hash and individual results.

| Path | Resistance screening | Regression ceiling |
| --- | ---: | ---: |
| U12 output to U13 input | 35.434 mOhm | 50 mOhm |
| U13 output to left driver | 66.499 mOhm | 85 mOhm |
| U13 output to middle driver | 60.596 mOhm | 85 mOhm |
| U13 output to right driver | 48.131 mOhm | 85 mOhm |
| U13 output to wheel power header | 26.347 mOhm | 50 mOhm |
| Six button output paths | 7.501–15.841 mOhm | 25 mOhm each |

These use the existing 80 C conductor/barrel model, without credit for parallel
copper. They exclude components, contacts, pad resistance, ground-plane impedance
and inductance. They do not establish ampacity, temperature rise, source transition
behavior, reset/watchdog timing or hardware acceptance.

Seven focused tests cover the saved routing, an open CC detector, open wheel
enable, lost VBUS monitor supply, narrowed wheel feed, insufficient header vias
and a missing driver ground spreader. The original subset suite contained 38 modular regression tests; the signal-routing
pass extends it with analog, USB and return-path fault injection.

The main project now permits **0.45/0.20 mm signal vias**, with a 0.125 mm minimum
annular ring, matching the wheel's fine-escape geometry. Power arrays remain
0.60/0.30 mm. Track clearance and copper-to-edge rules are unchanged. The new
U25 pin 12 via is in the pad; include it in the filled/capped via manufacturing
review. This pass does not settle that assembly process or its cost.

```powershell
kicad-cli pcb drc --format json --schematic-parity --output build/modular/main-drc.json hardware/modular/main/Main.kicad_pcb
python hardware/modular/verify_main_controls.py --board hardware/modular/main/Main.kicad_pcb --output hardware/modular/main-controls-review.json
python -m unittest discover -s hardware/modular -p test_main_controls_checks.py
```

Use KiCad's bundled Python. Native DRC/parity and the separate input-power,
placement and stack checks remain required alongside the focused audit.

## Next work

Analog, USB, SPI3, SPI2/optical, remaining controls and board-wide 3.3 V/ground
routing are complete in the [signal/return pass](MAIN_SIGNAL_ROUTING.md).
Preserve the [mechanical interface register](MECHANICAL_INTERFACES.md).
Mechanical CAD and PCB adjustments, whole-board review, encoder stack migration
and manufacturing review must precede panelization. No order package is released.
