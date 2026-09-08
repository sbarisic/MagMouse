# Wheel control implementation contract

This is the next block after the revision 0.4 GPIO allocation, not an implemented
wheel circuit. Use DRV8316R, a second ADS7038, MA735 and the encoder-free GB1806,
subject to exact package and motor review. See [signal reservations](interfaces.md).

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
The output-disable gates and driver are not yet drawn; sheet 09 only reserves
the MCU interfaces and establishes the request's low reset default.

## Current and angle feedback

ADC2 CH0/1/2 are reserved for conditioned SOA/B/C. Review VREF, input range,
filters and power-off injection together. Low-side current is only valid in
appropriate switching states. Confirm gain, offset and settling at the actual
small wheel currents. CH3 stays optional until a bus-current sensor is chosen;
CH4-7 remain spare. Do not put slower housekeeping conversions inside the
time-critical three-phase acquisition burst.

Use MA735 SPI absolute angle; no ABZ/index/PWM connection is required in V1.
Bound angle age in the shared-bus scheduler. Check magnet alignment,
interference, filtering and electrical-angle calibration on the actual motor.
The dedicated ADC bus still needs [sampling-deadline validation](interfaces.md#wheel-acquisition-timing-gate).

Bring up with WHEEL_RUN_REQ low: obtain valid power, wait for driver startup,
configure/read back mode and gain, establish valid angle/current samples,
initialize bounded PWM, then request run. Reset, timeout and lost permit must
remove drive without another SPI transaction.

## Regenerative-energy path

The existing TVS/capacitors support pulse characterization. Determine a local,
hysteretic comparator-controlled brake MOSFET/resistor from measured wheel
energy. It must protect a charged ACT rail after USB removal, MCU reset and
heartbeat loss, without depending on an upstream supply that has disappeared.
Keep the TVS as secondary transient protection. No MCU GPIO is reserved for
brake activation; the comparator must act autonomously.

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

1. DRV8316, ADC2, MA735, motor interface, hardware disable and brake circuit.
2. Exact PAW3950 reference, optics and initialization; resolve OPT_CTRL behavior.
3. ICM-42688-P, INT1 and internal clock.
4. Addressable RGB with suitable supply/data interface; preserve GPIO45's low
   boot strap and the USB suspend budget.

The allocation stabilizes MCU connections. Missing reference material and
unmeasured motor/timing behavior still constrain circuit and layout approval.
