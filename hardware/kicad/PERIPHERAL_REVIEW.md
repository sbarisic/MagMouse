# IMU and RGB circuit review

Revision 0.6, 2026-09-09. Sheets 14 and 15 add 16 BOM components and two copper
test pads. The PCB retains all 272 earlier placements and stages these 18
footprints off-board. This is schematic development, not routing or fabrication
approval. Optical work is tracked separately in [OPTICAL_REVIEW.md](OPTICAL_REVIEW.md).

## Parts and source evidence

| References | Selection | Catalog |
| --- | --- | --- |
| U32 | TDK InvenSense ICM-42688-P | [C1850418](https://jlcpcb.com/partdetail/TDKInvenSense-ICM_42688P/C1850418); JLC requires X-ray inspection |
| U33 | TI TPS7A2450DBVR, 5V LDO with enable | [C2864436](https://jlcpcb.com/partdetail/TexasInstruments-TPS7A2450DBVR/C2864436) |
| U34 | TI SN74LV1T34DBVR, logic buffer/translator | [C100024](https://jlcpcb.com/partdetail/SN74LV1T34DBVR/C100024) |
| D5 | OPSCO SK6805-EC15 | [C2890035](https://jlcpcb.com/partdetail/OPSCOOptoelectronics-SK6805EC15/C2890035); Standard PCBA only, MSL4 |
| C71 | Samsung CL10B225KP8NNNC, 2.2uF/10V X7R | [C100082](https://www.lcsc.com/product-detail/C100082.html) |
| C72 | Samsung CL10B103KB8NNNC, 10nF/50V X7R | [C1589](https://www.lcsc.com/product-detail/C1589.html) |

Other passives reuse existing selections. Catalog identities do not guarantee
inventory: the LCSC ICM-42688-P page showed out of stock during this review;
refresh JLC stock and obtain a real quote before purchase. D5's catalog name
omits the `-001` suffix used by its linked 2025 datasheet. Confirm the supplied
lot and timing revision before ordering; do not silently substitute another
SK6805 or WS2812 version.

Manufacturer evidence inspected:

- [TDK DS-000347, revision 1.6](https://product.tdk.com/system/files/dam/doc/product/sensor/mortion-inertial/imu/data_sheet/ds-000347-icm-42688-p-v1.6.pdf), supply/timing tables, sections 4, 10, 12.3 and register definitions.
- [TI TPS7A24, SBVS386E](https://www.ti.com/lit/ds/symlink/tps7a24.pdf), September 2022; fixed DBV pinout, enable, accuracy, dropout and capacitance.
- [TI SN74LV1T34, SCLS743E](https://www.ti.com/lit/ds/symlink/sn74lv1t34.pdf), February 2024; DBV pinout, input tolerance, thresholds and drive.
- [OPSCO SK6805-EC15-001 A1](https://datasheet.lcsc.com/datasheet/pdf/0f4b58ac8908ccf8037b2d7ca0ec1e91.pdf?productCode=C2890035), August 2025; pinout, lands, supply and signal limits, GRB format and timing. Geometry cross-checked against the [earlier EC15 drawing](https://cdn-shop.adafruit.com/product-files/4492/Datasheet.pdf); older timing is not interchangeable with A1.

## IMU connections and firmware

U32 uses system +3V3 on both power pins, without a switched SPI power domain.
C70/C71 belong at VDD pin 8; C72 belongs at VDDIO pin 5. Pin 7 is grounded;
2/3/10/11 are NC as permitted. The native KiCad LGA-14_3x2.5mm footprint matches
the manufacturer's top view, 0.5mm pitch and 1.1625/0.9125mm land centres.
It has no exposed pad. Its 0.625x0.35mm lands need normal stencil review.

SPI2 uses CS_IMU, the existing R73 pull-up, and the unchanged SCLK/MOSI/MISO.
Use mode 0 at an initial 10MHz, with at least 100ns CS setup, hold and release
guard. INT1 has a new 10k pull-up for active-low open-drain operation. Pin 9 has
a 10k pulldown: select its FSYNC input function, keep FSYNC disabled and retain
the internal clock. The resistor avoids a hard short if firmware misconfigures
this multiplexed pin as an output.

Wait at least 1ms after valid supply before register access. Check WHO_AM_I
0x47, configure 4-wire SPI and follow section 12.3 interface settings. Configure
INT1 polarity/drive, interrupt clearing and FIFO policy explicitly. Bound FIFO
bursts so MA735, ADC1 and optical transactions retain their timing budgets.
Put accelerometer/gyro into their required sleep modes for USB suspend. Measure
current, restart delay, motion data and sensitivity to button/wheel vibration.

## RGB power and boot behavior

U33 takes PWR_5V and is enabled by HALL_EN, which already falls during reset
and sensor sleep. Its output supplies both U34 and D5. The regulator prevents
normal elevated input voltage near the input eFuse's OVLO threshold from being
applied directly to the LED. It never uses the regenerating ACT_5V rail.
The nominal 5V output has a regulated accuracy range of 4.9375..5.0625V when
the datasheet's regulation conditions hold. This is not a transient clamp
guarantee. Qualify fast input steps and startup overshoot separately.

At ordinary USB voltage U33 may operate in dropout: it does not boost a low
input back to 5V. LED operation requires 3.7..5.5V. The buffer's published
4.5..5.5V logic specifications give a conservative initial operating budget;
combined LED/buffer operation below 4.5V needs qualification at the actual cable
drop. Do not report guaranteed RGB operation across all USB supply corners yet.
C74 is 10uF/25V nominal; verify at least 1uF effective capacitance for stability.

U34 raises the data level, with R128=330 ohms in series and R129=100k at DIN.
The checked LED requires VIH >=0.78 VDD, so a direct 3.3V GPIO is insufficient.
GPIO45 only sees U34's input, its original R78 10k pulldown and test pad. U34
allows input voltage independent of VCC; its input leakage is specified with
VCC=0. Its output and LED share a supply, avoiding an independently powered
data output into an unpowered LED. Measure leakage during rail transitions.

R130=10k discharges the local rail. With 10.2uF nominal total output bypass,
the passive time constant is about 102ms and the initial bleed is 0.5mA.
Account for capacitance tolerance and leakage when setting the off-time; a
short off/on toggle is not a proven LED reset. Send black first, drive data
low, then disable HALL_EN for suspend. Wake with data low, wait for valid rail,
send a reset interval and then a complete colour frame.

For the checked A1 LED revision, use one RMT channel at 800kbps, GRB/MSB-first:
0 bit 0.30us high/0.95us low; 1 bit 0.90us high/0.35us low; reset low >=300us.
Use a provisional 25mA active RGB allocation including bleed and buffer;
verify maximum full-white current, brightness, thermal behavior and suspend
current. No actuator enable may depend on successful RGB communication.

## Validation

Run export_review.py, verify_power.py, verify_resources.py, verify_wheel.py,
verify_peripherals.py, test_peripheral_checks.py and export_pcb_review.py.
Current results: ERC 0 errors/0 warnings; physical DRC 0; schematic parity 0.
The peripheral checker covers 51 connections, seven new part identities and
four LED lands. Five tests include rejection of wrong LED power, direct GPIO
drive, wrong IMU reserved-pin power and always-enabled RGB. The PCB remains
unrouted; native DRC reports 499 unconnected items.

Keep the IMU away from board flex/heat and fit the LED to its light pipe after
mechanical CAD. These electrical checks do not prove enclosure fit, noise,
firmware scheduling, USB current compliance or final assembly suitability.
