# Reference sources

Starting points from `ideas.md`; inclusion does not mean a circuit or rating has
been independently validated. Record document revisions during design work.
Manufacturer datasheets take precedence over brainstorming estimates.

| Topic | Source |
| --- | --- |
| Optical reference | [badjeff/paw3395-pcb](https://github.com/badjeff/paw3395-pcb) (check PAW3950 variant and license) |
| Voice coil | [Moticont](https://www.moticont.com/) (obtain LVCM-013-008-02 drawing/datasheet) |
| Button driver | [TI DRV8874](https://www.ti.com/product/DRV8874) |
| ADC | [TI ADS7038](https://www.ti.com/product/ADS7038) |
| Hall sensor | [TI TMAG5253](https://www.ti.com/product/TMAG5253) |
| Wheel driver | [TI DRV8316](https://www.ti.com/product/DRV8316) |
| Wheel motor | [Micronix TSL-GB1806](https://micronixmotor.com/shop/bldc-gimbal-motor-tsl-gb1806/) (confirm encoder-free variant) |
| ESP32-S3 hardware | [Espressif schematic checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html) |
| Type-C background | [USB-IF Type-C release 2.0](https://www.usb.org/sites/default/files/USB%20Type-C%20Spec%20R2.0%20-%20August%202019.pdf) (historical; verify current requirements before sign-off) |
| Hardware license | [CERN OHL](https://cern-ohl.web.cern.ch/home) |

DRV8874 and DRV8316 manufacturer product pages were checked on 2026-09-08 for
their 4.5 V minimum operating supply. Other parameters need part-specific validation.
