# Type-C detector routing

2026-09-09, KiCad 10.0.6. This pass continues the
[input-power routing](INPUT_POWER_LAYOUT.md). It connects the Type-C detector
and source-selection supplies; USB data and the rest of the motherboard are
still incomplete.

## Completed connections

- J1 A5/B5 connect to U20's CC protection pads and then U11 CC1/CC2.
  The controller-side branches start at the protection pads. CC1 and CC2 are
  separate configuration channels, not the USB data differential pair.
- U20 has two nearby ground vias to the filled In1 plane. The right USB ground
  contact now connects to its adjacent plated shield land, replacing one
  separate via that obstructed the CC escape. The shield and contact remain GND.
- VBUS reaches R25 through a low-current sense branch. R25's protected side
  connects directly to U11 VBUS_DET on front copper.
- U11 PORT is grounded for sink mode, EN_N is grounded to enable detection,
  and its GND pin and C22 return connect to In1 ground.
- The buck output supplies C22/U11, the R26/R27 capability-output pull-ups,
  U14/C32 and U16/C29. These are source-selection supply branches; the MCU
  and the remaining 3.3 V loads still need distribution.
- The previously routed capability outputs and current-limit switch commands
  remain connected. U16's actuator-interlock inputs/outputs and the MCU's
  capability inputs remain part of later signal routing.

The detector configuration is unchanged: GPIO mode, fixed sink, active-low
enable and an 887 kohm VBUS-detect resistor. The current-limit values and logic
truth tables are unchanged. The schematic and BOM did not change in this pass.

## Placement and supply routing

| Reference | Centre X, Y (mm) | Rotation | Change |
| --- | --- | --- | --- |
| U20 | 136.7, 104.5 | 0 degrees | Small move toward USB while clearing nearby parts |
| C22 | 138.7, 106.8 | 90 degrees | Bypass beside U11's supply side |
| R25 | 138.5, 113.7 | 0 degrees | Shorter local VBUS_DET connection |
| R26 | 140.5, 116.1 | 0 degrees | Pull-up moved out of the congested U11/buck fanout |
| C29 | 101, 170.4 | 180 degrees | Bypass closer to U16 VCC |

[TI's TUSB320LAI datasheet, sections 8.3 and 10](https://www.ti.com/lit/ds/symlink/tusb320lai.pdf)
specifies local 100 nF bypass, a VDD ramp within 25 ms, and pull-up supplies
that rise with or after VDD. The supply routing uses the same buck rail for
the controller and its output pull-ups; ramp behavior still needs measurement.

C22's local connection uses layer transitions because the nearby CC and ground
escapes constrain a front-only path. Through vias are 0.60/0.30 mm and sit
outside solder lands. Power distribution in this pass uses 0.25–0.50 mm tracks
for the detector and logic loads. This does not size the rail for the MCU or
actuators. The longer rear logic feed needs review alongside the final board
distribution and bypass network.

The layout retains the 60 x 95 mm outline, selected stackup, USB/optical/ESP32
datums, mechanical keepouts and separate encoder board. There are still
316 motherboard footprints and 272 BOM parts.

## Verification and next work

- Physical DRC: zero violations; schematic parity: zero issues, no new exclusions.
- Native connectivity: **698 unrouted connections**, down from 718 before this
  pass. The DRC JSON's 499 entries are not the full native connection count.
- The expanded input copper checker passes. Eight tests include deliberate
  opens in CC1, the detector supply and the sink-mode ground connection.
  The three buck tests also pass, with its 3.95 mm front-only switch trace intact.

Use the commands in [the input review](INPUT_POWER_LAYOUT.md). Reports under
`build/pcb-review` carry the board hash. These checks establish the stated
copper connectivity and CAD clearance only; they do not prove powered operation,
ESD performance or USB compliance.

Continue with the actuator eFuse U13 and its local power/current-limit loops,
then bridge/BLDC/brake copper and USB data routing. Input-current telemetry,
fault/reset/MCU interfaces, wider supply distribution, ILM parasitic review,
mechanical qualification and bench acceptance remain open. No fabrication or
assembly order files have been released.
