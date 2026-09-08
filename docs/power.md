# USB-C power control — revision 0.3

The [KiCad circuit](../hardware/kicad/README.md) connects USB-C to protected logic
and actuator supplies. Source detection, current limits, soft-start, reverse
blocking, telemetry, sensor shutdown and the hardware heartbeat interlock are
implemented. Firmware and bench acceptance remain open; this is not a USB
compliance result. See [component and package evidence](../hardware/kicad/POWER_REVIEW.md).

## Source capability and operating budgets

U11, TUSB320LAIRWBR, is strapped as a sink in GPIO mode. Its internal Rd supports
unpowered attachment. Do not add parallel Rd resistors. U20 protects CC1/CC2;
R25 is 887 kOhm for VBUS detection. OUT1/OUT2 have 100 kOhm pull-ups to the
detector's own 3.3 V supply. There is no negotiation of voltages above 5 V.

| CC OUT1 / OUT2 | Detected state | U12 nominal input fault threshold | Initial firmware operating ceiling |
| --- | --- | --- | --- |
| H / H | Unattached / unknown | 0.503 A | Actuators and Hall sensors off |
| H / L | Default USB | 0.503 A | 100 mA before configuration; 400 mA after a 500 mA configuration is granted; haptics off |
| L / H | Type-C 1.5 A | 1.212 A | 1.0 A total input; reduced haptics after reserving logic power |
| L / L | Type-C 3 A | 2.556 A | 2.0 A total input; reserve logic power and respect the actuator branch limit |

These are provisional ceilings, not predicted consumption. Initially keep even
higher-current sources within 100 mA until USB configuration. Disable radios,
start at a low CPU clock, and measure ROM boot, application boot and enumeration.
If that cannot meet 100 mA, revise the startup architecture before claiming
default-port compatibility. A 3 A advertisement does not allocate 3 A to haptics.

Q1/Q2 change the input current-setting resistance directly from CC-derived logic;
firmware cannot select a higher setting. R56+R57+R58 = 6.633 kOhm. R59 adds
4.7 kOhm in parallel for 1.5/3 A; R60/R61 add 3.3 kOhm || 10 kOhm for 3 A.
The nominal equation is ILIM = 3334 / RILM, with resistance in ohms.
Conservative screening gives 1.41 A for medium (+15% device allowance and -1%
resistance) and 2.84 A for high (+10% and -1%). Measure real thresholds and
transitions. MOSFET on resistance can only lower this programmed allowance.

**U12 is fault protection, not a 100/500 mA USB compliance limiter.** Its default
threshold can exceed 500 mA with tolerance. ITIMER is NC for fastest response,
but the current-limit loop still allows brief transient excess current.
Firmware must control ordinary demand. Do not infer a 900 mA allowance for
this Full-Speed device from a USB 3 host connector.

The [USB-IF system overview](https://www.usb.org/sites/default/files/D1T1-2%20-%20USB%20Type-C%20System%20Overview.pdf)
distinguishes Type-C current from state-dependent default USB power. Check the
applicable specifications and [compliance updates](https://compliance.usb.org/index.asp?UpdateFile=Electrical)
during final electrical review.

## Power paths

VBUS_USB → U12 → PWR_5V → U2 → +3V3 powers logic.
PWR_5V → U13 → ACT_5V powers the button bridges.
U12/U13 are TPS259470LRPWR active-current-limit eFuses with adjustable OVLO
and reverse blocking. The 472 and 474 variants are not equivalent substitutes.

| Function | Network | Calculated nominal |
| --- | --- | --- |
| Input UVLO | R29/R30 | 3.852 V rising / 3.499 V falling |
| Input OVLO | R31-R35 | 6.0 V rising; approximately 5.8-6.3 V with threshold/resistor/leakage tolerances |
| Actuator UVLO | R36-R39 | 4.80 V rising / 4.36 V falling |
| Actuator input OVLO | R40/R41 | 6.63 V rising |
| Actuator branch current limit | R42 || R43 | 2.02 A |
| Both rail ramps | C25/C26, 10 nF | 0.2 V/ms; about 25 ms to 5 V |
| ACT capacitor-only inrush | 70 uF nominal | About 14 mA; other loads are additional |

D3 clamps U13 EN low when ACT_DRIVE_EN is low. High-value EN/OVLO dividers
reduce standby demand. The driver still has its own undervoltage protection:
4.36 V is below its 4.5 V minimum operating supply, so firmware must stop effects
on droop instead of attempting force regulation through undervoltage.

The eFuse fault outputs and U2 power-good pull MCU_EN low through separate
1 kOhm resistors, limiting reset-capacitor discharge current. Overcurrent causes
current limiting and FLT; thermal shutdown latches the selected L variant.
UVLO/OVLO open the power path without asserting FLT. Test recovery separately;
firmware must always boot with actuator requests low.

U2 is now **TPS62162DSGR**, fixed 3.3 V, 3-17 V input, 1 A output. It replaces
the TLV62569, whose 5.5 V input ceiling left insufficient transient margin, and
removes its R1/R2 feedback divider. L1 is SWPA4020S3R3MT, 3.3 uH; C2/C3/C23
provide 30 uF nominal local output capacitance. The 1 A logic target remains
subject to thermal, effective-capacitance and transient validation. Route VOS
to the regulated output and follow TI's AGND/PGND guidance.

D1, **SMBJ12A**, protects U12's input against transients; U12 OVLO protects the
downstream rails. The TVS's 19.9 V specified pulse clamp is below U12's 28 V
absolute maximum. Verify hot-plug/surge coordination at U12 and U2, including
overshoot before the eFuse opens. This remains a 5 V sink, not a general-purpose
high-voltage input.

## Hardware interlock and startup

GPIO16 ACT_REQ, GPIO17 ACT_HEARTBEAT and GPIO18 SENS_REQ default low through
external resistors. HALL_EN = SENS_REQ AND MCU_EN enables the three Hall sensors.
ARM_VALID requires SOURCE_OK, ACT_REQ and HALL_EN. Default/unknown source,
reset, sensor shutdown or request removal clears the monostable immediately.

U15, SN74LVC1G123DCUR, has A grounded, B driven by the software heartbeat,
and CLR driven by ARM_VALID. R46 = 10 kOhm and C27 = 1 uF give approximately
10 ms timeout. This is a calculated nominal, not a guaranteed corner limit.
Initial bench acceptance target: drive gates low within 15 ms of the final
heartbeat edge, including timing-factor, capacitor, voltage and temperature
variation. Change the network if that target is not met.

A held-high heartbeat can trigger one pulse when CLR rises, then expires.
Firmware should refresh every 1 ms from the control task after validating sensor
freshness, USB state and effect limits. Do not use autonomous PWM for heartbeat.
A continuing heartbeat does not independently enforce each effect's duration
or detect every possible firmware error.

ACT_DRIVE_EN = monostable Q AND ARM_VALID. It controls U13 and gates all six
button inputs through U17/U18. Driver-side pulldowns remain; command-side
pulldowns prevent floating logic inputs during reset. Drive stops even while
the ACT capacitors retain energy.

For bring-up: hold commands low, enable sensors, obtain valid readings, check
CC status/VBUS presence, then start heartbeat and arm. Hold commands low for
at least 50 ms and require ACT voltage at least 4.7 V before pulsing.
Stop on droop, stale data, source downgrade, USB deconfiguration or fault.
Validate final voltage hysteresis with the actual cable and load.
Coil current, force and duty-cycle limits depend on the
[button experiment](../mechanical/button-mechanisms/README.md).

## Suspend, resume and telemetry

On USB suspend, deconfiguration or bus reset, clear ACT_REQ and all commands,
stop heartbeat, clear SENS_REQ, stop ADC conversions and disable radios and
other future loads. Hall outputs become high impedance; ADS7038 consumes little
power without conversions. Retain the USB state required for host resume; do not
assume an ESP32 sleep mode preserves it.

Initial acceptance requires **at most 2.5 mA at the connector in suspend**,
including all ICs, divider currents, MCU/USB PHY and leakage. D1 has a 1 uA
specified leakage ceiling at standoff; D2 is behind the disabled actuator switch.
Establish the remaining MCU/PHY allowance by measurement. CC detection does not
detect USB data-bus suspend: firmware must handle the USB event. A healthy
control task that ignores suspend can continue its heartbeat.

Do not advertise device-initiated remote wake until a low-power wake path is
implemented and tested; this policy turns the Hall sensors off. Resume must
revalidate capability and sensors before rearming.

Q3 supplies **VBUS_PRESENT_N** to GPIO1 with a 3.3 V pull-up. Its gate divider
and filter isolate the GPIO from raw VBUS, including when logic is off.
This is coarse presence detection, not a precision voltage measurement.

ADS7038 AIN6 measures U12 ILM through unity-gain U19 and a 1 kOhm / 100 nF
filter. The buffer isolates ADC sampling from the current-setting resistor.
Nominally I = VADC / (182e-6 × RILM). Select RILM using the CC state captured
with the sample; discard transition samples and calibrate gain/offset.
Low-current accuracy still needs measurement.

AIN7 measures ACT_5V through 100 kOhm / 22.1 kOhm and 100 nF:
VACT = VADC × 122.1 / 22.1; nominal filter time constant 1.81 ms.
D4 shunts residual monitor voltage to the ADC supply during power loss.
The 100 kOhm resistor limits this alternate path to about 100 uA at a 10.3 V
rail. Verify ADC pin voltage/injection and logic discharge on unplug/regeneration.
These are supervisory signals; wheel phase-current acquisition still needs a
separate path. All eight ADS7038 channels are allocated.

## Regeneration and validation before layout

U13 blocks regenerative power into PWR_5V; U12 blocks return to the host.
C37-C40 plus the three driver bulk capacitors give 70 uF nominal storage.
R69, 1 kOhm, gives a nominal 70 ms discharge constant and about 30 mW at 5.5 V.
Hardware command gating does not wait for that discharge.

D2, SMBJ6.0A, absorbs excess pulse energy locally. At 25 C its standoff is 6 V,
breakdown 6.67-7.37 V and specified pulse clamp 10.3 V. Temperature and layout
change the result. The 600 W rating applies to a specified pulse and copper
area, not continuous dissipation. This path is for characterization of button
pulses; it is not an accepted continuous wheel brake. Resolve wheel energy and
any brake resistor/chopper before freezing that subsystem.

Record oscilloscope/current measurements for both orientations and default,
1.5 A and 3 A sources: startup/enumeration, inrush, source transitions,
suspend/resume, missing/stuck heartbeat, reset, short circuit, UVLO/OVLO,
disconnect under load, reverse current and regeneration. Start with a
current-limited supply and one characterized coil. Calculate winding energy
from measured L and I, and integrate actual returned power. Validate overshoot,
pulse/thermal ratings, capacitor bias, passive return, cable drop and repeated
clicks. These physical tests remain open.
