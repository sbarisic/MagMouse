> Rev-A bench update: internal interfaces now use soldered through-hole arrays.
> The active manufacturing-review package is `hardware/bench/`; its HARNESS_REVIEW.md
> and generated wire maps supersede historical FFC/JST details below. Order scope
> is five bare three-board panels, one component population and one stencil.
> No final-shell or supplier/CAM acceptance is claimed.

# Main-to-wheel circuit interface review

2026-09-10. Independent main/wheel schematics exist and pass migration checks.
**No modular PCB layout, harness or assembly release is approved.**

Prototype scope, updated by the user: assume internal cables remain fully
connected. Possible child-board damage after disconnection is accepted for now.
Disconnect, partial-insertion and open-return survival are outside acceptance;
normal connected operation, rail sequencing and regeneration remain in scope.

Open [main/Main.kicad_pro](main/Main.kicad_pro) or
[wheel/Wheel.kicad_pro](wheel/Wheel.kicad_pro). Their schematics are independent
editable sources. The old motherboard PCB remains a retained routing baseline;
do not update it from either split schematic. The independent wheel PCB now has
a [completed routing pass](WHEEL_ROUTING.md). The shaped main also has
[completed routing](MAIN_SIGNAL_ROUTING.md), with zero unrouted connections and
zero physical DRC/parity issues. Its source/actuator/interlock checks still pass.
The encoder remains in `hardware/encoder`. Routing does not close the cable
or sampling-time findings below.

## Implemented connections and parts

The split preserves 988 original connected pin assignments. Main has 246
footprints (207 BOM parts); wheel has 87 (82 BOM parts). The existing encoder
adds three. Nine bias resistors, four connector headers and three local power
parts are new, for a total of 336 footprints across the three units.
Mechanical items and cables are extra.

J8/J9 use Hirose **FH12-30S-0.5SH(55), C506793**, a 30-contact, 0.5 mm pitch,
bottom-contact header accepting 0.3 mm thick FFC/FPC. Its
[JLCPCB listing](https://jlcpcb.com/partdetail/HRS_Hirose-FH12_30S_0_5SH_55/C506793)
identifies SMT assembly support; stock is not reserved. Use the native KiCad
Hirose FH12-30S footprint. Do not substitute the top-contact FH12A variant.
Main J8 odd contacts are GND. Facing bottom-contact headers with a flat same-side
FFC connect J8.N to J9.(31-N), so wheel J9 even contacts are GND. The schematic
and `partition-plan.json` now implement that physical mapping.

J10/J11 use **JST SM02B-PASS-TB(LF)(SN), C495198**: pin 1 ACT_5V, pin 2 GND.
The [JLCPCB listing](https://jlcpcb.com/partdetail/JST-SM02B_PASS_TB_LF_SN/C495198)
matches the no-boss, side-entry version. The local footprint follows the
[JST PA drawing](https://www.jst-mfg.com/product/pdf/eng/ePA-F.pdf), pages 4/11:
2 mm pitch, signal lands 1 x 2.7 mm, hold-down lands 1.8 x 3.8 mm. Pin 1 is on
the right in that mounting-side drawing. No locating holes are used for this
no-boss part; do not substitute the `PASS-1` version. The footprint still needs
part/assembly sign-off and has no fabricated 3D model.

Power harness target: PAP-02V-S housings, SPHD-001T-P0.5 contacts, AWG22 wire.
JST specifies 3 A with AWG22; this is a connector rating, not a motor operating
allocation. The source-aware USB/actuator limits still apply. FFC conductor
construction, mating orientation and length remain open; 50 mm is the target.
Verify pin-to-pin continuity instead of inferring it from contact-side labels.
The [cable qualification brief](CABLE_REVIEW.md) now records an exact FFC
candidate, connected-operation checks and the excluded disconnect fault cases.

## Disconnected cable defaults

| Circuit change | Purpose |
| --- | --- |
| Wheel R137-R140, 10k to GND | Low defaults on raw RUN and PWM inputs |
| Wheel R84, 100k changed to 10k | Local low default on enable/nSLEEP |
| Main R141, 33k to GND | An unplugged wheel asserts the fault return |
| Main R142/R143, 33k to GND | Prevent floating driver/ADC2 return-buffer inputs |
| Wheel R144/R145, 33k to GND | Define raw CS levels without pulling into a switched-off rail |
| Wheel R88, 10k changed to 4.7k | Preserve nFAULT startup-high margin with the new main pulldown |

Main R77 remains in place for the ESP32 GPIO3 boot strap. A disconnected CS
defaults low, but clock/MOSI are biased low and RUN is disabled. A connected,
reset main board still pulls CS high through R74/R76. This avoids adding a raw
CS pullup from the host signal into the independently switched DRV_AVDD rail.

Static screens use 2% resistor corners, system logic rail >=3.0 V, AVDD >=3.1 V
and 20 uA input-leakage allowance. Fault-high and enable-low screens reserve
50 uA total leakage. They give: fault disconnected <=0.674 V, fault connected
>=2.389 V (above the driver's 2.2 V startup threshold), CS disconnected <=0.674 V,
CS high during host reset >=2.125 V, enable disconnected <=0.510 V. These are
settled DC calculations, not cable-bounce or ramp guarantees. `verify_split.py`
also evaluates 64 harness/command combinations using U22's exported pin nets.

## Power-domain correction

The previous wheel review incorrectly claimed Ioff for SN74LVC125A.
[TI confirms this device lacks Ioff](https://e2e.ti.com/support/logic-group/logic/f/logic-forum/265362/sn74lvc125apw-has-ioff-circuitry).
Its [datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc125a.pdf) permits
overvoltage on inputs but constrains output voltage to the device supply.

| Buffer | Supply | Input source | Output destination |
| --- | --- | --- | --- |
| U24/U26 on wheel | DRV_AVDD | Main logic through cable | Driver/ADC2 on DRV_AVDD |
| U25 on main | +3V3 | Wheel returns and encoder MISO | Main +3V3 SPI/fault inputs |
| U29 on main | ENC_3V3 | Main logic | Encoder on ENC_3V3 |

The intended directions avoid externally driving a dead buffer output from
another rail. Retain destination-rail pullups on local outputs. Do not add a
main-powered pullup to ADC2/driver output-side nets, and do not assume that OE
alone supplies power-off protection. Partial ramps, rail discharge, clamps and
shared-MISO contention remain measured acceptance tasks. The pin-compatible
SN74LV125A has Ioff but slower timing; it has not been substituted.

## Findings that must be closed before routing/bring-up acceptance

**Connected harness loading:** verify current sharing, voltage drop and heating
with both harnesses fully seated at the allowed operating loads. Power-GND-open
and partial-insertion survival are excluded by the user's prototype decision;
they do not block placement or require added wheel-feed protection. The fault
calculation remains informational and is not relabeled as a passed test.

**Wheel-local stored energy:** C90 adds 100 uF/16 V polymer bulk to the original
40.4 uF, giving **140.4 uF nominal locally**. D6 adds a local secondary TVS;
R146 adds a local discharge path. The [local power review](LOCAL_POWER_REVIEW.md)
checks part selection, polarity, footprint and conditional energy/inrush/peak
calculations. Effective C >=47 uF, ESR, actual inrush and brake transient
qualification remain open. The TVS does not establish the 6.5 V rail ceiling.

**SPI3 timing:** a simple worst-case path has two SN74LVC125A delays of 6 ns
each plus [ADS7038 SCLK-to-SDO delay](https://www.ti.com/lit/ds/symlink/ads7038.pdf)
of 16 ns: **28 ns before cable and MCU input delay**. That exceeds an unshifted
20 MHz half-cycle of 25 ns. This does not prove 20 MHz is impossible with a
different sample phase; it means the old target is not accepted. Validate the
ESP32-S3 capture phase, `input_delay_ns`, setup/hold and loaded cable using the
[target-specific driver](https://docs.espressif.com/projects/esp-idf/en/v5.5.1/esp32s3/api-reference/peripherals/spi_master.html).
Do not apply original-ESP32 GPIO-matrix delay numbers blindly to ESP32-S3.

Start ADC register/data bring-up at 1 MHz, then characterize 10 MHz before
attempting 20 MHz. Four 18-clock frames with 0.7 us high gaps take 10 us at
10 MHz before software overhead. That misses the existing 8 us burst target,
so current-loop cadence and the valid low-side window must be revised if the
slower clock becomes necessary. No firmware timing acceptance is claimed.
The machine report now sweeps 1/5/10/20 MHz. At 10 MHz, only 2 us of the
proposed 12 us quiet window remains after the nominal four-frame burst;
transaction overhead, settling, trigger latency and jitter still consume that
margin. At 1 MHz, the burst is 74.8 us, suitable for stopped-motor bring-up
only; do not run the proposed 20 kHz current loop with that setting.

## Verification and reproducibility

Both projects export with **zero ERC errors and zero warnings**. All BOM parts
have MPN, LCSC ID and footprint fields; catalog fields do not prove availability.
The connector and local-power pages were rendered and visually inspected.
Ten regression tests pass, including deliberate local-power circuit faults and
an incorrectly unreversed J9 pin map.
The retained source
motherboard schematic and PCB have not been modified by this migration.

```powershell
python hardware/kicad/export_review.py --schematic hardware/modular/main/Main.kicad_sch --output build/modular/main-review
python hardware/kicad/export_review.py --schematic hardware/modular/wheel/Wheel.kicad_sch --output build/modular/wheel-review
python hardware/modular/verify_split.py --baseline build/modular/main-netlist.xml --main build/modular/main-review/netlist.xml --wheel build/modular/wheel-review/netlist.xml --output build/modular/split-check.json
python -m unittest discover -s hardware/modular -p test_split_checks.py
```

Export a fresh baseline netlist as described in README.md if absent. The strict
`--require-reviewed` mode intentionally fails on the open gates above. It must
not be used to claim PCB or manufacturing approval from ERC alone.
`extract_schematics.py` records the initial migration into an empty staging
directory. The promoted `main/` and `wheel/` files are now editable sources;
do not rerun extraction over later hand edits. Review library-table paths when
using another staging location.
