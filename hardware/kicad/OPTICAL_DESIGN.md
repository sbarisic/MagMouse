# PMW3360 optical implementation

Revision 0.7, checked 2026-09-09. The V1 circuit now uses **PMW3360DM-T2QU
and LM19-LSI**. Sheets 16 and 17 add 22 BOM components and four test pads.
U35 now has a provisional on-board location; its support parts remain staged. Samples,
SROM usage rights, physical fit and measured operation remain open.

## Circuit and power

The design follows the pinout and reference in the
[PixArt datasheet, R1.50, 26 September 2016](https://datasheet.lcsc.com/datasheet/pdf/c018c3e1d470821feefadd37e2f785d5.pdf?productCode=C20612443),
with local regulation, power gating and shared-bus isolation added for MagMouse.

| Part | Function | Catalog identity |
| --- | --- | --- |
| U35 PMW3360DM-T2QU | Optical sensor with integrated illumination | C20612443; out-of-stock identity, **not an available JLC supply** |
| U38 TPS22918DBVR | HALL_EN-controlled, adjustable-rise OPT_3V3 supply | [C131941](https://www.lcsc.com/product-detail/C131941.html) |
| U36 TLV75519PDBVR | OPT_1V9 core regulator, supplied by OPT_3V3 | [C2865381](https://www.lcsc.com/product-detail/C2865381.html) |
| U37 SN74LVC125APWR | Selected-device SPI buffers and strong reset drive | C7813; also used by the wheel |
| U39 SN74LVC1G125DBVR | Isolates chip select from the powered host | [C23654](https://www.lcsc.com/product-detail/C23654.html) |

U35 pin 4 receives 1.9V; pin 5 receives local 3.3V. Pin 3 is an internal
regulator output and connects only to its 4.7uF/100nF bypass pair and TP42.
Pin 15 receives 1.9V through R132, 39 ohms, using the reference LED feed.
The power flag after R132 declares that passive feed to ERC; the optical
checker verifies its actual connection. Pins 1, 2, 6, 14 and 16 remain NC.

[TLV755P, Rev. D](https://www.ti.com/lit/ds/symlink/tlv755p.pdf) requires at
least 1uF at both input and output. C81/C82 are 2.2uF/10V; verify their effective
capacitance with tolerance, bias and temperature before release. Its 1.9V
nominal output has margin within the sensor's 1.8..2.1V core range. This does
not qualify transient droop or ripple. C83 goes at VDD; C86 at VDDIO; C84/C85
at VDDPIX. C80/C87 bypass the respective buffers.

The sensor specifies supply rise of 0.15..20ms and up to 100ms between valid
rails. The existing TPS62162's nominal ramp is too fast to assume compliance.
[TPS22918, Rev. C](https://www.ti.com/lit/ds/symlink/tps22918.pdf) with C79=1nF
has a tabulated typical 10–90% rise of 1.68ms at 3.3V; its approximate equation
gives 1.914ms. These are **typical estimates**, use a different measurement
interval from the sensor requirement, and do not guarantee either optical rail's
ramp. Capture both at TP40/TP41, including the LDO's startup. QOD is intentionally
open to avoid forcing a fast VDDIO discharge while core storage remains charged.
Verify falling rails and hot replug too; this is not a reverse-blocking switch.

HALL_EN = SENS_REQ AND MCU_EN now enables optics, encoder and RGB as well as
the Hall sensors. Hold SENS_REQ low through USB enumeration, and raise it only
after configuration with sufficient total current budget. Do not enable the
actuators until fresh sensor data is available. The sensor's stated startup
transients reach 70mA on VDD and 60mA on VDDIO, excluding capacitor charging.
Use a provisional **150mA optical startup allocation on the 3.3V domain** until measured, and
include the other simultaneously enabled loads. This allowance is not a USB
connector limit or a proven worst case. The sensor's run-current table contains
typical values up to 37mA, including illumination; it supplies no run-current
maximum. The advertised lower headline current is not a complete power budget.

## SPI, reset and scheduling

The existing GPIO map is unchanged: CS_PAW/2, MOSI/11, SCLK/12, MISO/13,
OPT_CTRL/26 and PAW_MOTION_N/39. The historical PAW net names are retained.

U37 runs from OPT_3V3. Three channels pass MOSI, SCLK and return MISO only
while CS_PAW is low. This isolates the sensor's 50pF clock/data input load and
prevents other devices' 20MHz transactions from reaching the 2MHz sensor port.
It also isolates MISO, whose state is undefined during sensor reset. The fourth
channel drives NRESET continuously: R79's boot-low input becomes a strong low
at the sensor despite its internal pull-up, specified at up to 600uA when reset
is held low. A direct 10k pulldown cannot establish that reset level.

U39 isolates NCS. Its input connects to CS_PAW; its output and pull-up use the
local rail. Both buffer types have overvoltage-tolerant inputs and Ioff support:
[SN74LVC125A](https://www.ti.com/lit/ds/symlink/sn74lvc125a.pdf),
[SN74LVC1G125](https://www.ti.com/lit/ds/symlink/sn74lvc1g125.pdf).
No host-powered pull-up is allowed on the sensor-side nets. Disable the ESP32's
internal pull-up on PAW_MOTION_N while the optical domain is off. Do not select
the device during rail transitions or reset; buffer outputs are not a general
power-good indication. Qualify leakage and shared-MISO behavior during ramp,
brownout and powered-off operation.

Use mode 3 at no more than 2MHz. Set SCLK high before selection and allow 1us
CS setup, read hold and inter-device release guards. For writes, hold CS low
for at least 35us after the last clock; honor the 180us write-to-next-access
interval. Ordinary reads require 160us address-to-data delay and 20us to the
next access. Motion bursts require 35us address delay. The 1us guard covers
the sensor's 500ns MISO release plus buffer delay; verify waveforms at the
sensor as well as the ESP32.

A full motion burst occupies at least 87us at 2MHz: one address byte, 35us
wait, and 12 data bytes, before guards and software overhead. It cannot be
preempted with another SPI2 transaction while CS is low. This **exceeds the
existing 50us encoder scheduling-delay target** if launched just before an
angle slot. Reserve optical bursts immediately after an encoder read and
admit them only when measured worst-case execution fits before the next 200us
angle slot. The old generic FIFO scheduler is not sufficient evidence.
Keep configuration and SROM uploads outside active haptic control. SPI3 wheel
ADC timing remains independent, but ISR/CPU contention still needs measurement.

## Firmware acceptance sequence

No firmware toolchain or driver has been implemented by this schematic change.

1. Boot with all CS high, OPT_CTRL low and SENS_REQ low. Mask motion IRQ and
   keep actuator commands/heartbeat off. Disable host pull-ups into optical IO.
2. After USB configuration/current-budget approval, raise SENS_REQ. For initial
   bring-up, wait 100ms for the gated rails, then release reset with CS high.
   That delay does not replace measurement of the specified rail-rise limits.
3. Wait at least 50ms after releasing hardware reset before register access.
   Then follow the manufacturer's SPI reset sequence, write 0x5A to
   Power_Up_Reset (0x3A), wait another 50ms, and read 0x02..0x06 regardless
   of motion. This conservative bring-up sequence deliberately includes both
   resets. Check Product_ID=0x42 and Inverse_Product_ID=0xBD.
4. Disable rest mode; load the supplier-authorized SROM with the documented
   0x1D / 10ms / 0x18 enable sequence and burst transfer. Verify supplied
   length, version and checksum expectations rather than accepting any blob.
   Read SROM_ID before unrelated register accesses, then configure wired mode,
   CPI, lift-off behavior and interrupt handling.
5. Activate Motion_Burst and validate signed X/Y, tracking quality, lift-off,
   orientation, lost-motion recovery and shared-bus scheduling with haptics.
   Re-activate the burst after accesses that invalidate it.
6. On suspend/deconfiguration, stop haptics, mask motion, send Shutdown if the
   bus is responsive, deselect, assert reset and clear SENS_REQ. Do not delay
   the USB suspend deadline waiting on a failed sensor transaction. Resume
   requires full initialization and SROM reload before reporting valid motion.

The current [QMK driver](https://github.com/qmk/qmk_firmware/blob/master/drivers/sensors/pmw33xx_common.c)
has weak SROM callbacks returning no payload by default. Its driver license does
not establish rights to an external binary. No SROM bytes or third-party driver
source have been copied into this repository. Obtaining the authorized payload
and terms is still a sample-procurement gate.

## Mechanical and assembly boundary

See [optical stack parameters and drawing](../../mechanical/optical/README.md).
The custom footprint follows Figure 3: staggered 1.78mm pitch, 10.70mm row
spacing and 0.70mm finished holes. Land diameter 1.30mm is our review choice,
not a manufacturer-provided copper land diameter. The footprint origin is the
optical center; front points left in its zero-degree top view. Rotate it to
the actual mouse front during placement and validate reported axis signs.

The recommended opening is drawn only on Dwgs.User, with a matching copper/pad
keepout. It is **not an Edge.Cuts opening**, and the board still needs the reviewed cutout,
lens/base features and mounting positions after sample fit. The sensor is a
through-hole optical assembly. Arrange protected no-wash soldering and controlled
seating height with the assembler, or fit the supplied sensor after SMT assembly.
Do not assume ordinary reflow or that the lens is included in JLC's BOM service.

## Review evidence

Run `export_review.py`, `verify_optical.py`, `test_optical_checks.py` and the
existing power/resource/wheel/peripheral checks. The optical checker verifies
81 pin connections, ten part identities and 16 land coordinates. Eight injected
fault cases cover back-powering, reset, MISO contention, core-output misuse,
ramp-cap omission, enable gating and incorrect pitch; the baseline also passes.
ERC and PCB parity are necessary checks, not analog or fabrication acceptance.

Final revision-0.7 exports: 18 sheets, 272 BOM components and 316 PCB footprints;
ERC 0 errors/0 warnings, physical DRC 0, schematic parity 0. All power, resource,
wheel and peripheral checks pass; optical baseline and eight fault injections
pass. All prior 290 footprint positions, orientations, pad nets, schematic paths
and the board outline were preserved. The PCB has no tracks/vias and native
connectivity reports 792 unrouted connections (DRC JSON lists 499 entries).
The schematic pages and mechanical datum diagram were rendered and inspected.
Subsequent PCB-first placement moves only U35 to X=125.5, Y=157.5mm, F.Cu at
270 degrees; the other 315 footprints stay put. The optical keepout now follows
the aperture guide and a separate drawing reserves the underside lens envelope.
The outer shell will be designed around the resulting mechanical interfaces.
