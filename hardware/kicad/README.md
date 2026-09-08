# KiCad starter schematic

Revision 0.1, 2026-09-08. Created and exported with KiCad 10.0.6.
This is an editable circuit-development draft, **not a working or order-ready
mouse design**. No PCB layout exists yet.

## Open and edit

1. In KiCad Manager, choose **File > Open Existing Project** and select
   [MagMouse.kicad_pro](MagMouse.kicad_pro).
2. Open [MagMouse.kicad_sch](MagMouse.kicad_sch) from the project tree.
3. Double-click a sheet to enter it. Select a component and press **E** to
   inspect its MPN, footprint, LCSC number and sourcing status.

Use the standard symbol and footprint libraries bundled with KiCad 10. Accept
the default library setup if this fresh installation asks. The project-local
symbol library is registered through [sym-lib-table](sym-lib-table).
No JLCPCB plugin is required to edit this project or retain sourcing fields.

## Included circuits

| Sheet | Draft content |
| --- | --- |
| Overview | Hierarchy and unresolved blocks |
| 01 Power / USB | USB-C data, ESD candidate, TLV62569 3.3 V buck and test pads |
| 02 MCU | ESP32-S3-MINI-1-N8, decoupling, USB resistors, reset/boot and recovery pads |
| 03 Buttons | Three DRV8231A bridges, input pulldowns, fixed VREF, current feedback and coil connections |
| 04 Sensing | Three TMAG5253 Hall sensors, ADS7038 and decoupling |

The custom stationary coils and moving magnets replace the industrial voice
coils. The elastic paddles provide passive return; the bridges deliver brief
effects. Coil windings, magnets and mechanical assemblies are external items,
not SMT components for JLCPCB to populate.

Draft GPIO allocation: GPIO4/5 left IN1/IN2; GPIO6/7 middle; GPIO8/9 right;
GPIO10 ADC CS; GPIO11 MOSI; GPIO12 SCLK; GPIO13 MISO; GPIO19/20 USB D-/D+.
Other MCU pins have NC marks only because their circuits have not been added.
The complete mouse still needs a reviewed GPIO and peripheral-resource budget.

The buck divider is 100 kOhm / 22.1 kOhm, nominally 3.315 V. Each bridge uses
a 10 kOhm / 10 kOhm VREF divider and 3.3 kOhm IPROPI resistor. With the
datasheet's nominal 1500 uA/A mirror ratio, the provisional trip current is
1.65 / (0.0015 * 3300) = 0.333 A. This is a starting value for bench work;
accuracy, required force, pulse duration and coil heating are unverified.

## Work before layout

- Complete USB CC termination/current detection, input protection, VBUS sensing
  and source-current policy. **VBUS_USB is disconnected from PWR_5V_PENDING
  and ACT_5V_PENDING. This draft cannot run from its USB connector.**
- Add the protected actuator supply switch, hardware timeout/shutdown and a
  path for regenerated energy. Input pulldowns alone do not provide a timeout.
- Add PAW3950 reference circuitry, IMU, wheel driver/encoder/current feedback
  and RGB indicator. Validate the optical parts and initialization first.
- Select the remaining parts and footprints listed in [SOURCING.md](SOURCING.md).
- Prototype one button, then review power, ADC settling, current sensing,
  thermal limits, magnetic interference and the complete pin allocation.
- Review every symbol-to-package mapping and clear ERC before board layout.

## Review exports

From the repository root, with Python 3 and KiCad 10 installed:

```powershell
python hardware/kicad/export_review.py
```

The script discovers KiCad on PATH or in typical Windows installation locations;
use `--kicad-cli PATH` to override it. It exports the current editable sources
to `build/kicad-review/`: five SVG sheets, XML netlist, ERC JSON, grouped
`DRAFT-bom.csv`, and `review-status.json`. It never overwrites schematic sources.
The BOM includes unresolved rows so they cannot silently disappear from review.
Its column names include Comment, Designator, Footprint and LCSC Part #.

The initial draft has 60 BOM components, 43 with verified LCSC catalog numbers,
17 without numbers and six without footprints. Nine copper test pads and two
ERC power flags are excluded from the BOM. Catalog identity does not establish
current JLC assembly stock, price or assembly eligibility.

Initial ERC: **two errors** for the unsourced logic/actuator 5 V inputs and
**two warnings** for the dangling CC1/CC2 connections. These have not been
waived. Ground and the buck output have power flags; the unfinished input rails
do not. The script returns exit code 2 while ERC or BOM gaps remain; this is
expected for revision 0.1. Even a future successful export is not fabrication
approval: ERC cannot validate analog behavior or missing subsystems.

Initial review also checked 56 critical pin-to-net assignments and confirmed
that all 63 assigned footprints (including test pads) exist in the installed
libraries and contain the required pin numbers. All five rendered sheets were
visually inspected. These checks do not replace a full circuit/package review.

After schematic and layout review, generate Gerbers, drill files and a PCB
placement/CPL file, refresh JLC stock and prices, and inspect its assembly
preview. A schematic BOM alone cannot order an assembled PCB.

Hardware design: CERN-OHL-S-2.0. The separate reusable symbol library has the
license and attribution recorded in [SOURCING.md](SOURCING.md).
