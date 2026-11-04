# Two-layer layout review — 2026-11-03

The cleanup checkpoint passes KiCad 10.0.6 DRC with no reported warnings or
errors, no unrouted connections and no schematic-parity findings on all three
boards. Component values, footprints and pad-to-net assignments match the
source boards. Source PCB hashes and schematic contents are preserved.
See [summary.json](summary.json) for exact board hashes and check results.

## Main repairs

- Trimmed CC_OUT2 at (128.70, 30.75) mm and CS_ADC2 at (116.30, 66.55) mm.
- Trimmed both CS_IMU overruns to their shared junction at (88.35, 84.45) mm.
- Removed three redundant WHEEL_PWM_A segments beside the MCU. Their acute
  intersection with the retained direct route produced the copper-sliver
  warning near (128.053, -16.213) mm. The retained left branch now connects
  directly to the pad center at (122.00, -17.45) mm.

The changes remove about 29.0 mm of excess routed copper. Zone fills were
regenerated. There are no component moves, net changes or changes to the Wheel
and Encoder PCB sources. [trim_main_stubs.py](../trim_main_stubs.py) records the
guarded repairs; re-running it on this checkpoint makes no changes.
Replaying the repairs against a copy of the original checkpoint with its project
settings reproduced the final PCB byte for byte. The schematic-comparison check
was also exercised with CRLF/LF equivalents and a changed value: it accepts the
line-ending difference and rejects the content change.

## Visual screening and measured priorities

Front-copper overviews of all three boards and the repaired MCU area were
inspected. The local PWM branch now joins at the pad without the acute redundant
branch. Main remains a large, dispersed bench layout with long inter-group
routes; Wheel's motor-driver area and Encoder remain comparatively compact.
This screening does not complete assembly, solder-mask, silkscreen, thermal or
mechanical review.

The native exports provide front copper, back copper and fabrication placement:

| Board | Front copper | Back copper | Placement |
| --- | --- | --- | --- |
| Main | [front](Main-front.svg) | [back](Main-back.svg) | [placement](Main-placement.svg) |
| Wheel | [front](Wheel-front.svg) | [back](Wheel-back.svg) | [placement](Wheel-placement.svg) |
| Encoder | [front](Encoder-front.svg) | [back](Encoder-back.svg) | [placement](Encoder-placement.svg) |

[routing.json](routing.json) measures total copper on each net, including all
branches. These numbers are not endpoint path lengths or propagation delays.

| Main net | Total copper, mm | Vias |
| --- | ---: | ---: |
| SPI_SCLK | 449.3679 | 32 |
| SPI_MOSI | 343.9657 | 21 |
| SPI_MISO | 363.6216 | 35 |
| MOTOR_SPI_SCLK | 223.8117 | 8 |
| MOTOR_SPI_MOSI | 243.2315 | 13 |
| MOTOR_SPI_MISO | 223.6822 | 9 |
| WHEEL_PWM_B | 515.9850 | 28 |

Prioritize the shared SPI bus and the long PWM route for topology review and
placement/routing reduction. The [interface plan](../../../docs/interfaces.md)
has initial 20 MHz ADC and 10 MHz encoder/IMU targets; this layout has not
validated those targets. Check source-to-load paths, branch lengths, return
continuity and loaded waveforms before selecting operating clocks.

USB_DP and USB_DM have 63.6234 and 59.5526 mm of copper, respectively, with no
vias; the separate MCU-side nets add 1.9786 and 2.3099 mm. The main-run and
escape widths remain 1.10 and 0.1466 mm. These measurements do not certify pair
impedance, effective skew or USB operation. Keep the fabricator-stack and USB
validation work open.

Main's ACT_5V, PWR_5V and VBUS_USB width inventories include 0.15 mm segments.
Determine which are low-current branches versus load-carrying paths before
using width alone to assess voltage drop or heating. Review source-to-load
resistance, via bottlenecks and return paths against the
[power plan](../../../docs/power.md). No current-rating conclusion is made here.

[reference-copper.json](reference-copper.json) still records gaps in opposite-side
ground coverage for some analog and digital routes. It includes pad/via
clearances and is a geometric screen, not a noise or signal-integrity model.

## Validation limits and next work

The saved projects still ignore missing courtyards, off-center track/via ends,
tuning-profile geometry, footprint-filter mismatch and footprint-type mismatch.
No severity or exclusion settings were changed to obtain this pass. The new
strict-warning mode checks reported findings under those existing settings.

Next work is Main routing/placement optimization, power and return-path review,
then USB/SPI and actuator bench measurements. Via-in-pad assembly, antenna and
fixture clearances, final outlines, and a replacement panel remain open. This
checkpoint is not a fabrication release.
