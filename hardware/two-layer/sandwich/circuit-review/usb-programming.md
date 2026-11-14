# USB programming review — 2026-11-06

The present circuit supports native ESP32-S3 USB programming. No crossed data
pins, missing boot controls, or schematic-to-PCB net mismatches were found.
USB routing needs improvement before layout sign-off: its reference ground is
interrupted, and its fanouts have unequal via counts. This is a signal-integrity
risk, not evidence that enumeration or flashing necessarily fails.

## Connections checked

Fresh Lower/Upper netlists were compared with the current PCB pad nets.

| Function | Actual connection | Result |
|---|---|---|
| D+ | J1 A6/B6 → USB_DP → R6 33 Ω → U3 pad 24 / GPIO20 | Correct |
| D− | J1 A7/B7 → USB_DM → R5 33 Ω → U3 pad 23 / GPIO19 | Correct |
| Data ESD | U1 TPD2EUSB30DRTR: 1 D+, 2 D−, 3 GND | Correct DRT pin assignment |
| CC | J1 A5/B5 → U11 CC1/CC2; U20 TPD2E2U06DCKR pins 1/2 protect CC, pin 3 GND | Correct |
| Type-C sink | U11 TUSB320LAIRWBR PORT and EN_N grounded; ADDR open; VDD +3V3; VBUS_DET through 887 kΩ | Correct; internal dead-battery Rd permits attachment before +3V3 starts |
| BOOT | SW2 grounds GPIO0; R4 10 kΩ pulls it high otherwise | Correct manual download selection |
| Boot strap | GPIO46 / U3 pad 44 pulled low by R80 10 kΩ | Compatible with ROM download |
| RESET | SW1 grounds EN; R3 10 kΩ pull-up and C4 1 µF; logic PG and power faults also feed EN | Manual reset available; actual startup timing remains a bench test |

No additional USB-UART bridge or parallel CC pull-down resistors are required.
The native Serial/JTAG controller provides flashing and a Windows COM port.

## Power and programming procedure

USB power goes from Lower J1 through J103.2/J104.2 to Upper U12, returns as
PWR_5V through J104.3/J103.3, then feeds Lower U2 and the ESP32's +3V3 supply.
Consequently the Lower board alone does not normally power from J1. Connect the
main boards with their intended power and signal harnesses. Wheel and Encoder
are not needed for the flashing interface. Do not bypass the protection circuit.

1. Connect a USB data cable to J1 with the main-board harnesses installed.
2. Hold SW2 BOOT, press and release SW1 RESET, then release BOOT.
3. Select the resulting ESP USB COM port in the flashing tool.
4. Flash a built ESP32-S3 image with its supplied flash offsets, or use
   `idf.py -p COMx flash` from a configured ESP-IDF firmware project.
5. Release BOOT and reset to run the application if the flashing tool has not
   already restarted it.

Automatic download entry is available while native USB Serial/JTAG is active.
The future HID mouse application uses USB-OTG on the same internal PHY, so the
native programming port is not an independent always-available port. Retain the
manual BOOT/RESET recovery procedure. Firmware can later provide an intentional
reboot-to-download workflow. The repository currently contains a firmware plan,
not a buildable application; no firmware was flashed during this review.

## Layout findings

The long B.Cu paired sections are 58.673 mm (D+) and 58.991 mm (D−), with
1.10 mm width and approximately 0.15 mm edge gap on their parallel straight run.
These lengths exclude connector, ESD and resistor fanouts and are not complete
end-to-end propagation lengths. Connector-side nets use two vias for D+ and
three for D−, with narrow 0.127/0.15 mm fanouts. Resistor-to-module traces are
approximately 3.86/4.73 mm and have no vias.

Intersecting those wide bottom-layer trunk centerlines with the actual filled
front-layer GND polygons, GND pads, tracks and via lands finds **35.454 mm of D+
and 42.343 mm of D− without GND directly opposite**. This is a geometric screen,
not a field solver, return-current simulation, or proof of USB failure. Same-layer
ground exists but does not establish a continuous opposite-layer reference.

Recommended correction: reserve a continuous reference corridor for the USB
pair; route fanouts together with matched layer transitions and nearby ground
return vias; put U1 closer to the connector (its signal pads are currently about
12.4 mm behind J1's data lands). Keep the 33 Ω resistors near the module. Confirm
the 90 Ω differential geometry against the actual two-layer stackup and nearby
copper. Full-Speed operation is more forgiving than High-Speed USB, but the
current geometry has not been electrically qualified.

## Validation and remaining tests

- Fresh Lower and Upper KiCad DRC: zero violations, zero unconnected items,
  zero schematic parity issues. Fresh netlist-to-pad comparison: zero mismatches.
- PCB files were read only. Evidence and the measurement script are saved in
  `build/sandwich/usb-programming`; compact geometry results accompany this report.
- Unverified on hardware: Type-C attachment in both orientations, stable +3V3
  and EN during startup/flashing, current before enumeration, enumeration across
  cables/hosts, repeated flash/readback, HID-to-ROM recovery, and ESD performance.
- Earlier power simulations did not simulate the USB PHY/protocol or execute the
  ESP32 ROM. They cannot establish that programming works.

## Primary references

- [Espressif native USB Serial/JTAG](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/usb-serial-jtag-console.html)
- [Espressif boot mode selection](https://docs.espressif.com/projects/esptool/en/latest/esp32s3/advanced-topics/boot-mode-selection.html)
- [Espressif shared USB PHY and HID device stack](https://docs.espressif.com/projects/esp-usb/en/latest/esp32s3/usb_device.html)
- [Espressif USB routing requirements](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html#usb)
- [TI TUSB320LAI](https://www.ti.com/lit/ds/symlink/tusb320lai.pdf)
- [TI TPD2EUSB30, DRT pin table](https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf)
- [TI TPD2E2U06, DCK pin table](https://www.ti.com/lit/ds/symlink/tpd2e2u06.pdf)
