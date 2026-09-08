# Preliminary interface allocation

This is a logical signal inventory. GPIO numbers remain **TBD** until the exact
ESP32-S3-MINI-1-N8 module pinout, boot constraints, peripheral routing, and timing
budget are checked. Do not route a PCB from this table alone.

| Function | Signals / connections | Design work remaining |
| --- | --- | --- |
| Native USB | GPIO19 D-, GPIO20 D+ | ESD, series resistors, connector routing and VBUS detection |
| Shared SPI proposal | SCLK, MOSI, MISO | Per-device modes, clock limits, arbitration and loading |
| PAW3950 | CS_PAW, motion interrupt, reference-design power/reset signals | Circuit, optics, initialization/SROM availability and license |
| ICM-42688-P | CS_IMU, interrupt | Supply/interface mode and interrupt policy |
| ADS7038 | CS_ADC; eight analog channels below | Acquisition schedule, settling, scaling and supply accuracy |
| MA735 | CS_WHEEL | Read latency, angle calibration and magnetic interference |
| DRV8316R | CS_DRV, 3- or 6-PWM, enable/sleep and fault signals as required | PWM mode, current feedback acquisition and FOC timing |
| DRV8874 x3 | Per-driver control, sleep, fault, current-reference and IPROPI circuits | Control mode, PWM resources, current regulation/scaling |
| RGB LED | Three controlled channels | Polarity, resistors and output capability |
| Type-C capability | CC1/CC2 to sink/current-detection circuitry | Detector, orientation handling and capability-loss response |
| Recovery | EN/reset, GPIO0/boot, UART/test pads, 3V3, GND | Module boot requirements and accessible programming |

The USB GPIO assignment and 22/33-ohm series resistor guidance come from
[Espressif's hardware guidance](references.md). Other GPIO allocation is open.

## ADS7038 analog channels

| Channel | Source | Meaning |
| --- | --- | --- |
| CH0 | Left TMAG5253 | Left button position |
| CH1 | Middle TMAG5253 | Middle button position |
| CH2 | Right TMAG5253 | Right button position |
| CH3 | Left DRV8874 IPROPI | Left actuator current feedback |
| CH4 | Middle DRV8874 IPROPI | Middle actuator current feedback |
| CH5 | Right DRV8874 IPROPI | Right actuator current feedback |
| CH6 | Unassigned | Spare |
| CH7 | Unassigned | Spare |

Verify sensor output ranges against ADC inputs and design each IPROPI resistor
and filter. Interpret current readings with the selected driver mode and PWM
sampling phase. ADC headline throughput alone does not establish loop bandwidth.
Wheel current feedback still requires an explicit acquisition path.

## Pin-allocation acceptance criteria

- Count every chip select, PWM, interrupt, fault, enable, and recovery signal.
- Check module-exposed pins, reserved flash pins, strapping states, and USB pins.
- Confirm timer/PWM synchronization, dead-time responsibilities, and ADC latency.
- Specify safe boot/reset levels and fault shutdown independent of normal tasks.
- Record the final GPIO table and schematic net names together.
