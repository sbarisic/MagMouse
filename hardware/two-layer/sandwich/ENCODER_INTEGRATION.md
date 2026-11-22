# Integrated motor encoder

Use the TSL/SteadyWin GB1806 with the **AS5048A SPI encoder**, not the AS5600 or
encoder-free variant. This replaces the separate MA735 PCB, magnet and mount.
Lower, Upper and Wheel remain separate installed boards supplied on one panel.

## Wiring

Wheel J5 retains the three motor phase wires. Lower J6 connects directly to the
motor encoder. Wire by the module's printed signal labels: the supplier table
does not establish numbered connector positions. Its PWM output is unused.
The three J6 grounds can share the module GND connection. Keep clock and return
wiring short and away from motor phases.

| Lower J6 pad | Net | Motor module signal |
| --- | --- | --- |
| 1 | ENC_5V | VDD5V |
| 2, 4, 7 | GND | GND |
| 3 | ENC_SCLK_LOCAL | CLK |
| 5 | ENC_MOSI_LOCAL | MOSI |
| 6 | ENC_CS_LOCAL | CSn |
| 8 | ENC_MISO_LOCAL | MISO |

GPIO37 remains encoder CS; the net is now `CS_ENCODER`. Clock/MOSI/MISO retain
GPIO12/11/13 and shared SPI2 ownership. Main and Wheel retain their 19-wire maps.

## Supply and isolation

PWR_5V → U33 regulated RGB_5V → U28 switched ENC_5V powers the encoder module.
U42 (TLV75533PDBVR) derives local ENC_3V3 for U29 and its CS pull-up R99.
C55/C64 are 1 µF LDO input/output capacitors; C105 bypasses U29 with 100 nF.
U25 retains the CS-controlled MISO return to the shared bus.

The input eFuse's approximately 6 V OVLO cannot protect 5.5 V-rated encoder
parts by itself. U28 therefore uses U33's regulated output rather than raw
PWR_5V. Both U33 and U28 use HALL_EN. U28 retains output discharge through
R125; U42 has output discharge. The encoder shares U33 with the single RGB LED.

Reserve **25 mA at 5 V** for the encoder branch, including module overhead and
buffers; this is an allocation, not measured consumption. The IC specifies up
to 15 mA. Keep the combined LED/encoder load below U33's 200 mA rating and check
thermal rise. U33 is not a boost converter: verify at least 4.5 V at the module
under cable drop, LED activity and motor load. Valid SPI does not prove supply
margin. Keep motor drive disabled until supply and angle checks pass.

AS5048A logic thresholds reference its 3.0–3.6 V core even in 5 V supply mode:
VIH ≥ 0.7 × VDDCORE and VOH ≥ VDDCORE − 0.5 V. Keep U29 and R99 on ENC_3V3;
never connect them to ENC_5V. U25 drives the MCU bus from main 3.3 V. Check the
actual module for added buffers/pull-ups. Do not load its internal VDD3V output.

Static checks use the full -40 to +125 °C buffer limits and TLV755P's ±1.5%
output accuracy, giving ENC_3V3 = 3.2505–3.3495 V:

| Path | Worst-case check | Margin |
| --- | --- | --- |
| U29 high → encoder | 3.2505 − 0.3 V output versus 0.7 × 3.6 V input | 0.4305 V |
| U29 low → encoder | Conservative 0.8 V output versus 0.3 × 3.0 V input | 0.1 V |
| Encoder high → U25 | 3.0 − 0.5 V output versus 2.0 V input | 0.5 V |
| Encoder low → U25 | 0.4 V output versus 0.8 V input | 0.4 V |

The high-output calculation assumes at most 100 µA static load; the bare
encoder inputs meet this, but added module loads must be checked. R99 draws
about 0.335 mA when CS is low, below the buffer's specified sink-current test
load. These DC checks do not establish the 10 MHz cable timing margin.
U33's regulated maximum is 5.0625 V before transients, below the 5.5 V operating
limits of U28/U42 and the encoder. Dropout and cable losses set the lower limit.
The saved-copper resistance screen estimates 11.368 mV from U33 to U28 and
8.526 mV from U28 to J6 at 25 mA (80 °C copper model). Add the regulator/switch
and external-wire drops separately; these values are not measured voltages.

Before enabling HALL_EN, clear motor permission, deselect every SPI target,
and hold clock/MOSI low. Reserve at least 10 ms after the encoder supply becomes
valid before angle initialization; use a provisional 20 ms overall wake guard
and extend it if measured rail settling requires it. U29's powered-off outputs
are high impedance, and U25 stays disabled by the host-side CS pull-up.

Before shutdown, remove motor permission, finish the transaction, deselect CS
and park clock/MOSI. R125 remains 0 Ω into U28's internal discharge path.
U42's EN follows ENC_5V; its internal discharge operates on disable/UVLO, not
directly on HALL_EN. It has no reverse-current blocking. Scope both rails during
shutdown/unplug and require ENC_3V3 ≤ ENC_5V + 0.3 V; the module's unknown input
capacitance/load prevents a guaranteed discharge waveform from this CAD review.
Failure requires a discharge/protection revision before hardware acceptance.

## Firmware specification (not executable firmware)

- Use SPI mode 1, MSB first, 16-bit frames. Start at 1 MHz; the 5 kHz sampling
  target assumes a validated 10 MHz link. Minimum CS setup/hold/high times are
  350/50/350 ns; use 1 µs guards for each.
- Send an even-parity read of angle register 0x3FFF, followed by NOP to receive
  its response. Discard the initial stale response. Check response parity and
  error flag; clear/read errors and verify magnetic/AGC diagnostics before torque.
  Angle read is 0xFFFF and NOP is 0x0000. Read 0x0001 to clear errors, then
  clock out its response and confirm recovery. In diagnostics 0x3FFD require
  OCF=1, COF=0 and no field-limit flags; inspect magnitude 0x3FFE periodically.
- Two frames per fresh read require 32 bits × 5 kHz / 10 MHz = 16 µs/ms of clock
  time, replacing 8 µs/ms. With three 1 µs guards per frame, reserve at least
  46 µs/ms before software overhead; at 1 MHz this becomes 190 µs/ms. Retain the
  bus owner's optical-burst limits. Wire occupancy is not sensor latency.
- Unwrap modulo 16384 with signed differences in [-8192,8191]. Calibrate direction
  and electrical zero, verify the motor's seven pole pairs, and account for
  sensor delay in FOC. Do not program OTP/NVM during operation.
  The sensor's specified 90.7–110.2 µs propagation delay is additional to bus
  scheduling and transfers; timestamp samples and include this in angle-age limits.
- Invalid or missed angle deadlines command zero torque, clear ACT_REQ and stop
  heartbeat. Reinitialize and obtain valid samples before rearming. Deselect SPI
  before sensor shutdown; initialize again after wake.

## Validation limits and bring-up

All 37 bottom test pads are removed. Six top test pads remain: Lower TP38/TP39
and Wheel TP34–TP37. UART0 pins become unused after TP4/TP5 removal; USB download
and BOOT/RESET switches remain. Bottom traces, vias and functional wire pads stay.

CAD checks cover ERC/DRC/parity, component spacing, panel copper translation and
USB reference copper. Bench checks still need to measure supply startup/discharge,
SPI voltages while sensors are off, bus isolation, LED noise, cable-drop margin,
360° angle continuity, diagnostics, direction, zero, latency and fault shutdown.
Check the encoder-equipped motor's dimensions, shaft and strain relief in the
housing. PCB exports do not establish fit of a complete motor assembly.

The [acceptance record](encoder-review.json) binds all three boards to their
source hashes and records zero ERC, DRC, parity, connectivity and non-ground
planar trace findings. It checks the immutable pre-change geometry/rules,
2 mm component spacing and retained top test points. The later three-board
routing cleanup changes USB fanouts and local jogs, while preserving the wide
paired trunks, layer-transition vias and full-width USB ground coverage.
`routing-cleanup-review.json` records the independent bend/staircase checks and
before/after measurements. The panel manifest checks exact translated source copper
and router/tab geometry. These are CAD results, not hardware validation.

## Sources

- [GB1806 variants and module labels](https://micronixmotor.com/shop/bldc-gimbal-motor-tsl-gb1806/)
- [ams AS5048A datasheet, v1-11 (manufacturer PDF mirrored by SparkFun)](https://cdn.sparkfun.com/assets/e/d/e/1/d/AS5048_DS000298_4-00.pdf)
- [TPS7A24 regulated rail](https://www.ti.com/product/TPS7A24)
- [TPS22919 load switch](https://www.ti.com/product/TPS22919)
- [TLV75533PDBVR regulator](https://www.ti.com/product/TLV755P/part-details/TLV75533PDBVR)
- [74LVC125A buffers](https://assets.nexperia.com/documents/data-sheet/74LVC125A.pdf)
