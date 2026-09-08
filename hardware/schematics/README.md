# Schematics

Reserved for editable schematic sources and review exports. CAD tool and version
are not selected yet. Planned circuit sheets:

1. USB-C, CC capability detection, ESD, input protection and power rails.
2. ESP32-S3 module, boot/reset, programming pads and RGB indicator.
3. PAW3950 optical circuit and ICM-42688-P interface.
4. ADS7038, three Hall inputs, and three DRV8874 current-feedback inputs.
5. Three voice-coil drivers, hardware current limits and actuator connectors.
6. DRV8316R, wheel motor, MA735 and wheel current measurement.

Before layout, review power sequencing, fault/reset states, pin allocation,
analog scaling, connector orientation and ERC results. Keep schematic net names
consistent with [the logical interfaces](../../docs/interfaces.md).
