# MagMouse

An open-source wired mouse exploring contactless Hall-sensed buttons with plastic
click mechanisms, and a motorized haptic scroll wheel.

**Active development: [four two-layer boards](hardware/two-layer/sandwich/README.md),
with two 70 × 100 mm stacked Main boards and passive plastic button clicks.**
All four boards are routed, with independent schematics and clean native
ERC, DRC, connectivity and schematic-parity checks under the saved rules.
The [quote package](hardware/two-layer/sandwich/quote-package/README.md) contains
Gerbers, drills, BOMs and placement files; supplier and physical acceptance remain open.
The Main stack and Wheel harness each use 19 wires with three shared grounds.

The earlier three-board Rev-A bench design below retains button coils and is a
historical checkpoint, not the current button design.
Open the earlier [Main project](hardware/modular/main/Main.kicad_pro) or
[Wheel project](hardware/modular/wheel/Wheel.kicad_pro). Both have zero unrouted
connections and zero physical DRC/parity issues. See the
[routing review](hardware/modular/MAIN_SIGNAL_ROUTING.md) and
[modular hardware package](hardware/modular/README.md). The original monolithic
project is retained as a reference. These are not fabrication-ready designs;
mechanics, manufacturing and hardware qualification remain open. Contactless sensing removes
electrical switch contacts; it does not eliminate mechanical wear or other failures.

The earlier [Rev-A bench package](hardware/bench/README.md) targets five bare
three-board panels, one self-assembled population and one stencil, with U32
unpopulated. Encoder now uses the common four-layer construction. The
[cost checkpoint](hardware/bench/COST_CHECKPOINT.md) records historical delivered
prices of EUR 224.55 for economy panels/stencil, EUR 252.46 with paid impedance
control and EUR 335.96 for separate boards. These precede the wire revision. Components, wires and bench
mechanisms are additional; the complete delivered total remains unverified.
The files are for quote/review only, pending supplier, assembly, bench-fit and
CAM checks. Earlier [PCBA quote packages](hardware/quotes/README.md) remain as
historical comparisons, not the selected purchasing plan.

In that earlier package, nine internal connectors use labelled soldered-wire arrays. The
[wire map](hardware/bench/package/wire-map.svg) retains all conductors and grounds;
[printable PETG fixtures](mechanical/bench/README.md) include editable build123d,
STEP/STL parts and assembly drawings. Fixed button magnets use
[per-button calibration](docs/button-calibration.md); runnable firmware remains
separate. The revised electronics subtotal from saved prices is EUR 73.84 for
one set, excluding optics, freight/taxes and unpriced fixture/wire materials.

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
