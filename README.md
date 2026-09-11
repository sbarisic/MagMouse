# MagMouse

An open-source wired mouse exploring contactless magnetic buttons, programmable
electromagnetic click feedback, and a motorized haptic scroll wheel.

**Status: main and wheel prototype PCBs routed; mechanical integration pending.**
Open the active [Main project](hardware/modular/main/Main.kicad_pro) or
[Wheel project](hardware/modular/wheel/Wheel.kicad_pro). Both have zero unrouted
connections and zero physical DRC/parity issues. See the
[routing review](hardware/modular/MAIN_SIGNAL_ROUTING.md) and
[modular hardware package](hardware/modular/README.md). The original monolithic
project is retained as a reference. These are not fabrication-ready designs;
mechanics, manufacturing and hardware qualification remain open. Contactless sensing removes
electrical switch contacts; it does not eliminate mechanical wear or other failures.

[Quote-only JLCPCB packages](hardware/quotes/README.md) now provide separate
Main/Wheel/Encoder Gerbers, BOMs and CPLs for pricing five sets. The live JLCPCB
checkout quotes USD 1,187.35 (about EUR 1,021) including DHL DDP shipping and
duties/taxes for five sets to Croatia 43000. Three stock shortages and the separately installed optical sensor remain;
this is a partial-population quote, not an order-ready complete set.

## V1 concept

- ESP32-S3 with native USB Full-Speed HID; target report interval: 1 ms.
- PMW3360DM-T2QU + LM19-LSI optical sensor for cursor movement; ICM-42688-P for supplementary motion.
- Three elastic button paddles provide passive return. Each uses a TMAG5253
  position sensor with its own magnet, plus a custom moving-magnet actuator with
  a stationary wound coil, ADS7038 feedback, and a DRV8231A bidirectional driver.
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
