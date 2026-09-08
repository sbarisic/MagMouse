# MagMouse

An open-source wired mouse exploring contactless magnetic buttons, programmable
voice-coil click feedback, and a motorized haptic scroll wheel.

**Status: architecture and repository setup.** There are no fabrication-ready
schematics, CAD models, or runnable firmware yet. Contactless sensing removes
electrical switch contacts; it does not eliminate mechanical wear or other failures.

## V1 concept

- ESP32-S3 with native USB Full-Speed HID; target report interval: 1 ms.
- PAW3950 optical sensor for cursor movement; ICM-42688-P for supplementary motion.
- Three TMAG5253 Hall sensors and LVCM-013-008-02 voice coils for left, middle,
  and right buttons, with ADS7038 feedback and three DRV8874 drivers.
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
and [roadmap](docs/roadmap.md). [ideas.md](ideas.md) preserves the original
brainstorming notes; the organized documents distinguish selected directions from
open engineering questions.

## Contributing and licensing

See [CONTRIBUTING.md](CONTRIBUTING.md). The next milestone is schematic-level
design and feasibility validation, before PCB layout or production firmware.

Hardware/mechanical: **CERN-OHL-S-2.0**. Firmware, PC software and supporting code:
**GPL-3.0-or-later**. General documentation: **CC-BY-SA-4.0**.
See [LICENSE.md](LICENSE.md) for scope and full texts.
