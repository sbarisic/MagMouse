PAW3950 - Motion sensor
TDK ICM-42688-P — 6-axis accelerometer + gyro
TI TMAG5253BA2 - Magnetic sensor for buttons
MPS MA735 - Hall-effect rotary encoder
TI ADS7038 - Analog Digital Converter
ESP32-S3 - Main processor
TI DRV8316 - 3 phase BLDC motor driver
LVCM-013-008-02 - Voice coil actuators, haptic button feedback
SteadyWin/TSL GB1806 (also sold as PM1806), without its encoder - Scroll motor




Assuming V1 is a wired USB mouse, I would freeze the architecture roughly like this. One correction: the **PAW3950 handles normal cursor movement**; the IMU is supplementary for lift/orientation/acceleration/experimentation.

|   Qty | Component                           | Purpose                                                                                                                |
| ----: | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
|     1 | **ESP32-S3-MINI-1-N8**              | Main MCU, USB HID, control loops. I would use the module for V1 so flash, crystal and RF circuitry are already solved. |
|     1 | **PAW3950DM-T5QU**                  | Primary optical X/Y mouse tracking                                                                                     |
|     1 | **LOAE-LSI1** lens                  | Optical lens for PAW3950                                                                                               |
|     1 | **TLV74318**                        | Local 1.8 V regulator required by the PAW3950 implementation                                                           |
|     1 | **ICM-42688-P**                     | 6-axis accelerometer + gyro                                                                                            |
|     3 | **TMAG5253BA2**                     | Analog position sensing for left, middle and right buttons                                                             |
|     3 | Small axial NdFeB magnets           | One attached to each button mechanism                                                                                  |
|     1 | **ADS7038**                         | 8-channel 12-bit 1-MSPS ADC for Hall/button feedback                                                                   |
|     3 | **LVCM-013-008-02**                 | Left, middle and right programmable haptic actuators                                                                   |
|     3 | **DRV8874**                         | Bidirectional H-bridge/current driver for the three voice coils                                                        |
|     1 | **MA735**                           | Absolute magnetic scroll-wheel angle sensor                                                                            |
|     1 | Diametric encoder magnet            | Mounted coaxially with scroll-wheel shaft                                                                              |
|     1 | **GB1806 / TSL-GB1806, no encoder** | 3-phase BLDC haptic scroll motor                                                                                       |
|     1 | **DRV8316R**                        | 3-phase BLDC driver with current sensing                                                                               |
|     1 | 2020/0606 RGB LED                   | Mouse status/profile indication                                                                                        |
|     3 | RGB current-limiting resistors      | One per R/G/B channel                                                                                                  |
|     1 | **TLV62569 / TPS62A0569**           | 5 V → 3.3 V logic supply, ~2 A capability                                                                              |
|     1 | USB-C receptacle                    | USB data + 5 V input                                                                                                   |
|     2 | 5.1 kΩ resistors                    | USB-C CC1/CC2 Rd resistors                                                                                             |
|     1 | **TPD2EUSB30**                      | USB D+/D− ESD protection                                                                                               |
|     2 | 22–33 Ω resistors                   | ESP32-S3 USB D+/D− series resistors                                                                                    |
|     1 | Reset/EN button                     | Development/recovery                                                                                                   |
|     1 | Boot button                         | ESP32 download-mode recovery                                                                                           |
| 1 set | Test/programming pads               | 3V3, GND, EN, GPIO0, UART etc.                                                                                         |
|     — | Decoupling capacitors               | 100 nF per IC plus device-specific bulk capacitors                                                                     |
|     — | Power bulk capacitors               | Especially around DRV8316 and the three VCA drivers                                                                    |
|     — | Pull-ups/pull-downs                 | As required by each IC                                                                                                 |
|     — | Inductor + feedback components      | For 3.3-V buck converter                                                                                               |
|     — | Misc. PAW3950 passives              | Follow the PAW3950 reference circuit exactly                                                                           |

The PAW3950 open reference design is useful here: it runs from a 3.3-V input but generates a local 1.8-V rail and uses a specific capacitor/resistor network around the sensor. It supports both LOAE-LSI1 and LM19-LSI optics. ([GitHub][1])

For the buttons, I would specifically change our previous driver choice to **DRV8874 ×3**. The LVCM-013-008-02 has a force constant of about **0.97 N/A**, 0.8 N continuous capability and 2.53 N short-duration capability. ([Moticont][2]) The DRV8874 handles 6 A peak, has only ~200 mΩ combined bridge resistance, and—very importantly—provides integrated current sensing and regulation. ([Texas Instruments][3])

That lets us use the ADS7038 very neatly:

```text
ADS7038

CH0  Left TMAG5253
CH1  Middle TMAG5253
CH2  Right TMAG5253

CH3  Left DRV8874 IPROPI
CH4  Middle DRV8874 IPROPI
CH5  Right DRV8874 IPROPI

CH6  spare
CH7  spare
```

So the ESP32 measures both:

```text
BUTTON POSITION
      +
ACTUAL ACTUATOR CURRENT
```

at high speed. The ADS7038 gives eight channels at up to 1 MSPS, so six channels is trivial. ([Texas Instruments][4])

The button feedback loops then become:

```text
TMAG5253
    │
    │ position
    ▼
ADS7038
    │
    ▼
ESP32-S3
    │
    │ desired force
    ▼
DRV8874
    │
    │ controlled current
    ▼
LVCM-013-008-02
    │
    ▼
finger


DRV8874 IPROPI ──────► ADS7038
       current feedback
```

That is a proper closed-loop haptic button rather than merely PWMing a coil.

The scroll system is similar:

```text
               finger
                 │
                 ▼
             scroll wheel
                 │
              GB1806
                 │
        dedicated encoder magnet
                 ▼
               MA735
                 │
              position
                 ▼
             ESP32-S3
                 │
            FOC / torque
                 ▼
             DRV8316R
                 │
               U V W
                 ▼
              GB1806
```

The GB1806 is a 7-pole-pair, 395-rpm/V gimbal motor with a 0.06 N·m/A torque constant and about 20 g mass without an encoder. That's much more appropriate for low-speed torque feedback than a high-KV drone motor. ([micronixmotor.com][5]) The DRV8316 gives us integrated FETs, integrated current sensing, 3/6-PWM control and SPI configuration in the `R` version. ([Texas Instruments][6])

For communication, I'd put almost everything on shared SPI:

```text
                        ESP32-S3

SPI SCLK/MOSI/MISO ───────────────┐
                                  │
            CS_PAW ───────── PAW3950
            CS_IMU ───── ICM-42688-P
            CS_ADC ───────── ADS7038
            CS_WHEEL ───────── MA735
            CS_DRV ───────── DRV8316R
```

with separate interrupt/fault lines where useful.

The ESP32-S3 has native USB Full-Speed device support, and Espressif recommends 22/33 Ω series resistors on GPIO19/20 when those pins are used for USB D−/D+. ([Espressif Documentation][7])

The overall block diagram becomes:

```text
                                USB-C
                                  │
                         ┌────────┴────────┐
                         │      5 V        │
                         │                 │
                    haptic power       3.3-V buck
                         │                 │
         ┌───────────────┼──────┐          │
         │               │      │          ▼
     DRV8874 ×3       DRV8316    │     ESP32-S3
         │               │      │          │
      VCA ×3           GB1806    │          │
                                         SPI bus
                                           │
                    ┌──────────┬───────────┼─────────┐
                    ▼          ▼           ▼         ▼
                PAW3950    ADS7038    ICM-42688    MA735
                    │          │
                1.8-V LDO      ├─ Hall L
                               ├─ Hall M
                               ├─ Hall R
                               └─ VCA currents


ESP32 ───────────────────────────── RGB status LED
```

There is one issue I would solve **before laying out the PCB: the power budget**.

Three LVCM actuators plus a BLDC wheel make this very different electrically from an ordinary mouse. The VCA has a 0.97 N/A force constant, meaning a fairly realistic 0.5-N click already corresponds to roughly:

$$
I \approx \frac{0.5}{0.97} \approx 0.52 A
$$

per active button.

The maximum short-duration rating corresponds to roughly 2.6 A, although we absolutely do not need that for normal mouse clicks. ([Moticont][2])

So I would impose firmware power budgeting:

```text
Normal button:
~0.3–0.7 A momentarily

Very strong button effect:
~1 A

Wheel normal detent:
tens to low hundreds of mA

Never allow:
3 VCAs at maximum
+
BLDC at maximum
simultaneously
```

A regular legacy USB port cannot reliably supply several amps. For V1 we can operate within the available USB current and cap haptic force. If later we want extremely strong haptics, I'd add either a small internal energy buffer/battery or explicit USB-C power negotiation.

One other design constraint is important: **magnet placement**. You now have at least four dedicated sensing magnets plus the BLDC rotor magnets:

```text
Left button magnet
Middle button magnet
Right button magnet
MA735 encoder magnet
GB1806 rotor magnets
```

The PCB/mechanical design needs to keep the magnetic sensing zones separated. In particular, the MA735 should have its dedicated diametric magnet very close to it, while the BLDC rotor field and button actuators should be sufficiently distant/oriented so they don't appreciably disturb its angle reading.

At this point, I would consider the electronics feature list complete. I would **not add any more functional ICs yet**. The next step should be converting this into an actual schematic-level architecture: power rails, ESP32 pin assignment, SPI chip selects, PWM outputs, ADC channels, motor-driver connections and connectors.

[1]: https://github.com/badjeff/paw3395-pcb?utm_source=chatgpt.com "GitHub - badjeff/paw3395-pcb: An open source breakout board for PixArt PAW3395DM-T6QU / PAW3950DM-T5QU low power optical mouse sensor. · GitHub"
[2]: https://www.moticont.com/site-map.htm?utm_source=chatgpt.com "Site Map | Moticont"
[3]: https://www.ti.com/product/DRV8874?utm_source=chatgpt.com "DRV8874 data sheet, product information and support | TI.com"
[4]: https://www.ti.com/product/ADS7038?utm_source=chatgpt.com "ADS7038 data sheet, product information and support | TI.com"
[5]: https://micronixmotor.com/shop/bldc-gimbal-motor-tsl-gb1806/?utm_source=chatgpt.com "BLDC Gimbal Motor with AS5600/AS5048A Encoder"
[6]: https://www.ti.com/product/DRV8316?utm_source=chatgpt.com "DRV8316 data sheet, product information and support | TI.com"
[7]: https://documentation.espressif.com/esp-hardware-design-guidelines/en/latest/esp32s3/esp-hardware-design-guidelines-en-master-esp32s3.pdf?q=hardware+guidelines&title=ESP32-S3+Hardware+Design+Guidelines&utm_source=chatgpt.com "Chapter 1. Latest Version of This Document"





Yes. That is actually a cleaner architecture for this mouse.

Use a **self-powered USB hub internally or inline**:

```text
PC
│
│ USB data
│
▼
Powered USB hub
│
├── USB 2.0 data ─────► ESP32-S3
│
└── dedicated 5 V power ─────► mouse haptics
                              ├── 3× voice coils
                              └── BLDC wheel
```

The PC can still see the mouse as an ordinary **USB 2.0 Full-Speed HID device**. The hub does not force the downstream device to become USB 3.x just because the hub itself supports newer USB. USB explicitly supports USB 2.0 devices behind hubs. ([USB-IF][1])

The important distinction is power.

A conventional self-powered USB 2.0 hub downstream port is normally specified around **500 mA**, and a USB 3.x self-powered port around **900 mA**. ([USB-IF][2]) So simply buying an old powered hub does not automatically give your mouse 2–3 A while remaining standards-compliant.

But with **USB-C**, a downstream hub port can advertise:

* Default USB current
* 1.5 A @ 5 V
* **3.0 A @ 5 V**

independently of whether the attached device uses USB 2.0 data. USB Type-C explicitly allows a host or downstream hub port to advertise higher current through the CC pins. ([USB-IF][3])

So the ideal setup is:

```text
                    external PSU
                     5 V / 3–5 A
                          │
                          ▼
PC ─── USB 2/3 ───► powered hub/controller
                          │
                 USB-C downstream port
                          │
                 ┌────────┴─────────┐
                 │                  │
               D+/D-               VBUS
                 │                  │
                 ▼                  ▼
             ESP32-S3          haptic power
                                 │
                       ┌─────────┼─────────┐
                       │         │         │
                     VCA L     VCA M     VCA R
                                           │
                                        BLDC
```

The mouse's USB-C connection can advertise/enumerate as:

```text
USB device class: HID
USB speed:        Full Speed
Polling:          1000 Hz
Data:             USB 2.0 D+/D-
```

while simultaneously seeing:

```text
VBUS = 5 V
CC advertisement = 3 A
```

So, yes:

> **USB 2.0 mouse data + 5 V / 3 A from a powered USB-C hub is completely reasonable.**

In fact, I prefer this to requiring a high-power PC port.

For a desk mouse you could have a small powered hub/dongle like:

```text
             PC USB
               │
       ┌───────┴────────┐
       │ Mouse Power Hub│
       │                │◄── USB-C PD wall adapter
       └───────┬────────┘
               │
            USB-C
               │
             mouse
```

The mouse itself then only needs one cable.

There is another even cleaner possibility: don't make the intermediate box a general-purpose USB hub at all. Make it effectively a **powered USB 2.0 repeater/hub with one downstream Type-C port**. Internally:

```text
USB upstream
     │
 USB2512B / similar USB 2 hub IC
     │
 downstream D+/D-
     │
 mouse

external 5V
     │
current-limited power switch
     │
downstream VBUS
```

You could therefore build a tiny dedicated **mouse power adapter**.

One caution: if you want to advertise **3 A via USB-C**, the power source/hub needs to implement Type-C current advertisement correctly. Don't simply connect a 5 V / 5 A supply to VBUS and assume the mouse may consume whatever it wants. The sink is supposed to detect the advertised current through CC and remain within it. ([USB-IF][3])

For our mouse I'd therefore have:

```text
Mouse USB-C
    │
    ├── D+/D- ─── ESP32-S3
    │
    ├── CC1 ─┐
    └── CC2 ─┴── Type-C sink/current detector
                      │
                      ▼
                  ESP32-S3
```

Then firmware knows:

```text
500/900 mA available
→ haptics restricted

1.5 A available
→ normal haptics

3.0 A available
→ full haptics
```

And because you're likely to make your own powered hub anyway, I'd make its downstream port always advertise **5 V / 3 A**.

That gives the mouse up to **15 W peak input power**, while the PC still just sees a normal USB 2.0 mouse. ([USB-IF][3])

For this project, I think this is preferable to trying to make the mouse itself USB 3.x.

[1]: https://www.usb.org/sites/default/files/3.2%20Interoperability%20Testing%20v0.99%20w%20USB%20Type-C.pdf?utm_source=chatgpt.com "USB Implementers Forum"
[2]: https://www.usb.org/sites/default/files/USB20_32_BC12_Drop_Droop_1_4_1.pdf?utm_source=chatgpt.com "P a g e  | 1"
[3]: https://www.usb.org/sites/default/files/USB%20Type-C%20Spec%20R2.0%20-%20August%202019.pdf?utm_source=chatgpt.com "Release 2.0"

For this project, I would use a split license rather than forcing one license onto everything.

* Hardware/PCB/CAD: **CERN Open Hardware Licence v2 – Strongly Reciprocal (CERN-OHL-S)**
* Firmware: **GPL-3.0-or-later**
* PC configuration software: **GPL-3.0-or-later**
* Documentation: **CC BY-SA 4.0**

For your stated goal—open source, including the physical mouse design—I think **CERN-OHL-S** is the most important choice. It is specifically designed for open hardware and requires modified hardware designs to remain open when distributed.

If you want commercial companies to be able to incorporate the design into proprietary products, use **CERN-OHL-P** instead. If you want improvements to this mouse to stay open, use **CERN-OHL-S**.

I would structure the repository roughly like:

```text
Mouse/
├── hardware/
│   ├── pcb/
│   ├── schematics/
│   ├── bom/
│   └── LICENSE             CERN-OHL-S-2.0
│
├── mechanical/
│   ├── housing/
│   ├── scroll-wheel/
│   └── button-mechanisms/
│       LICENSE             CERN-OHL-S-2.0
│
├── firmware/
│   └── LICENSE             GPL-3.0-or-later
│
├── software/
│   └── LICENSE             GPL-3.0-or-later
│
└── docs/
    └── LICENSE             CC-BY-SA-4.0
```

If you prefer maximum adoption and don't care whether companies make closed derivatives, then I'd instead use:

```text
Hardware:   CERN-OHL-P-2.0
Firmware:   MIT
Software:   MIT
Docs:       CC-BY-4.0
```

For this particular mouse, though, my recommendation is the stronger setup:

**CERN-OHL-S-2.0 + GPL-3.0-or-later + CC BY-SA 4.0.**

That keeps both the electronics/mechanical design and the software improvements open.
