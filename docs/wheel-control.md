# Wheel control implementation contract

Revision 0.5 implements DRV8316R, a second ADS7038, MA735, GB1806 phase-wire
pads, hardware shutdown and an autonomous brake in sheets 10–13. Firmware and
motor validation remain open. See [the circuit review](../hardware/kicad/WHEEL_REVIEW.md)
for exact parts, power domains, calculations and bench limits, and [interfaces](interfaces.md)
for the unchanged GPIO map.

## Driver configuration and shutdown

Select 3-PWM with analog current outputs: PWM_MODE = 10b. The 11b current-limit
mode does not expose the SOx signals required by this architecture. Configure
and read back the mode while disabled; power-up defaults to 6-PWM.

WHEEL_PWM_A/B/C feed INHA/B/C through external gates. Derive WHEEL_RUN_EN from
WHEEL_RUN_REQ AND ACT_DRIVE_EN; use it for INLA/B/C and PWM gating. Assert
DRVOFF whenever running is not permitted. Three low PWM commands alone are
not high-impedance shutdown. Derive nSLEEP from the actuator permit so SPI
configuration is possible with DRVOFF asserted. This separates wake/configure
from torque enable without another MCU pin.

Choose driver-domain defaults that work while the MCU is unpowered. Fault clear
can use SPI; power/sleep recovery must reinitialize configuration. DRV_FAULT_N
has a dedicated MCU/MCPWM input. A combinational fault gate alone is not a
latched fault mechanism. The unused buck still requires TI's specified external
termination; do not simply ground or float its pins.

These requirements follow [TI DRV8316 SLVSF16B, April 2022](https://www.ti.com/lit/ds/symlink/drv8316.pdf).
U22 implements the AND gates; Q4/R82 assert DRVOFF while RUN is low. U21 nSLEEP
follows ACT_DRIVE_EN. R81/C50 terminate the unused buck with 22 ohms/22 uF;
set BUCK_DIS = 1 after wake. Begin driver SPI at 1 MHz and read back all required
configuration before RUN. Reset must restore these settings before torque resumes.

## Current and angle feedback

ADC2 U23 CH0/1/2 receive SOA/B/C through 330 ohm/22 pF filters. Its analog and
digital supplies share DRV_AVDD with VREF; U24–U26/U29 isolate SPI power domains.
Low-side current is only valid in
appropriate switching states. Confirm gain, offset and settling at the actual
small wheel currents. CH3 stays optional until a bus-current sensor is chosen;
CH3–7 are presently grounded through removable zero-ohm links. Do not put slower housekeeping conversions inside the
time-critical three-phase acquisition burst.

Use MA735 SPI absolute angle; no ABZ/index/PWM connection is required in V1.
Bound angle age in the shared-bus scheduler. Check magnet alignment,
interference, filtering and electrical-angle calibration on the actual motor.
The dedicated ADC bus still needs [sampling-deadline validation](interfaces.md#wheel-acquisition-timing-gate).

Bring up with WHEEL_RUN_REQ low: obtain a stable ACT rail of at least 4.5 V,
wait for driver startup, configure/read back mode and gain, establish valid angle/current samples,
initialize bounded PWM, then request run. Reset, timeout and lost permit must
remove drive without another SPI transaction.

## Regenerative-energy path

U30 TLV1811, U31 LM4040 and Q5 switch four parallel 47 ohm / 2 W resistors.
The entire brake operates from ACT_5V with nominal 5.982 V turn-on and 5.725 V
release. It is independent of MCU reset, heartbeat and upstream power. D2 remains
secondary transient protection. The resistor/threshold selections are provisional;
validate them against measured wheel energy and the documented startup/thermal
envelope before accepting regenerative operation. No MCU GPIO is consumed.

Measure back-driven speed, winding resistance/inductance, phase current and
returned power. Resistor dissipation is approximately Vrail squared / R while
enabled. Check pulse energy, average heating, MOSFET SOA, copper area and
fault cases. Capacitor energy margin is 0.5 C (Vhigh squared - Vlow squared),
using effective capacitance. Motor advertised wattage is not a brake-resistor
specification.

Set thresholds above maximum normal ACT voltage and below validated rail
limits, with tolerance, hysteresis and overshoot margins. Keep brake-current
returns away from sensor/reference returns. Test repeated detents, continuous
hand rotation, abrupt stops, unplugging and braking with MCU reset asserted.
Firmware must also bound commanded torque and temperature.

## Remaining schematic order

1. Exact PAW3950 reference, optics and initialization; resolve OPT_CTRL behavior.
2. ICM-42688-P, INT1 and internal clock.
3. Addressable RGB with suitable supply/data interface; preserve GPIO45's low
   boot strap and the USB suspend budget.

The allocation stabilizes MCU connections. Missing reference material and
unmeasured motor/timing behavior still constrain circuit and layout approval.
