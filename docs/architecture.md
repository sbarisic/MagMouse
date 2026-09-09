# V1 architecture

V1 is a wired USB mouse with three independently sensed, actively haptic buttons
and a motorized scroll wheel. Wireless operation and additional functional ICs
are outside the current feature scope; supporting power/protection circuitry
is drawn; remaining peripheral circuitry and physical validation are open.

| Requirement | Target / interpretation |
| --- | --- |
| Cursor | PMW3360DM-T2QU + LM19-LSI optical X/Y tracking |
| Supplementary motion | ICM-42688-P lift/orientation experiments; not the cursor source |
| Buttons | Left, middle, right; magnetic position sensing without switch contacts |
| Button return | Elastic paddle/flexure supplies passive return with coil current off |
| Button feedback | Custom moving magnet and stationary wound coil; transient bidirectional effects with position/current feedback |
| Scroll | MA735 absolute angle, programmable BLDC detents/torque |
| Host connection | USB 2.0 Full-Speed HID, target 1 ms report interval |
| Power | 5 V USB-C, source-aware limits; intended 3 A advertised source for full effects |
| Indicator | One RGB status/profile LED |
| Recovery | Reset, boot, programming/test access |

```mermaid
flowchart TD
    PC[PC] --> Hub[Externally powered Type-C hub or adapter]
    Hub -->|USB data| MCU[ESP32-S3]
    Hub -->|5 V VBUS| Power[Protected power distribution]
    Power --> Logic[3.3 V logic supply]
    Logic --> MCU
    Logic --> Optical[PMW3360 and switched 3.3 V / local 1.9 V supplies]
    Optical -->|X/Y| MCU
    IMU[ICM-42688-P] --> MCU
    Hall[Three TMAG5253 sensors] --> ADC[ADS7038 #1]
    ADC --> MCU
    MCU --> Buttons[Three DRV8231A drivers and custom wound coils]
    Buttons -->|Current feedback| ADC
    Buttons -->|Magnetic force| Paddles[Elastic paddles with actuator magnets]
    Paddles -->|Separate sensing magnets| Hall
    MCU --> Wheel[DRV8316R and GB1806]
    Angle[MA735 wheel angle] --> MCU
    Wheel -->|Phase current| ADC2[ADS7038 #2, dedicated SPI3]
    ADC2 --> MCU
    Power --> Buttons
    Power --> Wheel
    CC[TUSB320 Type-C current detection] --> MCU
```

The button direction was revised on 2026-09-08: custom moving-magnet actuators
replace the industrial linear actuators, and elastic paddles provide return
instead of an active holding force or a dedicated magnetic return arrangement.
Each paddle carries separate sensing and actuator magnets. The stationary wound
coil adds bounded press/release effects; it is not required to support the paddle
continuously. Zero commanded coil current is the normal resting/held state after
an effect ends; driver and sensing electronics still consume power.

Retain bidirectional DRV8231A drive for resistance and brief assistance during
snap-through. A single-transistor driver, vibration exciter, and LRA are not the
selected V1 implementation. The smaller dimensions and 0.2-0.4 N actuator-force
target in the [button plan](../mechanical/button-mechanisms/README.md) are
unvalidated prototype targets. Measure force versus position and current before
freezing the coil, magnetic circuit, current limits, or PCB placement.

The mouse is a USB device. An external powered hub is a separate accessory, not
an assumption that every powered downstream port provides 3 A. A custom adapter
is optional future work; its controller, power switch, and Type-C source behavior
need their own design. USB2512B in the notes is only a candidate.

The [GPIO/resource allocation](interfaces.md) uses SPI2 for buttons/system ADC,
optical, IMU, angle and driver configuration; SPI3 is dedicated to the second
wheel ADC. Wheel control uses 3-PWM and RGB uses one RMT data pin. Validate
transaction latency, signal levels and sampling windows before routing. Loop
rates, current limits, USB identifiers, firmware framework and host protocol
still require implementation decisions and measurement.

Actuators must remain disabled until power capability, calibration, fault handling,
and limits are valid. Optical tracking and ordinary HID operation should remain
usable with haptics disabled.
