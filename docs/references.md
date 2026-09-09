# Reference sources

Sources for the maintained design; inclusion does not mean a circuit or rating has
been independently validated. Record document revisions during design work.
Manufacturer datasheets take precedence over brainstorming estimates.

| Topic | Source |
| --- | --- |
| Optical reference | [badjeff/paw3395-pcb](https://github.com/badjeff/paw3395-pcb) (check PAW3950 variant and license) |
| Custom button actuator | [Button mechanism and experiment](../mechanical/button-mechanisms/README.md), based on the user's two design analyses supplied 2026-09-08; elastic-paddle revision takes precedence |
| Button driver | [TI DRV8231A](https://www.ti.com/product/DRV8231A), [datasheet SLVSFZ8A, Rev. A, January 2026](https://www.ti.com/lit/ds/symlink/drv8231a.pdf) |
| ADC | [TI ADS7038](https://www.ti.com/product/ADS7038) |
| Hall sensor | [TI TMAG5253](https://www.ti.com/product/TMAG5253) |
| Wheel driver | [TI DRV8316](https://www.ti.com/product/DRV8316) |
| Wheel motor | [Micronix TSL-GB1806](https://micronixmotor.com/shop/bldc-gimbal-motor-tsl-gb1806/) (confirm encoder-free variant) |
| ESP32-S3 hardware | [Espressif schematic checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html) |
| Type-C background | [USB-IF Type-C release 2.0](https://www.usb.org/sites/default/files/USB%20Type-C%20Spec%20R2.0%20-%20August%202019.pdf) (historical; verify current requirements before sign-off) |
| Hardware license | [CERN OHL](https://cern-ohl.web.cern.ch/home) |

DRV8231A Rev. A was checked on 2026-09-08 for supply minimum, control pins,
current feedback/regulation and sleep behavior. The DRV8316 manufacturer product
page was checked the same day for its 4.5 V supply minimum. These checks do not
validate the custom winding, magnetic circuit, or operation with USB cable drop.

The custom actuator dimensions, force targets, material suggestions and cost
allowances come from the supplied analysis and remain unmeasured/unquoted.
`ideas.md` preserves the original industrial-actuator brainstorming; use the
maintained architecture and BOM for the current selection.

Optical sourcing and the pinned public reference comparison are in
[OPTICAL_REVIEW.md](../hardware/kicad/OPTICAL_REVIEW.md). Manufacturer revisions
and catalog links for IMU/RGB are in
[PERIPHERAL_REVIEW.md](../hardware/kicad/PERIPHERAL_REVIEW.md).
