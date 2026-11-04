# Wheel harness — 19 wires

J8 on Lower connects to J9 on Wheel using matching pin numbers. This replaces
the old 30-pad reversed-number map. J10 on Upper connects to Wheel J11.
There are 14 signals, two supply wires, and three shared grounds.

The signal arrays have 17 holes on a 2 × 9 grid with one position omitted.
Copper envelope: 22.12 × 4.34 mm (previously 37.36 × 4.34 mm).
Signal pads remain 1.8 mm diameter with 0.8 mm drills.

| Main pad | Wheel pad | Net |
| --- | --- | --- |
| J8.1 | J9.1 | GND |
| J8.2 | J9.2 | SPI_SCLK |
| J8.3 | J9.3 | SPI_MOSI |
| J8.4 | J9.4 | CS_DRV8316 |
| J8.5 | J9.5 | DRV_MISO_LOCAL |
| J8.6 | J9.6 | MOTOR_SPI_SCLK |
| J8.7 | J9.7 | MOTOR_SPI_MOSI |
| J8.8 | J9.8 | CS_ADC2 |
| J8.9 | J9.9 | ADC2_MISO_LOCAL |
| J8.10 | J9.10 | WHEEL_PWM_A |
| J8.11 | J9.11 | WHEEL_PWM_B |
| J8.12 | J9.12 | WHEEL_PWM_C |
| J8.13 | J9.13 | ACT_DRIVE_EN |
| J8.14 | J9.14 | WHEEL_RUN_REQ |
| J8.15 | J9.15 | DRV_FAULT_LOCAL_N |
| J8.16 | J9.16 | +3V3 |
| J8.17 | J9.17 | GND |
| J10.1 | J11.1 | ACT_5V |
| J10.2 | J11.2 | GND |

Both headers are shown from the component side in the PCB files.
Follow pad numbers; their rotations differ. No pin reversal is needed.
Wire gauge and lengths remain dependent on the assembled stack.
