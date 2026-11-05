# MagMouse

An open-source wired mouse exploring contactless Hall-sensed buttons with plastic
click mechanisms, and a motorized haptic scroll wheel.

**Active development: [four two-layer boards](hardware/two-layer/sandwich/README.md),
with two 70 Ã— 100 mm stacked Main boards and passive plastic button clicks.**
All four boards are routed, with independent schematics and clean native
ERC, DRC, connectivity and schematic-parity checks under the saved rules.
The [quote package](hardware/two-layer/sandwich/quote-package/README.md) contains
Gerbers, drills, BOMs and placement files; supplier and physical acceptance remain open.
The Main stack and Wheel harness each use 19 wires with three shared grounds.

Superseded boards, bench fixtures and quote packages are available in
[Git history](docs/history/README.md). The current checkout contains the active
designs, shared libraries, current manufacturing exports and retained evidence.

## V1 concept

- ESP32-S3 with native USB Full-Speed HID; target report interval: 1 ms.
- PMW3360DM-T2QU + LM19-LSI optical sensor for cursor movement; ICM-42688-P for supplementary motion.
- Three plastic click mechanisms provide tactile feedback and passive return.
  Each uses a TMAG5253 Hall sensor and a sensing magnet, read through ADS7038.
  Buttons have no coils or powered force feedback.
- MA735 angle sensing and a GB1806 motor driven by DRV8316R for scroll haptics.
- One USB-C cable for data and 5 V power, with force limits based on detected
  source capability. A powered Type-C hub/adapter is the intended full-power source.

## Repository map

| Directory | Contents |
| --- | --- |
| [hardware](hardware/README.md) | Electronics, preliminary BOM, schematic and PCB work |
| [mechanical](mechanical/README.md) | Housing, button mechanisms, scroll assembly |
| [firmware](firmware/README.md) | Embedded architecture and bring-up plan |
| [software](software/README.md) | Future PC configuration application |
| [docs](docs/README.md) | Requirements, interfaces, power and roadmap |

Start with the [architecture](docs/architecture.md), [interface plan](docs/interfaces.md),
and [button prototype plan](mechanical/button-mechanisms/README.md), then the
[roadmap](docs/roadmap.md). [ideas.md](ideas.md) preserves the original
brainstorming notes; the organized documents distinguish selected directions from
open engineering questions.

## Contributing and licensing

See [CONTRIBUTING.md](CONTRIBUTING.md). The next milestone is mechanical-interface
CAD, resulting PCB adjustments and whole-board review before manufacturing closure.

Hardware/mechanical: **CERN-OHL-S-2.0**. Firmware, PC software and supporting code:
**GPL-3.0-or-later**. General documentation: **CC-BY-SA-4.0**.
See [LICENSE.md](LICENSE.md) for scope and full texts.
