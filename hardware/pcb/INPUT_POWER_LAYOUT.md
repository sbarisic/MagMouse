# Input power and source-selection routing

For the latest completed scope and remaining work, see the
[USB and compact ILM review](USB_LAYOUT.md).


2026-09-09, KiCad 10.0.6. This is a checked routing subset in
[MagMouse.kicad_pcb](../kicad/MagMouse.kicad_pcb), not a complete or qualified PCB.

The subsequent [Type-C pass](TYPEC_LAYOUT.md) completes the detector input and
source-selection supply connections. See that review for five further placement
changes; the table below records the original input-power pass.

## Completed copper

- Both reversible USB VBUS contact groups feed U12 through back copper. Each
  contact group has two through vias. The main input trunk is 1.5 mm wide.
- U12 input and output escape in opposite directions into three-via arrays.
  A 2.0 mm In2 protected-power trunk crosses in front of the wheel keepout and
  reaches the buck input capacitor C1. U12 is not bypassed by copper.
- C24 and D1 connect locally to the input. New **C88, 10 uF / 25 V, 0805**,
  connects at U12's output: Samsung CL21A106KAYNNNE, LCSC C15850, the same
  part used for C1. C1 is too far away to be U12's local output bypass.
- U12 UVLO, OVLO, dV/dt, fault-to-R44 and base/switched current-limit resistor
  branches are routed. Q1/Q2 source returns and gate pull-downs are connected.
- U11's capability outputs reach R26/R27 and U14. SOURCE_OK reaches Q1,
  R62 and U16 pins 1/9; SOURCE_3A reaches Q2/R63; CC_OUT2_INV reaches U16.
  U14 connects to its bypass C32. These are partial logic connections;
  the subsequent Type-C pass completes the detector and source-selection supplies.
- A filled In1 GND plane now spans the board while respecting the existing
  wheel, optical and antenna keepouts. The local buck ground pours remain.
  This does not establish a continuous return path for every future signal.

All added vias are 0.60 mm copper / 0.30 mm drill. This original pass did not assume filled/capped vias. The later USB pass
requires them at U1 and C32; see [current fabrication notes](USB_LAYOUT.md). Short U12 pin escapes use 0.25 mm copper before widening;
the suggested Power netclass width is not a current-capacity guarantee.

The placement changes from the buck-only draft are:

| Reference | Centre X, Y (mm) | Rotation |
| --- | --- | --- |
| U12 | 108.25, 110 | 0 degrees |
| C24 | 105.95, 107.75 | 270 degrees |
| C25 | 112, 111.75 | 0 degrees |
| D1 | 102, 104 | 180 degrees |
| J6 | 113, 103.5 | 180 degrees |
| C88, added | 111.6, 107.9 | 0 degrees |

J6 now mates toward the front edge, minus Y. Check the plug, strain relief,
bend radius and shell access there. The harness pin numbering is unchanged.
The USB, optical and ESP32 datums, outline and encoder board are preserved.
At completion of this pass there were **316 motherboard footprints and 272 BOM parts**.
See [the U13 pass](ACTUATOR_POWER_LAYOUT.md) for current counts.

## Electrical review still required

[TI TPS25947 Rev. C, section 8.4](https://www.ti.com/lit/ds/symlink/tps25947.pdf)
calls for close bypass and setting components, short/wide power paths,
thermal spreading, quiet ground returns and less than 50 pF at ILM.
C88 addresses the local output-capacitor requirement, but this routing pass
does not establish full compliance with that layout guidance.

The [subsequent USB pass](USB_LAYOUT.md) compacts the current-limit network:
USB_ILM falls from 54.094 to 22.935 mm, and setting/input/test pads are within
8.990 mm of U12.9. U19/TP14 and buffered ADC telemetry are connected.
The total ILM parasitic capacitance and coupling still need calculation or
measurement. A common GND net does not by itself prove a quiet analog return.

Review current density, all neck-downs, via sharing and copper temperature at
maximum load and fault conditions. Validate input inrush, local capacitor
effective capacitance, eFuse stability/temperature, source transitions,
reverse blocking, suspend and fault/reset behavior on hardware.

## Verification and remaining routing

Native physical DRC and schematic parity pass with zero violations and no new
exclusions. Copper connectivity is **698 unrouted connections**, reduced from
775 in the buck-only draft. DRC JSON returns only 499 unconnected entries;
that list length is not the complete native count.

From the repository root, with KiCad's Python:

```powershell
$kicadPython = "$env:LOCALAPPDATA/Programs/KiCad/10.0/bin/python.exe"
& $kicadPython hardware/kicad/verify_input_layout.py
& $kicadPython hardware/kicad/test_input_layout_checks.py
& $kicadPython hardware/kicad/verify_buck_layout.py
& $kicadPython hardware/kicad/test_buck_layout_checks.py
python hardware/kicad/export_pcb_review.py
```

The input verifier traverses actual copper and filled zones. Eleven test methods check
the saved board and deliberate opens in the protected feed, C88 connection,
current-limit node, buffer/ADC telemetry, excessive ILM length, source command,
CC1, detector supply and sink-mode ground.
The three existing buck tests still
pass. Reports under `build/pcb-review` include the exact board hash. Run DRC
alongside the connectivity check; the latter is not a short-circuit detector.

The counts above record this earlier routing pass. See [USB_LAYOUT.md](USB_LAYOUT.md)
for the current board: input/actuator distribution, interlocks, buffered input
telemetry and USB data are now checked. Full-board signal routing, mechanical
fit, thermal/ILM measurements and fabrication preparation remain open.
This partial board cannot function as an assembled mouse.
