# KiCad electronics

Revision 0.8, 2026-09-09, KiCad 10.0.6. USB-C power, MCU allocation and wheel/brake, IMU, RGB and PMW3360 circuits are connected.
A [60 x 95 mm motherboard placement](../pcb/README.md) is available as of
2026-09-09, with all 315 footprints on-board. U27/C62 and J7 are in a separate,
fully routed [14 x 18 mm encoder project](../encoder/README.md). Both are editable
development drafts; **the motherboard is partially routed and neither board is
order-ready**. Firmware, measurements and mechanical fit remain open.

## Open and edit

1. Open [MagMouse.kicad_pro](MagMouse.kicad_pro) in KiCad Manager.
2. Open [MagMouse.kicad_sch](MagMouse.kicad_sch).
3. Enter a sheet and press **E** on a component to inspect its MPN, footprint,
   LCSC number and sourcing status.
4. Open [MagMouse.kicad_pcb](MagMouse.kicad_pcb) in PCB Editor for the initial
   layout. Enable Dwgs.User for reservations and F.Fab/B.Fab for references.

Use the standard KiCad 10 libraries. The local symbol and footprint libraries
are registered by [sym-lib-table](sym-lib-table) and [fp-lib-table](fp-lib-table).
No JLCPCB plugin is needed. Edit the schematic files directly.

| Sheet | Implemented content |
| --- | --- |
| Overview | Eighteen-page hierarchy and remaining work |
| 01 Power / USB | USB-C data/CC protection, TUSB320 sink detection, TPS62162 fixed 3.3 V regulator |
| 02 MCU | ESP32-S3 module, USB, reset/boot, recovery pads and power-control GPIOs |
| 03 Buttons | Three DRV8231A bridges, VREF/current feedback, input pulldowns and coil connectors |
| 04 Sensing | Three switchable Hall sensors, ADS7038; all eight ADC channels assigned |
| 05 Protected power | Separate input/actuator eFuses, UVLO/OVLO, ramps, fault/reset and enable clamp |
| 06 Actuator interlock | Hardware heartbeat timeout, source/reset/sensor-qualified arm and six input gates |
| 07 Power monitor | CC-selected current-limit resistors, buffered input-current sensing, VBUS presence and ACT voltage |
| 08 Actuator rail | Input/actuator transient clamps, ACT storage/discharge and test pads |
| 09 Interface reservations | MCU interfaces, test pads and boot/control bias |
| 10 Wheel driver | DRV8316R, 3-PWM hardware shutdown, charge pump, unused-buck termination and motor wire pads |
| 11 Wheel SPI | Driver/ADC2/encoder power-domain buffers and fault return |
| 12 Wheel feedback | Second ADS7038, phase-current filters, switched encoder supply and J6 cable header |
| 13 Regeneration brake | ACT-powered comparator/reference, MOSFET and four power resistors |
| 14 IMU | ICM-42688-P, shared SPI2, INT1 and supply bypass |
| 15 RGB status | Single-data-pin LED, enabled regulator and logic buffer |
| 16 Optical power | Sensor-enabled ramp switch, 1.9V LDO, illumination feed and bypass |
| 17 Optical sensor | PMW3360, isolated SPI/CS and strong reset buffer |

VBUS_USB feeds PWR_5V through U12; U13 supplies ACT_5V. These rails replace the
disconnected pending nets. The TPS62162 and 3.3 uH inductor replace the original
TLV62569/divider circuit. See [power behavior and firmware requirements](../../docs/power.md)
and [power sourcing/package review](POWER_REVIEW.md).

Each button bridge retains the provisional 0.333 A trip setting:
1.65 V / (0.0015 × 3300 ohms). Actual force, current accuracy, winding heating
and pulse duration require the mechanical experiment. Coils, magnets, paddles
and wiring are external assemblies, not SMT parts.

## Review exports

From the repository root, run these commands with Python 3 and KiCad 10:

    python hardware/kicad/export_review.py
    python hardware/kicad/export_review.py --schematic hardware/encoder/Encoder.kicad_sch
    python hardware/kicad/verify_encoder.py
    python hardware/kicad/test_encoder_checks.py
    python hardware/kicad/verify_power.py
    python hardware/kicad/verify_resources.py
    python hardware/kicad/verify_wheel.py
    python hardware/kicad/test_wheel_checks.py
    python hardware/kicad/verify_peripherals.py
    python hardware/kicad/test_peripheral_checks.py
    python hardware/kicad/verify_optical.py
    python hardware/kicad/test_optical_checks.py

The exporter accepts --kicad-cli PATH. The checker accepts --footprints PATH
for a nonstandard KiCad footprint installation. Generated files go to
build/kicad-review: eighteen SVG sheets, XML netlist, ERC JSON, DRAFT-bom.csv,
review-status.json, power-checks.json, resource-checks.json, wheel-checks.json, peripheral-checks.json and optical-checks.json. Sources are not overwritten.

The motherboard has **271 BOM components**, all with catalog IDs, MPNs and
footprints; 43 copper test pads, J5 motor wire pads and four power flags are
excluded from its BOM. The separate encoder has one schematic sheet and three
BOM components/footprints: U27, C62 and J7. Across both projects there are 19
schematic pages, 274 BOM components and 318 footprints. Encoder review outputs
and its separate draft BOM go to `build/encoder-review`; its two incoming power
flags are excluded from assembly. Export both netlists before running the wheel
checker. The encoder checker also verifies the actual harness contract.
**Both projects: ERC zero errors and zero warnings, without new waivers.**
The additional checker verifies 191 critical power pin connections, 315 motherboard footprint
assignments, complete source-to-export coverage and 4,096 Boolean interlock
cases. The resource checker verifies all 39 module GPIOs: 38 assigned and GPIO46
reserved low for boot-safe expansion. See [the full allocation](../../docs/interfaces.md).
The wheel checker adds 266 pin checks, 32 shutdown cases, 58 custom land checks
and 128 brake corners; five wheel tests include four fault injections.
Optical adds 81 pin checks, ten identities, 16 land coordinates and eight fault injections.
See [optical implementation](OPTICAL_DESIGN.md) for pending sample and firmware evidence.
See [wheel design and evidence](WHEEL_REVIEW.md) and [IMU/RGB review](PERIPHERAL_REVIEW.md). Analog timing, firmware
deadlines, thermal behavior and USB compliance are not simulated.

Catalog identity does not reserve stock. U11's current JLCPCB listing requires
Standard PCBA; refresh service eligibility and pricing before placing an order.
These schematic tools do not produce manufacturing files. Use
`python hardware/kicad/export_pcb_review.py` for the separate PCB placement/DRC
review; see [board setup and remaining layout work](../pcb/README.md).
The first [buck routing pass](../pcb/BUCK_LAYOUT.md) also provides native copper
connectivity checks and fault-injection tests, run with KiCad's bundled Python.

## Work before full-board freeze

A bench prototype and preliminary placement can proceed before all measurements
are complete. Full-mouse routing needs settled circuitry, pin allocation and
mechanical dimensions. The following tests are acceptance gates, including tests
that require a prototype PCB; finished firmware is not required to start layout.

- Implement and measure USB startup, configuration, suspend/resume and source
  changes. Verify the 100 mA startup and 2.5 mA suspend requirements.
- Prototype one button; measure force/current, winding properties, current-sense
  accuracy, heating, passive return and magnetic interference.
- Test timeout/reset/short-circuit behavior, cable drop, inrush, reverse current,
  regenerative clamp behavior and component temperatures.
- Qualify the [PMW3360 circuit](OPTICAL_DESIGN.md), samples, SROM and optical stack.
  Review and measure the [IMU/RGB circuits](PERIPHERAL_REVIEW.md). Validate wheel current/angle
  acquisition and the provisional autonomous regeneration brake on hardware.
- Validate the [allocated SPI/PWM timing budgets](../../docs/interfaces.md), review symbols,
  land patterns and stencil requirements, then perform board layout and DRC.

See [SOURCING.md](SOURCING.md) for retained component evidence and
[the roadmap](../../docs/roadmap.md) for the broader project.
