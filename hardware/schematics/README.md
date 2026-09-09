# Schematics

Editable sources now live in [the KiCad project](../kicad/README.md), using
KiCad 10.0.6. It contains an overview plus power/USB, MCU, button-driver and
Hall/ADC sheets. USB input power and several subsystems remain incomplete.
The intended full schematic will cover:

1. USB-C, CC capability detection, ESD, input protection and power rails.
2. ESP32-S3 module, boot/reset, programming pads and RGB indicator.
3. PMW3360 optical circuit and ICM-42688-P interface.
4. ADS7038, three Hall inputs, and three DRV8231A current-feedback inputs.
5. Three DRV8231A wound-coil drivers, VREF limits, IN1/IN2 reset/timeout controls
   and two-wire coil connectors.
6. DRV8316R, wheel motor, MA735 and wheel current measurement.

Before layout, review power sequencing, fault/reset states, pin allocation,
analog scaling, connector orientation and ERC results. Keep schematic net names
consistent with [the logical interfaces](../../docs/interfaces.md).
