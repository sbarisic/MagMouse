# GPIO and peripheral allocation — revision 0.5 (pin map unchanged)

The ESP32-S3-MINI-1-N8 fits V1 with **38 assigned GPIOs and one boot-low spare,
GPIO46**. The user selected a single-data-pin addressable RGB LED on 2026-09-08.
Wheel control uses 3-PWM; ADC2 gets a dedicated SPI host. USB, recovery UART,
button commands and existing power-control pins stay put.

The allocation is checked, but runtime timing is **not yet proven**.
The [machine-readable allocation](../hardware/kicad/gpio-allocation.json) and
[MCU schematic](../hardware/kicad/02_MCU.kicad_sch) use the same net names.
[Sheet 09](../hardware/kicad/09_Interface_Reservations.kicad_sch) exposes new
signals on test pads and adds boot/control bias resistors. These are real MCU
connections. Revision 0.5 adds ADC2, wheel driver, encoder, SPI isolation and
autonomous brake sheets. The optical circuit, IMU and RGB still need their
component sheets; see [wheel review](../hardware/kicad/WHEEL_REVIEW.md).

## Complete module pin map

The second column contains module land numbers, not bare-chip pins.
ADC_CS is CS_ADC1; SPI_SCLK/MOSI/MISO are bus A. MOTOR_SPI_* are bus B.
OPT_CTRL reserves one output for optical reset/power sequencing; its circuit
must follow the exact PAW3950 reference when obtained.

| GPIO | Module pad | Net | Peripheral / role |
| --- | --- | --- | --- |
| 0 | 4 | BOOT | boot |
| 1 | 5 | VBUS_PRESENT_N | power |
| 2 | 6 | CS_PAW | SPI2 |
| 3 | 7 | WHEEL_RUN_REQ | wheel |
| 4 | 8 | BTN_L_CMD1 | MCPWM1 |
| 5 | 9 | BTN_L_CMD2 | MCPWM1 |
| 6 | 10 | BTN_M_CMD1 | MCPWM1 |
| 7 | 11 | BTN_M_CMD2 | MCPWM1 |
| 8 | 12 | BTN_R_CMD1 | MCPWM1 |
| 9 | 13 | BTN_R_CMD2 | MCPWM1 |
| 10 | 14 | ADC_CS | SPI2 |
| 11 | 15 | SPI_MOSI | SPI2 |
| 12 | 16 | SPI_SCLK | SPI2 |
| 13 | 17 | SPI_MISO | SPI2 |
| 14 | 18 | CC_OUT1 | power |
| 15 | 19 | CC_OUT2 | power |
| 16 | 20 | ACT_REQ | power |
| 17 | 21 | ACT_HEARTBEAT | software |
| 18 | 22 | SENS_REQ | power |
| 19 | 23 | MCU_USB_DM | USB_OTG |
| 20 | 24 | MCU_USB_DP | USB_OTG |
| 21 | 25 | CS_IMU | SPI2 |
| 26 | 26 | OPT_CTRL | optical |
| 33 | 28 | MOTOR_SPI_MOSI | SPI3 |
| 34 | 29 | MOTOR_SPI_SCLK | SPI3 |
| 35 | 31 | MOTOR_SPI_MISO | SPI3 |
| 36 | 32 | CS_ADC2 | SPI3 |
| 37 | 33 | CS_MA735 | SPI2 |
| 38 | 34 | CS_DRV8316 | SPI2 |
| 39 | 35 | PAW_MOTION_N | interrupt |
| 40 | 36 | IMU_INT1 | interrupt |
| 41 | 37 | DRV_FAULT_N | MCPWM0_fault |
| 42 | 38 | WHEEL_PWM_A | MCPWM0 |
| 43 | 39 | UART_TX | UART0 |
| 44 | 40 | UART_RX | UART0 |
| 45 | 41 | RGB_DATA | RMT |
| 46 | 44 | BOOT_SAFE_SPARE | Boot-low spare; no peripheral |
| 47 | 27 | WHEEL_PWM_B | MCPWM0 |
| 48 | 30 | WHEEL_PWM_C | MCPWM0 |

EN is module pad 45, net MCU_EN, and is not a GPIO. Supply/ground pads are
unchanged. GPIO22-25 do not exist; GPIO27-32 are not exposed by this module.
GPIO26 is usable on N8 but occupied by PSRAM on N4R2. GPIO33-37 are available
on this N8 module; memory-variant restrictions matter when substituting modules.

GPIO0 retains the boot button/pull-up. GPIO3 WHEEL_RUN_REQ has R77 to ground.
GPIO45 RGB_DATA has R78 to ground; the eventual LED/level shifter must not pull
it high during reset. GPIO46 has R80 to ground and no consumer, preserving
download boot. Hold the required levels through the manufacturer's 3 ms
strapping interval. No eFuse changes are required. GPIO39-42 have other uses,
so external four-wire JTAG is unavailable. USB Serial/JTAG and USB OTG share
physical pins/PHY; they are not simultaneous independent USB links. UART
recovery remains accessible.

## SPI assignment

| Host | Pins | Devices / CS GPIOs | Resource use |
| --- | --- | --- | --- |
| SPI2_HOST / bus A | SCLK12, MOSI11, MISO13 | ADC1/10, PAW/2, IMU/21, MA735/37, DRV8316/38 | Five of six hardware CS slots |
| SPI3_HOST / bus B | SCLK34, MOSI33, MISO35 | ADC2/36 only | One of three hardware CS slots |

SPI0/1 remain dedicated to memory. There is no third general-purpose SPI host
for ADC1. SPI2 uses native bus pins; SPI3 uses the GPIO matrix. Register ADC1
first when using SPI2 CS0 on GPIO10. The slot counts come from S3 capabilities,
not a generic ESP32 three-device limit.

Use per-device mode, clock and CS timing. Initial clock targets: 20 MHz for
both ADCs, 10 MHz for MA735/IMU, and 1 MHz for DRV8316. The driver
clock is reduced for its open-drain SDO pull-up and new return buffer; measure
edge rate and setup margin before increasing it. PAW mode, clock,
read delays, voltage domain and MISO release await its exact reference.
Do not treat PAW3395 circuitry as PAW3950 validation. The MCU-side CS pull-ups
do not authorize direct connection to a lower-voltage peripheral: review
translation, power-off isolation and SDO idle behavior in each future circuit.
DRV8316 requires 16-bit, mode-1 SPI timing and at least 400 ns between CS frames.
Keep both ADS7038 devices in mode 0, including initial configuration. Use mode 3
for MA735, with at least 80 ns CS setup and 25 ns hold; allow 150 ns between
angle frames and 750 ns around register accesses. Do not perform encoder NVM
writes during motor control. Its SPI read width does not equal effective angle
resolution. Exact IMU and optical SPI settings belong in their circuit review.

Bus A needs a bounded scheduler/owner. Reserve recurring angle-read slots,
then service ADC1, optical and IMU work. Bound FIFO bursts; release the bus
during device-internal waits when its protocol allows. Initial targets are
5 kHz angle reads with at most 50 us scheduling delay, 1 kHz button/system
scans and 1 kHz HID reports. PAW timing may force a schedule change.

Eight ADC1 16-bit reads at 20 MHz use 6.4 us of clock time per 1 ms scan.
MA735 16-bit reads at 10 MHz use another 8 us/ms at 5 kHz. These calculations
exclude conversions, CS gaps, optical traffic and software overhead; available
wire bandwidth is not proof of worst-case latency.

Bus B has one owner and no optical, encoder, configuration or logging traffic.
Use an independent DMA channel only if the measured acquisition path needs DMA;
short transfers can perform better without it.

## PWM, interrupt and recovery resources

| Resource | Allocation |
| --- | --- |
| MCPWM group 0 | Wheel: timer 0, operators 0/1/2, generator A from each; three center-aligned PWM outputs |
| MCPWM group 1 | Buttons: timer 0, operators 0/1/2, generators A/B per button; six independent outputs |
| RMT | One TX channel for addressable RGB; exact LED/interface pending |
| GPIO interrupts | PAW_MOTION_N, IMU_INT1, DRV_FAULT_N; CC/VBUS changes as needed |
| MCPWM fault | DRV_FAULT_N to group 0; firmware setup does not replace external disable gates |
| UART0 | GPIO43 TX / GPIO44 RX |
| USB OTG | GPIO19/20, Full-Speed HID |
| Heartbeat | GPIO17, software refresh only after a valid control iteration |

Each of the S3's two MCPWM groups has three timers, three operators and two
comparators/generators per operator. Both groups use all three operators,
but only timer 0 initially. Start with a 20 kHz carrier as a bring-up target.
Button A/B outputs are independent, not complementary; follow DRV8231A
drive/decay requirements. Update wheel comparators together at a timer boundary.
Do not allocate these operators again through another library. LEDC is unused.

MA735 uses SPI absolute angle; A/B/Z, PWM and magnetic-status output pins have
no V1 MCU allocation. Use appropriate SPI diagnostics. IMU uses INT1 and its
internal clock; INT2/FSYNC/CLKIN are unassigned. GPIO46 reuse needs a boot-level
review. The brake chopper must protect the rail independently of an MCU output.

Power-domain controls are included in the allocation: reuse HALL_EN (derived
from SENS_REQ and MCU_EN) for future MA735 and RGB supply enables. This keeps
them off during reset/suspend without extra GPIOs. RGB power comes from the
appropriate protected logic supply, not the haptics-only ACT rail. OPT_CTRL
reserves optical sequencing; IMU uses its software sleep controls. Implement
power-off SPI/data isolation and startup settling in those component sheets.
Independent always-on RGB/encoder operation would require a new resource review.

## Two ADCs

| Channel | ADS7038 #1 — U10, buttons/system | ADS7038 #2 — U23, wheel |
| --- | --- | --- |
| CH0 | Left Hall | Phase A current, conditioned SOA |
| CH1 | Middle Hall | Phase B current, conditioned SOB |
| CH2 | Right Hall | Phase C current, conditioned SOC |
| CH3 | Left coil current | Grounded spare via R105; bus-current sensor unselected |
| CH4 | Middle coil current | Grounded spare via R106 |
| CH5 | Right coil current | Grounded spare via R107 |
| CH6 | Input current | Grounded spare via R108 |
| CH7 | ACT_5V | Grounded spare via R109 |

ADC1 inputs stay unchanged. ADC2 needs no CONVST/DRDY GPIO: host-mode conversions
start on CS rising edges. It is multiplexed, not simultaneous-sampling.
Account for channel switching and its result pipeline. Do not copy ADC1's slow
power-telemetry filter onto motor-current inputs.

## Wheel acquisition timing gate

Evaluate host-triggered, on-the-fly selection of the three phase channels,
without averaging, using 16-bit frames and channel identification. Each frame
needs its own CS edge: one long transfer with CS held low cannot take three
samples. Discard the initial stale result; a fourth frame retrieves the third
fresh conversion. Track timestamps and reject stale/misidentified results.

At 20 MHz, 16 clocks plus one setup and one hold clock take 0.9 us. With
0.7 us CS-high time, a conservative schedule is 1.6 us/frame, or 6.4 us for
four frames before software overhead. First-to-third sampling spacing is
3.2 us in this ideal schedule. Conversion and acquisition timing must hold
with the actual front end and channel changes.

Initial targets: 20 kHz PWM, 5 kHz current-control updates, at most 8 us for
the acquisition burst, 1 us launch jitter, and a 3 us settling guard. The guard
now includes the driver propagation delay plus CSA settling at the 200 V/us
slew setting. Reserve at least 12 us of valid common low-side measurement time.
The combined 12 us budget has no spare time; it is not measured. A 12 us common low-side interval
within a 50 us PWM period can limit maximum phase duty to roughly 76%,
depending on modulation.

The ESP-IDF v5.5.1 guide reports typical one-byte polling transactions around
9 us without DMA, and interrupt transactions around 24 us. These are reference
measurements, not board-specific bounds. Four ordinary API calls do not
establish the 8 us target. Prototype a bounded polling/LL or segmented-transfer
path that preserves per-frame CS timing. PWM-to-SPI launch also needs measured
implementation; no autonomous hardware trigger is established by the schematic.

DRV8316 senses low-side FET current. Reject samples outside valid switching
states; establish amplifier/filter settling and small-current offset/gain.
If the common sampling window or jitter budget fails, revise modulation,
acquisition hardware or the controller architecture before full-board routing.
Reducing the control-loop update rate alone does not widen a PWM sampling window.

## Checks and next work

Run from the repository root:

    python hardware/kicad/export_review.py
    python hardware/kicad/verify_power.py
    python hardware/kicad/verify_resources.py
    python hardware/kicad/verify_wheel.py

Checks cover all module GPIOs, net/pad agreement, boot biases, independent CS
signals, peripheral capacity and timing arithmetic. They do not establish
firmware deadlines or analog performance.

Wheel circuits now implement the [wheel control contract](wheel-control.md).
Next draw the exact optical circuit, IMU and RGB. Timing, regenerative energy and physical acceptance remain open.

## Primary evidence

Checked 2026-09-08. Software versions below are review baselines, not a
selected firmware toolchain or a claim that they are the latest release.

- [Espressif module datasheet v1.7](https://documentation.espressif.com/esp32-s3-mini-1_mini-1u_datasheet_en.html): module pads, memory variants and boot configuration.
- [ESP-IDF v5.5.1 S3 capability header](https://github.com/espressif/esp-idf/blob/v5.5.1/components/soc/esp32s3/include/soc/soc_caps.h): GPIO, SPI CS, MCPWM and RMT resources.
- [ESP-IDF v5.5.1 SPI guide](https://docs.espressif.com/projects/esp-idf/en/v5.5.1/esp32s3/api-reference/peripherals/spi_master.html): routing, ownership and transaction overhead.
- [TI ADS7038, SBAS979C, September 2024](https://www.ti.com/lit/ds/symlink/ads7038.pdf): conversion timing, channel selection and data frames.
- [TI DRV8316, SLVSF16B, April 2022](https://www.ti.com/lit/ds/symlink/drv8316.pdf): PWM modes, disable behavior, SPI and low-side sensing.
- [MPS MA735, Rev. 1.0, April 26, 2022](https://www.monolithicpower.com/en/documentview/productdocument/index/version/2/document_type/Datasheet/lang/en/sku/MA735GGU/): SPI angle readout and optional outputs.
- [TDK ICM-42688-P, DS-000347](https://invensense.tdk.com/wp-content/uploads/2020/04/ds-000347_icm-42688-p-datasheet.pdf): SPI interface; full circuit/package review remains later work.
