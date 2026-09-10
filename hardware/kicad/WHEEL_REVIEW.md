# Wheel circuit review — revision 0.5

Checked 2026-09-09 against the manufacturer documents below. Sheets 10–13 now
implement the wheel driver, ADC2, encoder, power-domain isolation and autonomous
brake. These are editable prototype circuits. Motor behavior, firmware timing,
regeneration limits and enclosure temperatures have not been measured.

The board contains 272 linked footprints: the previous 183 placements are
preserved, and 89 new footprints are staged outside the outline. The complete
circuit has 234 BOM components, 37 copper test pads and three motor wire pads
in J5. J5 and the test pads are excluded from BOM/placement exports. The GB1806,
shaft magnet, wiring, bearings and strain relief are separate mechanical items.

## Selected parts and packages

| Reference | Part / catalog identity | Package or purpose |
| --- | --- | --- |
| U21 | [DRV8316RRGFR / C5218861](https://jlcpcb.com/partdetail/C5218861) | RGF0040E, 5 × 7 mm, 40 leads plus EP41 |
| U22 | [SN74LVC08APWR / C465737](https://jlcpcb.com/partdetail/C465737) | Four hardware AND gates, TSSOP-14 |
| U23 | [ADS7038IRTER / C2871580](https://jlcpcb.com/partdetail/C2871580) | Second ADC, RTE 3 × 3 mm with EP17 |
| U24–U26, U29 | [SN74LVC125APWR / C7813](https://jlcpcb.com/partdetail/C7813) | Destination-powered SPI buffers and MCU-powered returns |
| U27 | [MA735GGU-P / C17233427](https://jlcpcb.com/partdetail/C17233427) | UTQFN-14, 2 × 2 mm, no exposed pad |
| U28 | [TPS22919DCKR / C2149796](https://jlcpcb.com/partdetail/C2149796) | Encoder load switch, SC-70-6 |
| U30 | [TLV1811DBVR / C5373003](https://jlcpcb.com/partdetail/C5373003) | 2.4–40 V push-pull comparator, SOT-23-5 |
| U31 | [LM4040AIM3-2.5/NOPB / C139302](https://jlcpcb.com/partdetail/C139302) | 2.5 V A-grade reference, SOT-23 |
| Q5 | [AO3400A / C20917](https://jlcpcb.com/partdetail/C20917) | 30 V brake MOSFET, SOT-23 |
| R121–R124 | [RC2512JK-7W47RL / C136992](https://jlcpcb.com/partdetail/C136992) | Four 47 Ω, 5%, 2 W resistors, 2512 |

Catalog identity was checked; stock and assembly eligibility are not reserved.
Refresh the complete BOM in the selected JLCPCB assembly service before ordering.
Do not substitute the DRV8316T hardware-controlled variant or the different RNQ
package. The encoder's SPI word length does not establish its effective resolution.

Custom land patterns in MagMouse.pretty follow TI drawing 4224999/B, June 2021,
and MPS MA735 Rev. 1.0 page 28. RGF lands are 0.25 × 0.60 mm on 0.5 mm pitch;
EP41 is 3.7 × 5.7 mm with twelve 1.05 × 1.15 mm paste apertures, approximately
69% coverage for TI's 0.125 mm stencil example. Thermal vias remain a board-layout
task. The encoder uses 0.4 mm pitch, 0.20 mm land width and eight 0.10 mm inner
corner chamfers. Only pin 1 is 0.75 mm long, with its centre shifted inward by
0.025 mm to keep the outer edge aligned; the other 13 lands are 0.70 mm long.
No thermal pad may be added to its 14-pad package.
Assembly orientation, stencil thickness and final mask clearances still need review.

The driver symbol marks its second bonded pad of each phase (14, 17, 20) passive;
13, 16, 19 represent the corresponding output driver. This avoids falsely modelling
two independent output stages. Both physical pads of every phase must be routed.
R125 explicitly connects U28 QOD to its output; it is a removable zero-ohm
discharge link, not another supply. No ERC waiver was added for either case.

## Hardware shutdown and driver startup

U22 derives WHEEL_RUN_EN = ACT_DRIVE_EN AND WHEEL_RUN_REQ and gates all three
PWM commands. It also drives INLA/B/C. Q4 pulls DRVOFF low only while RUN is
permitted; R82 otherwise pulls DRVOFF to the driver's own AVDD. Low PWM alone
is not an output-disable condition. R83/R84/R90–R92 establish low defaults.
The existing heartbeat/reset/source interlock supplies ACT_DRIVE_EN.

nSLEEP follows ACT_DRIVE_EN so configuration is possible with RUN low. After
each wake or driver power loss, firmware must wait for startup, unlock the
configuration registers as specified by TI, configure and read back at least:

- PWM_MODE = 10b: 3-PWM with analog SOx outputs. Reset defaults to 6-PWM.
- CSA_GAIN = 11b: initial 1.2 V/A gain; calibrate offset and gain.
- BUCK_DIS = 1. The unused buck still has TI's R81 = 22 Ω and C50 = 22 µF
  termination from SW_BK to FB_BK/output. Its pins are not grounded or floated.
- Select the 200 V/µs slew-rate setting for the initial sampling timing budget.
  Measure switching delay and EMI before selecting a slower edge rate.
- Use latched fault handling; require an explicit recovery sequence. Do not
  automatically resume torque after a fault or stale current/angle sample.

Only then initialize bounded PWM and request RUN. The mode exposing SOx does
not provide the alternative 3-PWM cycle-by-cycle current-limiting mode. The
existing input eFuse is not a substitute for phase-current control. Begin with
a provisional phase-current target no greater than 0.5 A, on a current-limited
bench supply; motor winding and thermal measurements determine the real limit.

## Power domains and SPI

DRV_AVDD powers U23 AVDD/DVDD, the driver VREF and forward buffers U24/U26.
Thus the ADC input range follows the CSA supply and disappears with the driver.
The 3.1–3.465 V AVDD rail permits up to 30 mA external load. ADC analog current
is below 0.6 mA in the specified full-rate cases; digital current is typically
sub-mA. A screening estimate using six buffer channels, 15 pF typical internal
capacitance plus 20 pF load per channel at 20 MHz is about 14.6 mA at 3.465 V.
This intentionally overcounts simultaneously switching signals but is not a
maximum-current guarantee. Verify actual AVDD load, ripple, temperature and
startup; do not add other loads to this rail without revisiting the budget.

ENC_3V3 comes from U28, enabled by HALL_EN. U27 and its forward buffer U29 share
that switched supply. TEST and SSCK are grounded; unused MA735 outputs are NC.
U25 runs from system +3V3 and returns driver/encoder MISO to SPI2, ADC2 MISO to
SPI3, and driver fault to DRV_FAULT_N. Its MISO output enables use the respective
host CS signals. Never assert two SPI2 device selects simultaneously.

Correction, 2026-09-10: SN74LVC125A does **not** have guaranteed Ioff protection.
Its overvoltage-tolerant inputs and destination-powered outputs must be reviewed
by direction: no output may be pulled or externally driven above its own dead
supply. This topology avoids a direct host SPI output into the ADC/encoder pins,
but does not by itself establish partial-power-down or ramp acceptance. Output
clamp current, startup glitches and bus contention still require review and
measurement. See [modular interface review](../modular/INTERFACE_REVIEW.md).
R87 is the required pull-up for the driver's open-drain SDO. Start driver register
access at **1 MHz**, mode 1, with at least 400 ns CS-high time; the former 5 MHz
interface ceiling is not accepted with this pull-up and unmeasured capacitance.
ADC2 remains mode 0, 20 MHz target; MA735 mode 3, 10 MHz target.

R88/R89 bias nFAULT from DRV_AVDD, not from the MCU supply. At minimum AVDD and
the checked resistor corners its high level is at least 2.809 V, above TI's
2.2 V power-up requirement to avoid test mode. Loss of AVDD pulls the return low.

## Current and angle acquisition

ADC2 CH0/1/2 receive SOA/B/C through R102–R104 = 330 Ω and C59–C61 = 22 pF,
the TI starting filter values. The simple RC cutoff is 21.9 MHz; this is an ADC
interface filter, not strong PWM-frequency rejection. CH3–7 are grounded through
removable zero-ohm links; no wheel bus-current sensor is populated.

At 1.2 V/A, SOx is centred at VREF/2. At minimum 3.1 V AVDD, the ideal linear
range is approximately ±1.08 A before error margins; nominal 3.3 V ADC scale is
about 0.67 mA/LSB. TI specifies up to ±50 mA equivalent zero-current offset and
±10.5% gain error below 4 A across temperature. Calibrate each phase; nominal
ADC resolution does not imply milliampere absolute accuracy.

Samples are sequential and valid only in appropriate low-side conduction states.
The driver specifies up to 1.05 µs input-to-output delay at its fastest slew
setting under the stated test conditions, and typical 1 µs CSA settling to 1%
with a 30 pF load. The settling guard target is therefore increased to 3 µs.
Together with an 8 µs burst target and 1 µs launch-jitter target, this consumes
the proposed 12 µs common low-side window. These are unverified targets;
there is no spare time in that budget. Slower slew rates require a new budget.
Include buffer delay, GPIO-matrix delay, ADC acquisition loading and pipeline
flush in the real measurements. See [interfaces](../../docs/interfaces.md).

Use MA735's 64 µs filter window initially, about 9-bit effective resolution;
its 16 ms high-resolution setting is unsuitable for the proposed fast loop.
Check actual angle age, startup, magnet strength/alignment, motor pole pairs,
electrical zero and current/angle timestamp alignment. No firmware is implemented
by these schematic changes.

## Autonomous brake and provisional limits

U30, U31 and Q5 are powered directly from ACT_5V. They need neither +3V3 nor
an ESP32 output, including during unplugging or MCU reset. R111 biases the 2.5 V
reference. R112 + R113 = 134.8 kΩ, R114 = 100 kΩ and R115–R117 = 3 MΩ provide
positive feedback. U30 drives Q5 through 100 Ω; R120 holds the gate low when
the comparator is unpowered. D2 remains secondary transient protection.

With top/bottom/feedback resistances Rt/Rb/Rh and comparator reference Vr:

    Von  = Vr × (1 + Rt/Rb + Rt/Rh) - VOL × Rt/Rh
    Voff = [Vr × (1 + Rt/Rb + Rt/Rh) + (Vrail - VOH) × Rt/Rh] / (1 + Rt/Rh)

The static check includes ±1.7% resistor bounds (1% initial plus temperature),
±1% reference allowance, ±4 mV comparator offset plus 0.1 mV bias allowance,
and 0–0.25 V output rail offsets. This review envelope is **−40 to +85°C**,
limited by the selected reference grade, not the wider comparator rating.

| Calculated quantity | Result |
| --- | --- |
| Nominal turn-on / release | 5.982 / 5.725 V |
| Turn-on across checked corners | 5.787–6.174 V |
| Release across checked corners | 5.552–5.915 V |
| Minimum hysteresis within one corner | 0.220 V |
| Equivalent brake resistance | 11.75 Ω |
| Dissipation while on at 6 V | 3.064 W total, 0.766 W per resistor |

Ranges overlap across different manufactured boards; each individual checked
corner retains positive hysteresis. Release has at least 50 mV margin above
the assumed 5.5 V maximum normal rail. Thresholds are prototype selections,
not a certified overvoltage limit or an energy rating.

The comparator's specified low output is below the MOSFET's minimum threshold.
At 4.5 V gate drive the MOSFET has at most 32 mΩ specified on resistance under
the datasheet test conditions: conduction loss at 0.4 A is about 5 mW before
temperature rise. Switching loss and SOA during gate transitions remain open.
The resistors are rated 2 W each at 70°C under their specified conditions;
their aggregate 8 W rating is not an enclosed-mouse cooling budget.

Initial monitored bench envelope: **0.4 A peak returned rail current, 0.5 W
average returned power, at least 47 µF effective ACT capacitance, running brake
response no slower than 10 µs, and measured peak ACT voltage below 6.5 V**.
The eleven 10 µF capacitors C8/C11/C14, C37–C40, C44–C45 and C68–C69 give
110 µF nominal bulk storage, plus 0.7 µF of direct rail bypass. The earlier
80 µF count omitted the three button-driver bulk capacitors. Bias,
tolerance and temperature must establish the 47 µF minimum. Add capacitance or
reduce the envelope if they do not. At 0.4 A and 47 µF, a 10 µs delay adds
0.085 V, giving a conditional 6.259 V peak from the highest static threshold.

TLV1811 can hold its output low for up to 200 µs after crossing 2.4 V on startup.
Under the same current/capacitance assumptions, the rail reaches about 4.102 V
during that delay, below brake turn-on. This arithmetic does not simulate the
reference ramp, motor diode rectification or sudden energy pulses. Test slow
and fast startup from a discharged rail, USB removal, brownouts, continuous
hand rotation, abrupt stops, repeated detents and MCU-held-reset operation.
Record rail overshoot and resistor/MOSFET/board/enclosure temperatures. A shorted
Q5 or comparator/reference failure is not covered by the normal-operation clamp.

## Reproducible checks and remaining gates

    python hardware/kicad/export_review.py
    python hardware/kicad/export_review.py --schematic hardware/encoder/Encoder.kicad_sch
    python hardware/kicad/verify_encoder.py
    python hardware/kicad/test_encoder_checks.py
    python hardware/kicad/verify_power.py
    python hardware/kicad/verify_resources.py
    python hardware/kicad/verify_wheel.py
    python hardware/kicad/test_wheel_checks.py
    python hardware/kicad/export_pcb_review.py

The wheel checker verifies 266 pin connections, 32 shutdown combinations,
22 part identities, 58 custom land geometries and 128 brake corners across both
board netlists. Five tests include a passing baseline and faults in shutdown,
brake/ADC supply domains, the 33 Ω catalog number and brake divider.
Both projects pass native ERC, physical DRC and parity without new exclusions.
After the [actuator distribution routing pass](../pcb/ACTUATOR_DISTRIBUTION_LAYOUT.md), the motherboard has 247
native unrouted connections (also 247 DRC entries). Wheel phases, current sensing,
PWM/enable/fault wiring and brake power/control are connected. U21 has four direct
thermal vias requiring filled/capped fabrication; temperature and transient
acceptance remain open. The encoder is fully routed with zero unconnected items. Eight encoder
tests check the baseline and seven connector, harness and split faults.

Subsequent revisions add ICM-42688-P/RGB and PMW3360 optics; see
[optical design](OPTICAL_DESIGN.md) for the motion-burst scheduling constraint.
The [60 mm motherboard pass](../pcb/PLACEMENT_60MM.md) places the wheel
motherboard circuitry. Revision 0.8 moves U27/C62 to the separate
[upright encoder board](../encoder/README.md), adds J6/J7 JST SH headers and
checks the pin-to-pin harness. U28, U29 and U25 remain on the motherboard;
power-off isolation and GPIO allocation are unchanged. Wheel timing, cable
waveforms, regeneration energy and mechanical qualification remain open.
Before routing, settle PCB-first mounting interfaces, motor/encoder magnetic alignment, sensor
aperture, Hall/paddle locations, wire clearance, brake cooling and the production
stackup. Bench timing and energy results remain electrical acceptance gates.

## Manufacturer evidence

- [TI DRV8316, SLVSF16B, April 2022](https://www.ti.com/lit/ds/symlink/drv8316.pdf): pinout, modes, shutdown, CSA, unused-buck termination and RGF land/stencil drawings.
- [TI ADS7038, SBAS979C, September 2024](https://www.ti.com/lit/ds/symlink/ads7038.pdf): supply domains, reference, input and conversion timing.
- [MPS MA735, Rev. 1.0, April 2022](https://www.monolithicpower.com/en/documentview/productdocument/index/version/2/document_type/Datasheet/lang/en/sku/MA735GGU/): pins, filter settings and UTQFN land pattern.
- [TI SN74LVC125A, SCAS290T, September 2024](https://www.ti.com/lit/ds/symlink/sn74lvc125a.pdf): input tolerance, output clamp constraints, supply range and propagation/loading limits; no Ioff guarantee.
- [TI TPS22919, SLVSEN5B, May 2019](https://www.ti.com/lit/ds/symlink/tps22919.pdf): load switching, ON thresholds and QOD connection.
- [TI TLV1811, SNOSDC8E, July 2025](https://www.ti.com/lit/ds/symlink/tlv1811.pdf): output levels, offset, power-on reset and external hysteresis.
- [TI LM4040-N, SNOS633N, August 2025](https://www.ti.com/lit/ds/symlink/lm4040-n.pdf): reference grade, bias and temperature bounds.
- [AOS AO3400A](https://www.aosmd.com/res/data_sheets/AO3400A.pdf): gate drive, resistance, charge and SOA.
- [YAGEO RC2512JK-7W47RL specification](https://www.yageogroup.com/component-documentation/download/specsheet/RC2512JK-7W47RL): resistance, 2 W at 70°C and temperature coefficient.
