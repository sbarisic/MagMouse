# Main input-power routing

2026-09-11. The shaped [main PCB](main/Main.kicad_pcb) now has its USB VBUS
feed, U12 passive protection/current-limit network, local current-buffer
supply/feedback and buck copper routed. Native unrouted count is **564**, down
from 632 at placement. Physical DRC and schematic parity both report zero
issues. The main remains a partially routed board.

## Completed scope

- Both reversible J1 VBUS contact groups use two 0.60/0.30 mm through vias.
  A new 1.5 mm B.Cu feed reaches the U12 input array from the relocated USB-C
  connector. J1 ground contacts and shell have local returns to In1.
- U12's input and protected output each retain three 0.60/0.30 mm power vias.
  Its 2.0 mm In2 trunk reaches C1 and the buck. C24 and C88 remain local to
  U12; their supply-pad distances from the corresponding eFuse pads are
  3.654 and 3.005 mm. D1 and the UVLO/OVLO/divider/dVdt networks are connected.
- The compact ILM resistor/switch branches and U19 input are connected.
  USB_ILM retains **22.935 mm** total copper and an **8.990 mm** maximum
  setting/input-pad radius. U19 has local feedback and powered bypass C34.
  Its buffered ADC telemetry output still awaits the analog routing pass.
- The buck retains its local input/output capacitor loops, output-sense route,
  ground spreading and **3.950 mm front-only switch connection**, without a
  switch-node via. Its local power-good connection reaches R28.
- One saved In1 GND outline spans the shaped board around its mechanical/RF
  keepouts. No signal or power tracks occupy In1. Thirty local ground pads,
  including connector shields, capacitor returns and regulator ground pads,
  are checked for connectivity to that reference.

The fixed local U12/buck copper was selectively carried over from the earlier
motherboard after checking the matching component geometry and net names.
USB feed and U19 supply distribution were rerouted for this board. Unused
branches were removed. No footprint positions, schematic values, project DRC
rules, wheel copper or panel-study files changed.

## Copper screening

The shared track/barrel model assumes 80 C copper, 35 um outer/30 um inner
copper and 20 um barrel plating. It counts complete traversed segments and
barrels, without credit for parallel copper. These are conservative regression
figures for the modelled conductors, not measured complete-path resistance,
ampacity or temperature predictions.

| Path | Screening resistance | Regression ceiling |
| --- | ---: | ---: |
| Either J1 VBUS group to U12 input | 21.020 mOhm | 40 mOhm |
| U12 output to C88 | 14.499 mOhm | 20 mOhm |
| U12 output to C1 | 20.387 mOhm | 40 mOhm |
| U12 output to either buck supply pin | 23.400 mOhm | 45 mOhm |

The model excludes components, connector contacts, solder, pad resistance,
ground-plane impedance and inductance. It does not establish eFuse/regulator
stability or USB startup compliance. ILM length and radius likewise do not
establish parasitic capacitance or coupling. Those reviews remain open.

## Validation and next routing

[verify_main_power.py](verify_main_power.py) checks twelve complete local nets,
the defined supply endpoints, U19 feedback/supply, power via arrays, saved
ground connections, ILM geometry and six resistance paths. It reuses the
existing local buck checker and stackup model. The
[saved review](main-power-review.json) includes the exact PCB hash.
Seven tests exercise the saved board, an open output capacitor, insufficient
input vias, a power neck-down, a missing ground reference, a disconnected ILM
input and a switch-node via.

Type-C/source-selection commands, interlocks, actuator power, board-wide
3.3 V, ADC telemetry, USB data and digital buses remain unrouted or incomplete.
The next power pass should complete the detector/source controls and U13/button/
wheel-feed distribution before the analog and USB data passes. Reserve the
selected 90-ohm USB geometry and continuous In1 return corridor when placing
additional vias. A connected subset does not make the board operable.

Mechanics remain provisional by the user's explicit choice. See the
[interface register](MECHANICAL_INTERFACES.md). Panelization stays on hold.

```powershell
kicad-cli pcb drc --format json --schematic-parity --output build/modular/main-drc.json hardware/modular/main/Main.kicad_pcb
python hardware/modular/verify_main_power.py --board hardware/modular/main/Main.kicad_pcb --output hardware/modular/main-power-review.json
python -m unittest discover -s hardware/modular -p test_main_power_checks.py
```

Use KiCad's bundled Python for these checks.
