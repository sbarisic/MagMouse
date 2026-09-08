# KiCad schematic

Revision 0.4, 2026-09-08, KiCad 10.0.6. USB-C power control and the full MCU GPIO allocation are connected.
This is an editable development draft; **no PCB layout or order-ready mouse
design exists yet**. Firmware, measurements and absent subsystems remain open.

## Open and edit

1. Open [MagMouse.kicad_pro](MagMouse.kicad_pro) in KiCad Manager.
2. Open [MagMouse.kicad_sch](MagMouse.kicad_sch).
3. Enter a sheet and press **E** on a component to inspect its MPN, footprint,
   LCSC number and sourcing status.

Use the standard KiCad 10 libraries. The local symbol and footprint libraries
are registered by [sym-lib-table](sym-lib-table) and [fp-lib-table](fp-lib-table).
No JLCPCB plugin is needed. Edit the schematic files directly.

| Sheet | Implemented content |
| --- | --- |
| Overview | Ten-page hierarchy and remaining work |
| 01 Power / USB | USB-C data/CC protection, TUSB320 sink detection, TPS62162 fixed 3.3 V regulator |
| 02 MCU | ESP32-S3 module, USB, reset/boot, recovery pads and power-control GPIOs |
| 03 Buttons | Three DRV8231A bridges, VREF/current feedback, input pulldowns and coil connectors |
| 04 Sensing | Three switchable Hall sensors, ADS7038; all eight ADC channels assigned |
| 05 Protected power | Separate input/actuator eFuses, UVLO/OVLO, ramps, fault/reset and enable clamp |
| 06 Actuator interlock | Hardware heartbeat timeout, source/reset/sensor-qualified arm and six input gates |
| 07 Power monitor | CC-selected current-limit resistors, buffered input-current sensing, VBUS presence and ACT voltage |
| 08 Actuator rail | Input/actuator transient clamps, ACT storage/discharge and test pads |
| 09 Interface reservations | Allocated MCU interfaces, test pads and boot/control bias; peripheral circuits still pending |

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
    python hardware/kicad/verify_power.py
    python hardware/kicad/verify_resources.py

The exporter accepts --kicad-cli PATH. The checker accepts --footprints PATH
for a nonstandard KiCad footprint installation. Generated files go to
build/kicad-review: ten SVG sheets, XML netlist, ERC JSON, DRAFT-bom.csv,
review-status.json, power-checks.json and resource-checks.json. Sources are not overwritten.

The current draft has **150 BOM components**, all with catalog IDs, MPNs and
footprints; 33 copper test pads and three power flags are excluded from the BOM.
**ERC: zero errors and zero warnings, without new waivers.**
The additional checker verifies 191 critical pin connections, 183 footprint
assignments, complete source-to-export coverage and 4,096 Boolean interlock
cases. The resource checker verifies all 39 module GPIOs: 38 assigned and GPIO46
reserved low for boot-safe expansion. See [the full allocation](../../docs/interfaces.md).
Analog timing, firmware deadlines, thermal behavior and USB compliance are not simulated.

Catalog identity does not reserve stock. U11's current JLCPCB listing requires
Standard PCBA; refresh service eligibility and pricing before placing an order.
No board-placement file or manufacturing release is produced by these tools.

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
- Add validated PAW3950 circuitry, IMU, wheel driver/encoder/current acquisition
  and RGB. Wheel regenerative energy may require a dedicated brake circuit.
- Validate the [allocated SPI/PWM timing budgets](../../docs/interfaces.md), review symbols,
  land patterns and stencil requirements, then perform board layout and DRC.

See [SOURCING.md](SOURCING.md) for retained component evidence and
[the roadmap](../../docs/roadmap.md) for the broader project.
