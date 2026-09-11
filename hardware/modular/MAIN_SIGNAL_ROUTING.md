# Main analog, digital and return-path routing

2026-09-11. The shaped [Main PCB](main/Main.kicad_pcb) is fully connected:
**zero native unrouted connections, zero physical DRC violations and zero
schematic-parity issues**. All 246 footprints and 781 checked connected-pin
assignments remain present. This is a routed prototype, not a fabrication release.
Mechanical integration and panelization remain subject to the
[interface register](MECHANICAL_INTERFACES.md).

This pass completes ADC1/Hall/button sensing, USB data, SPI3, SPI2, optical
support, IMU, encoder/configuration branches, interrupts, GPIO, RGB, telemetry
and remaining logic supplies. The source/actuator/interlock and input-power
regression checks still pass. The wheel, encoder and original monolithic PCB
were not changed.

## Analog locality and thermal clearance

All 13 main analog nets are connected and pass
[verify_main_analog.py](verify_main_analog.py) with `--require-reviewed`.
The [saved report](main-analog-review.json) separates geometry findings from
connectivity and records the exact board hash.

| Net | Total copper length | Signal vias |
| --- | ---: | ---: |
| HALL_L / HALL_M / HALL_R | 45.706 / 28.671 / 22.992 mm | 6 / 5 / 0 |
| BTN_L_ISENSE / BTN_M_ISENSE / BTN_R_ISENSE | 39.930 / 36.514 / 20.016 mm | 2 / 6 / 2 |
| BTN_L_VREF / BTN_M_VREF / BTN_R_VREF | 5.230 / 11.345 / 6.026 mm | 0 / 2 / 2 |
| ACT_VMON | 25.930 mm | 4 |
| ADC_DECAP | 1.950 mm | 0 |
| USB_IMON_BUF / USB_IMON_ADC | 36.594 / 7.109 mm | 2 / 4 |

ADC1 and all three Hall sensors retain their placement. Hall/paddle geometry
remains provisional despite the improved routes. C36 is now 3.351 mm from
ADC1's actuator-monitor input. R16/R17, R67/R68 and D4 were relocated to improve
the middle-button reference and actuator-monitor network.

R24 was moved to (65, 40.5) mm and the right IPROPI route was redrawn. Its old
route enclosed the driver's front ground copper. The revised route leaves
43.296 mm² of front copper connected to U6's exposed pad, above the unchanged
35 mm² regression floor. Each button driver retains four local thermal vias;
their front/back spreading checks pass.

The analog checker finds no missing front In1 shadow. Necessary switching
proximity at driver pins is reviewed within explicit 1.5 mm launch regions.
The checker also examines every segment outside those regions; a nearby pin
cannot hide an extended adjacent run. This is not ADC-noise or settling
qualification.

Seven fixed circuit footprints and twelve back test pads moved. Their exact
before/after coordinates are in the
[placement-change record](main-routing-placement-changes.json). J1, J2/J3/J4,
J6, J8, J10, ADC1, the Hall sensors and PMW3360 retained their datums. No component
values, pin assignments or schematic connections changed.

## USB data

The pair uses the selected JLC041611-2116 geometry: **0.1466 mm width and
0.1501 mm edge gap**, on F.Cu throughout, with no signal vias. Both reversible
connector paths pass continuity through U1 and the series resistors.

The [USB report](main-usb-review.json) independently checks this board's saved
In1 copper, including a 0.327 mm margin beyond the trace edge. Uncovered area
is zero. U1 has a direct ground-land via; its filled/capped treatment remains
part of manufacturing review. Measured CAD contact-path skew is 1.837 mm for
orientation A and 0.253 mm for B. Approximately 93.2% of connector-side copper
has the selected pair spacing. This does not certify manufactured impedance
or USB compliance.

## SPI, optical and test branches

The dedicated ADC2 bus reaches J8; U25 remains the main-side return buffer.
Forward buffering is on the wheel board. Selected main-board path measurements
are:

| Path | Counted conductor | Counted vias |
| --- | ---: | ---: |
| MCU clock to J8.10 | 67.291 mm | 7 |
| MCU MOSI to J8.12 | 52.084 mm | 6 |
| J8.16 to U25 input | 16.945 mm | 2 |
| U25 output to MCU MISO | 68.114 mm | 6 |
| MCU ADC2 select to J8.14 | 45.666 mm | 2 |

The longest listed PCB-only delay screen is about 0.63 ns using 8 ps/mm and
full 1.6 mm via barrels. It excludes buffers, ADC, connectors, cable and MCU
sampling. The existing [interface timing finding](INTERFACE_REVIEW.md) remains:
the 28 ns device-delay estimate already exceeds a 20 MHz unshifted half-cycle.
Start bring-up at 1 MHz with the motor stopped and characterize 10 MHz before
attempting 20 MHz. Routing does not close that timing requirement.

SPI2 reaches ADC1, the optical buffers, IMU and encoder/DRV8316 configuration
paths. PMW3360 reset, local rails, ramp, pixel supply and LED circuitry are
connected. The aperture and lens reservations remain intact. CS_PAW, ADC2 and
encoder test pads were moved onto short branches of actual routes. All eight
audited SPI test branches are at most 0.141 mm in the graph screen. Device
branches still have propagation delays and loading; the shared bus and FFC
require oscilloscope checks with the selected cable and assembled parts.

## Supplies and actual return copper

Remaining +3V3 and switched sensor supplies are connected. New 0.30 mm logic
supply branches shorten the IMU feed. The conservative source-to-IMU resistance
screen fell from approximately 0.60 Ω to 0.25–0.26 Ω, with ten counted barrels
instead of 26. The MCU feed screens at 0.243 Ω. These are whole-segment/barrel
path estimates at 80 C, not load-step or ampacity acceptance. The seven audited
local bypass supply paths are 0.763–4.446 mm long.

In1 remains a single saved ground outline with **no routed tracks**. Secondary
GND fills on In2 and B.Cu join the main reference through ground vias. Bare vias
connected only to In1 are not counted as useful return transitions. The digital
audit requires nearby vias to contact both primary and secondary saved copper;
every audited transition has one within 3 mm.

The audit projects every audited digital route, on all routing layers, onto
the saved In1 reference. Front shadows are complete. A 0.000106 mm² primary
shadow sliver on CS_DRV8316 is below the explicit 0.0002 mm² polygon tolerance;
the raw measurement remains in the report. Polygon approximation is 1 µm.
USB has its separate, wider reference-corridor check.

Inner/back traces have a more distant primary reference than front traces.
Secondary fills contain signal crossings and are not uninterrupted impedance
planes. Copper shadows and stitching establish geometric return provisions;
they do not certify impedance, crosstalk, EMI, rail transients or temperature.
The optical, wheel, antenna and FFC reservations are preserved in the fills.

## Reproduce the checks

Use KiCad's bundled Python. The reports below all refer to the saved main PCB.

```powershell
kicad-cli sch export netlist --format kicadxml --output build/modular/main-review/netlist.xml hardware/modular/main/Main.kicad_sch
kicad-cli pcb drc --format json --schematic-parity --output build/modular/main-drc.json hardware/modular/main/Main.kicad_pcb
python hardware/modular/verify_main_analog.py --board hardware/modular/main/Main.kicad_pcb --output hardware/modular/main-analog-review.json --require-reviewed
python hardware/modular/verify_main_routing.py --board hardware/modular/main/Main.kicad_pcb --output hardware/modular/main-routing-review.json --require-reviewed
python hardware/kicad/verify_usb_layout.py --board hardware/modular/main/Main.kicad_pcb --output hardware/modular/main-usb-review.json
python -m unittest discover -s hardware/modular -p test_*_checks.py
```

All **59 modular regression tests pass**. The input-power, actuator/control and
placement reports are also refreshed.
Fault-injection tests cover open ADC/SPI paths, remote filtering, driver-launch
limits, USB continuity/geometry/ESD, saved-plane voids, In1 signal routing and
missing secondary return copper.

Next comes mechanical-interface CAD and resulting PCB adjustments, followed by
a whole-board review, common-stack encoder migration, cable/manufacturing
closure and panelization. Filled/capped vias, exposed-pad/stencil details, stock,
probe access with the mechanism fitted and a final assembled quote remain open.
