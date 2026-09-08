# V1 architecture

V1 is a wired USB mouse with three independently sensed, actively haptic buttons
and a motorized scroll wheel. Wireless operation and additional functional ICs
are outside the current feature scope; supporting power/protection circuitry
still needs to be selected.

| Requirement | Target / interpretation |
| --- | --- |
| Cursor | PAW3950 optical X/Y tracking |
| Supplementary motion | ICM-42688-P lift/orientation experiments; not the cursor source |
| Buttons | Left, middle, right; magnetic position sensing without switch contacts |
| Button feedback | Bidirectional voice-coil force with position and current feedback |
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
    Logic --> Optical[PAW3950 and local 1.8 V regulator]
    Optical -->|X/Y| MCU
    IMU[ICM-42688-P] --> MCU
    Hall[Three TMAG5253 sensors] --> ADC[ADS7038]
    ADC --> MCU
    MCU --> VCA[Three DRV8874 drivers and voice coils]
    VCA -->|Current feedback| ADC
    MCU --> Wheel[DRV8316R and GB1806]
    Angle[MA735 wheel angle] --> MCU
    Power --> VCA
    Power --> Wheel
    CC[Type-C current detection, part TBD] --> MCU
```

The mouse is a USB device. An external powered hub is a separate accessory, not
an assumption that every powered downstream port provides 3 A. A custom adapter
is optional future work; its controller, power switch, and Type-C source behavior
need their own design. USB2512B in the notes is only a candidate.

SPI sharing is provisional. Validate transaction latency, device modes and
tri-state behavior before deciding whether the ADC or encoder needs a separate
bus. Pin numbers, loop rates, current limits, USB identifiers, CAD tools, firmware
framework, and the host configuration protocol have not been frozen.

Actuators must remain disabled until power capability, calibration, fault handling,
and limits are valid. Optical tracking and ordinary HID operation should remain
usable with haptics disabled.
