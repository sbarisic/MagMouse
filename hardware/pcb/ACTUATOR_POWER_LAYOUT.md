# U13 local actuator-power routing

Review stage, 2026-09-09, KiCad 10.0.6. The motherboard remains partially routed.
This pass follows the [input-power](INPUT_POWER_LAYOUT.md) and
[Type-C](TYPEC_LAYOUT.md) passes. It does not complete actuator distribution.

The subsequent [enable/fault/reset pass](ACTUATOR_CONTROL_LAYOUT.md) completes
those control nets. The later [distribution pass](ACTUATOR_DISTRIBUTION_LAYOUT.md)
connects the actuator branches and records the current board counts. The results
below describe this earlier local-power stage.

## Completed scope

- Routed PWR_5V from the existing buck-input feed to U13, using a 1.5 mm back
  copper trunk and three input transition vias. Local pad escapes are narrower.
- Added C89, 1 uF/50 V, Samsung CL10A105KB8NNNC, LCSC C15849, 0603, between
  PWR_5V and GND beside U13. This reuses C24's selected part; stock is not reserved.
- Moved existing C40, 10 uF/25 V, beside U13 OUT and connected it through local
  front copper and three output transition vias. C37-C39 remain remote storage.
- Routed the UVLO ladder, OVLO divider, C26 ramp capacitor and R42/R43 current
  limit network. ACT_ILM stays on front copper without vias (9.049 mm total).
- Connected D3's anode to ACT_UVLO. Its cathode-to-U16 ACT_DRIVE_EN connection
  remains open, so the hardware disable path is not yet complete on the PCB.
- Connected the local ground pads to the filled In1 ground reference.

[TI's TPS25947 datasheet, Rev. C, section 8.4](https://www.ti.com/lit/ds/symlink/tps25947.pdf)
calls for local input/output bypass, short power paths, close setting components,
quiet analog returns and adequate heat spreading. This pass addresses local
placement and connectivity; current capacity, thermal spreading, ILM parasitics
and the complete quiet-ground arrangement still require review and measurement.

## Placement

Coordinates are PCB millimetres; all listed components are on the front.
U13 remains at (146, 142), rotation 0 degrees.

| Reference | Centre X, Y | Rotation |
| --- | --- | --- |
| C89, new input bypass | 146, 139 | 90 degrees |
| C40, output bypass | 145.2, 144.9 | 0 degrees |
| C26, ramp | 148.5, 145.25 | 0 degrees |
| R42, current limit | 151, 138.1 | 0 degrees |
| R43, current limit | 151, 142.4 | 0 degrees |
| R40, OVLO | 153.5, 139 | 90 degrees |
| D3, disable clamp | 151.8, 145.1 | 90 degrees |

C89/C40/C26 signal-pad centres are respectively 2.239/3.523/2.680 mm from
their U13 pad centres. The checker applies a 5 mm project placement budget;
this is not a manufacturer limit or a decoupling-performance measurement.
The outline, stackup, USB/optical/ESP32 datums and mechanical keepouts are unchanged.

## Verification

The saved board has **317 motherboard footprints and 273 BOM parts**, all with
MPN/catalog fields. Native connectivity reports **677 unrouted connections**,
down from 698 before this pass. Physical DRC and schematic parity report zero
violations, with no new exclusions. Main ERC reports zero errors and warnings.
The DRC JSON's 499 unconnected entries are a capped list, not the full count.

Run with KiCad's bundled Python, alongside the existing review exporters:

```powershell
& 'C:/Users/cartm/AppData/Local/Programs/KiCad/10.0/bin/python.exe' hardware/kicad/verify_actuator_layout.py
& 'C:/Users/cartm/AppData/Local/Programs/KiCad/10.0/bin/python.exe' hardware/kicad/test_actuator_layout_checks.py
```

The native copper checker verifies the stated input/output, ground, divider,
ramp, current-limit and D3-anode connections. Five tests cover the saved baseline
and deliberate opens in the input feed, output bypass, ILM and clamp connection.
The eight input and three buck tests also pass: 16 routing tests in total.
The buck switch route remains front-only and 3.95 mm long. The power checker
passes 195 critical pin checks, 317 footprint assignments and 4,096 interlock cases.

The 21 added vias passed a sampled pad-intersection review; this supplements
native DRC and does not establish stencil or assembly acceptance. Reports in
`build/pcb-review` record board SHA-256
`ba0c9626d5c730d4cb2be85c9fad06848f6c15c9640fc4e854ea74d9e69c4e7d`.

## Next work

Route ACT_DRIVE_EN from U16 to D3 and ACT_FAULT_N through the reset network.
Complete ACT_5V distribution, C37-C39/D2 connections, button/BLDC current loops,
sensing and brake power. Review power necks, via arrays, heat spreading and
analog returns for actual current and temperature limits. USB and other signal
routing, mechanical qualification and bench acceptance remain open. No
fabrication files or assembly order have been released.
