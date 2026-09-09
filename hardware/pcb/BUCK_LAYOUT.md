# First motherboard routing: 3.3 V buck

2026-09-09, KiCad 10.0.6. U2 and its local power components now have routed
copper in [MagMouse.kicad_pcb](../kicad/MagMouse.kicad_pcb). The motherboard is
partially routed; this is not a fabrication release or a powered validation.

## Placement and copper

The placement follows the current
[TI TPS6216x layout guidance, section 11](https://www.ti.com/lit/ds/symlink/tps62162.pdf):
keep the input loop compact, use a short switch-node connection, sense voltage
at an output capacitor and join the regulator grounds at the exposed pad.
This implementation still needs ripple, load-step, startup, EMI and temperature
measurements on hardware.

| Part | Centre X, Y (mm) | Rotation | Purpose |
| --- | --- | --- | --- |
| U2 | 145.5, 111 | 0 degrees | TPS62162 fixed 3.3 V buck |
| C1 | 142.9, 110.5 | 90 degrees | Local input bypass beside VIN/PGND |
| L1 | 149.4, 108.25 | 0 degrees | Inductor with short front-layer SW route |
| C2 | 152.7, 110.5 | 270 degrees | Output bypass at the inductor output |
| C3 | 149.5, 113.7 | 0 degrees | Output bypass and VOS sense endpoint |
| C23 | 144.65, 114.2 | 180 degrees | Additional output bypass |

These are the only six moved footprints. All 315 footprint identities, symbol
paths and pad nets are preserved. The 60 x 95 mm outline, optical/USB/ESP32
datums, mechanical keepouts, encoder project and motherboard project rules are
unchanged. All motherboard assembly components remain on the front.

- C1 connects to VIN/EN, with a short local return to PGND. Input copper widens
  to 0.4 mm after the 0.25 mm pin escape.
- SW stays on F.Cu without vias, with **3.95 mm total track length**. Its
  0.25 mm pin escape widens to 0.65 mm toward L1. The check uses a 5 mm local
  review budget; this is a project constraint, not a manufacturer limit.
- Output power uses 0.75/0.5 mm tracks. VOS has a separate 0.15 mm sense trace
  to C3's output pad, away from the SW route. The sense trace does not carry
  the downstream load current.
- PGND, AGND and the grounded fixed-output FB pin connect at U2's exposed-pad
  copper. Ground vias sit outside the exposed solder land. No filled or capped
  via-in-pad process is assumed.
- Local F.Cu and In1.Cu ground pours occupy X=141.8..154, Y=107.5..115.7 mm.
  They provide capacitor returns and local spreading copper; they are not yet
  the board-wide ground plane. Thermal performance is unmeasured.
- LOGIC_PG reaches R28 through a back-layer route. Its pull-up and the rest of
  the reset/power-good network still need routing.

This pass adds **37 track segments and 11 through vias** (0.60/0.30 mm).
Track widths are prototype choices; final power-path sizing and cooling remain
subject to copper stackup, load and temperature review.

## Verification

Physical DRC and schematic parity pass with **zero violations**, without new
exclusions. Native connectivity reports **775 unrouted connections**, down
from 790. The DRC JSON still lists 499 unconnected entries, which is not the
complete native connectivity count.

Run the normal PCB review with Python 3:

    python hardware/kicad/export_pcb_review.py

Run the copper checks with KiCad's bundled Python, which supplies `pcbnew`.
For the current Windows installation, from the repository root:

```powershell
$kicadPython = "$env:LOCALAPPDATA/Programs/KiCad/10.0/bin/python.exe"
& $kicadPython hardware/kicad/verify_buck_layout.py
& $kicadPython hardware/kicad/test_buck_layout_checks.py
```

The verifier traverses native copper connectivity, including filled zones;
matching schematic net names alone cannot pass it. It checks local supply,
switch, output/sense, ground and power-good connections, short front-only SW
copper and nearby ground vias. All three tests pass: the saved board baseline,
an opened SW route and an opened VOS route. Tests modify temporary PCB copies.
The report is `build/pcb-review/buck-layout-checks.json` and includes the board
hash. Use native DRC alongside this check; neither proves regulator operation.

## Next routing work

1. Refine U12 input-eFuse placement and route its local bypass, protection,
   control and current-limit connections; plan the USB-to-U12 and U12-to-buck
   power paths together.
2. Review the actuator eFuse, button bridges and wheel-driver hot loops and
   thermal paths. Keep current-sense and brake-control returns clear of these.
3. Select the JLCPCB stackup, calculate USB geometry, and route the protected
   USB path with its reference plane and ESD return.
4. Extend the ground reference and 3.3 V distribution, then route sensing and
   control. Recheck the buck return paths after adding surrounding copper.

The buck input is not yet connected to U12's output. Its output does not yet
power the motherboard loads. The partial PCB cannot operate as an assembled
mouse. Wheel/encoder support, cable access, optical sample fit and mounting
holes remain mechanical acceptance gates alongside electrical bench work.
