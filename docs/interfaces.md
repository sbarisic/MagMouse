# Preliminary interface allocation

This is a logical signal inventory. The [KiCad starter](../hardware/kicad/README.md)
assigns provisional GPIOs for buttons and the ADC; the full-system module pin,
boot, peripheral and timing budget is still open. Do not route a PCB from this
table alone.

| Function | Signals / connections | Design work remaining |
| --- | --- | --- |
| Native USB | GPIO19 D-, GPIO20 D+; GPIO1 VBUS_PRESENT_N | Data/CC protection and presence sensing drawn; route USB pair and validate USB states |
| Shared SPI proposal | SCLK, MOSI, MISO | Per-device modes, clock limits, arbitration and loading |
| PAW3950 | CS_PAW, motion interrupt, reference-design power/reset signals | Circuit, optics, initialization/SROM availability and license |
| ICM-42688-P | CS_IMU, interrupt | Supply/interface mode and interrupt policy |
| ADS7038 | CS_ADC; eight analog channels below | Acquisition schedule, settling, scaling and supply accuracy |
| MA735 | CS_WHEEL | Read latency, angle calibration and magnetic interference |
| DRV8316R | CS_DRV, 3- or 6-PWM, enable/sleep and fault signals as required | PWM mode, current feedback acquisition and FOC timing |
| DRV8231A x3 | GPIO4-9 CMD pairs through hardware gates to IN1/IN2; VREF/IPROPI and stationary coil | Validate PWM/decay, current scaling, wake latency and shutdown timing |
| RGB LED | Three controlled channels | Polarity, resistors and output capability |
| Type-C capability | TUSB320 CC detector; GPIO14 OUT1, GPIO15 OUT2 | Hardware decode implemented; validate orientation and capability-loss behavior |
| Actuator interlock | GPIO16 ACT_REQ, GPIO17 ACT_HEARTBEAT | Firmware refresh after valid control iteration; verify approximately 10 ms timeout |
| Sensor enable | GPIO18 SENS_REQ; HALL_EN qualified by MCU_EN | Hall shutdown on reset/suspend; verify settling before sampling |
| Recovery | EN/reset, GPIO0/boot, UART/test pads, 3V3, GND | Module boot requirements and accessible programming |

The USB GPIO assignment and 22/33-ohm series resistor guidance come from
[Espressif's hardware guidance](references.md). The starter assigns GPIO4-9 to
left/middle/right CMD1/CMD2 pairs and GPIO10-13 to ADC_CS, SPI_MOSI, SPI_SCLK and
SPI_MISO respectively. CMD signals now pass through reset/timeout-qualified
gates before reaching driver IN pins. Power control also assigns GPIO1 and
GPIO14-18 as listed above. Remaining allocation is open; these choices are provisional.

## ADS7038 analog channels

| Channel | Source | Meaning |
| --- | --- | --- |
| CH0 | Left TMAG5253 | Left button position |
| CH1 | Middle TMAG5253 | Middle button position |
| CH2 | Right TMAG5253 | Right button position |
| CH3 | Left DRV8231A IPROPI | Left actuator current feedback |
| CH4 | Middle DRV8231A IPROPI | Middle actuator current feedback |
| CH5 | Right DRV8231A IPROPI | Right actuator current feedback |
| CH6 | U12 ILM through TLV9001 buffer | Total input-current monitor; gain depends on detected CC mode |
| CH7 | ACT_5V divided by 100 kOhm / 22.1 kOhm | Actuator rail voltage and ramp/droop supervision |

Verify sensor output ranges against ADC inputs and design each IPROPI resistor
and filter. Interpret current readings with the selected driver mode and PWM
sampling phase. ADC headline throughput alone does not establish loop bandwidth.
Wheel current feedback still requires an explicit acquisition path; no ADC
channels remain spare. See [power telemetry scaling](power.md).

## Button driver controls

The [DRV8231A datasheet](https://www.ti.com/lit/ds/symlink/drv8231a.pdf)
defines two control inputs, IN1 and IN2,
with VREF setting the current-regulation threshold and IPROPI providing feedback.
There is no dedicated nSLEEP or nFAULT pin. Both inputs low disable the bridge
and enter sleep after the specified delay. Budget wake time in click latency.
Revision 0.3 adds command/input pulldowns, hardware AND gates, a heartbeat
monostable and a switched actuator supply. Validate this complete path before
layout; firmware still owns sensor freshness, pulse bounds and USB suspend.

Check IPROPI validity and accuracy during drive, decay and current reversal at
the small currents used for clicks. Do not treat it as an always-valid signed
measurement of coil current. Map actual polarity to paddle force on the bench.
Choose fixed or adjustable VREF circuitry without assuming an available DAC.

## Pin-allocation acceptance criteria

- Count every chip select, PWM, interrupt, fault, enable, and recovery signal.
- Check module-exposed pins, reserved flash pins, strapping states, and USB pins.
- Confirm timer/PWM synchronization, dead-time responsibilities, and ADC latency.
- Specify safe boot/reset levels and fault shutdown independent of normal tasks.
- Record the final GPIO table and schematic net names together.
