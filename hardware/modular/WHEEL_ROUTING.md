# Wheel PCB routing

2026-09-11. The editable source is [wheel/Wheel.kicad_pcb](wheel/Wheel.kicad_pcb).
It has 87 front-side footprints on the 55 x 60 mm, four-layer outline. All
connections are routed: **zero native unconnected items, zero physical DRC
violations and zero schematic-parity issues**. The earlier power/analog pass
left 61 connections; this pass finishes those nets and their ground returns.
It is not yet a manufacturing release. Panelization is on hold until both
boards have stable placement and mechanical interfaces.

## Completed copper

- ACT_5V connects all 24 local terminals, including J11, C90/D6, driver VM
  bypassing, brake loads and TP34. The main back-side supply uses 1.5–1.8 mm
  tracks and multiple 0.6/0.3 mm through vias at power transitions. Smaller
  branches serve local bias/bypass circuits. These widths are prototype layout
  choices, not a measured ampacity or temperature-rise qualification.
- All three phases leave the bottom of U21 and run on the front to J5. Each
  uses short 0.25 mm pin escapes followed by 0.85 mm copper. No phase track
  enters the sensing area above U21. The total copper on each phase is
  22.81–23.37 mm, including the paired driver-pad branches.
- The four brake resistors have back-side supply feeds and a front-side drain
  bus to Q5. U30 was rotated and C65/C67 moved to shorten the brake reference
  and sensing connections. All brake nets connect, including feedback and test
  points. BRAKE_GATE is 5.27 mm of copper; BRAKE_OUT is 13.40 mm, BRAKE_REF
  17.97 mm and BRAKE_SENSE 12.05 mm. These are whole-net copper totals, including
  branches, not measured comparator-to-gate delay. All four are front-only.
- Driver charge-pump/buck support, DRV_AVDD and ADC2 decoupling are connected.
  C44/C47 and the VM capacitors were adjusted for direct pin escapes. The three
  current-sense filter resistors now follow the U21 output pin order.
- In1 has one connected saved GND outline. Front/back ground copper and local
  return vias support the driver, ADC, brake, input bulk and bypass capacitors.
  U21 has nine ground vias in its exposed pad; U23 has one in its exposed pad.
  U30, C65 and several signal/buffer pads also use vias in pads. **Specify filled
  and capped vias and confirm the process in the eventual quote.**

## Digital completion and ground returns

ADC2 SPI, driver configuration SPI, PWM, enables, fault, DRVOFF, +3V3 and the
ADC spare-input ties now connect. Tight IC escapes use staggered **0.45 mm pad /
0.20 mm hole** through vias. Existing high-current transitions retain their
larger vias. JLCPCB's [multilayer quote guidance](https://cart.jlcpcb.com/quote?fromDemo=yes)
lists the 0.45/0.20 mm geometry; filling/capping remains a separate order option.
The wheel project's minimum via diameter, drill and annular ring are now
0.45, 0.20 and 0.125 mm. Track clearance remains 0.15 mm; In1 zone clearance
remains 0.20 mm. No DRC exclusions were added.

DRV_AVDD was redistributed across F.Cu, In2.Cu and B.Cu to free the digital
escapes; its 19 endpoints remain connected. The sensitive six current-sense
nets and brake gate/reference/sense routes retain their front-only routing.
All 15 J9 ground contacts have dedicated return vias. Ground stitching and
local buffer ground vias close the fill islands created by digital routing.
Two signal crossings under the FFC were moved to B.Cu to preserve those returns.

The saved report inventories each SPI net's copper and vias. ADC2 local SCLK
and MOSI have 12.71 and 10.43 mm of copper and two vias each. The local ADC2
MISO net totals 25.16 mm, including its bias branch. These are layout measures,
not validated timing or signal-integrity results. The 20 MHz target still needs
the previously documented sampling-phase and connected-cable measurements.

## Current-sense review

| Channel | SO copper | Filtered ADC copper | Signal vias |
| --- | ---: | ---: | ---: |
| A | 2.82 mm | 5.42 mm | 0 |
| B | 2.14 mm | 4.60 mm | 0 |
| C | 2.05 mm | 5.22 mm | 0 |

The filtered totals include capacitor branches. All six nets stay on F.Cu.
Their complete trace-width shadows have saved In1 GND underneath. The same
shadow check passes for ADC2_DECAP, DRV_AVDD, BRAKE_REF and BRAKE_SENSE.
The closest projected gap from any of the six sensing nets to the checked
phase, brake-drain, charge-pump or buck-switch tracks is **1.785 mm**. The
regression floor is 0.5 mm, including opposite-layer projections. All 36
checked power/analog ground pads connect to the saved In1 fill.

## Reproduce the checks

Use the installed KiCad Python and CLI executables. Export the wheel netlist
to `build/modular/wheel-review/netlist.xml` with the schematic review exporter
if it is absent. Run from the repository root:

```powershell
kicad-cli pcb drc --format json --schematic-parity --output build/modular/wheel-drc.json hardware/modular/wheel/Wheel.kicad_pcb
python hardware/modular/verify_wheel_routing.py --board hardware/modular/wheel/Wheel.kicad_pcb --output hardware/modular/wheel-routing-review.json
python hardware/modular/verify_wheel_placement.py --board hardware/modular/wheel/Wheel.kicad_pcb --netlist build/modular/wheel-review/netlist.xml --drc build/modular/wheel-drc.json --output hardware/modular/wheel-placement-review.json
python -m unittest discover -s hardware/modular -p test_wheel_routing_checks.py
python -m unittest discover -s hardware/modular -p test_wheel_placement_checks.py
```

The [routing report](wheel-routing-review.json) fingerprints the PCB and records
connectivity, front-only routing, lengths, phase widths, ground shadows,
switching separation and thermal-via count. Six routing regression tests cover
the saved board and failures from missing In1 reference, a narrowed phase, phase
encroachment, an ADC signal via and a disconnected SPI pad. Four placement tests
also pass. Whole-board endpoint checks cover every multi-pad named net. Native DRC
and schematic parity remain separate required checks; the geometric checker
does not substitute for them. It also rejects net reassignment during native
connectivity rebuilding, which can otherwise obscure a short.

## Next work and acceptance limits

The wheel is now zero-unrouted. The [shaped main PCB](MAIN_PLACEMENT.md) is
placed from its split schematic and remains to be routed. Resolve board mounts,
motor/wheel/encoder supports, cable bends and optical stack together in mechanical
CAD. Do not start panelization until both boards' placement and interfaces are stable.

Bench validation still needs to establish current-reading noise/settling,
brake reaction and regenerative voltage peaks, power-transition losses, and
temperature rise. This pass does not approve the 20 MHz SPI3 timing target,
motor current, continuous braking power, or the completed assembly. Cable mating
tolerances, mounting, test access, final silkscreen and panel tooling remain open.
The fully connected internal-cable assumption is unchanged; cable-disconnect
survival is outside this prototype's acceptance scope.

The original monolithic PCB and its copper remain unchanged. The historical
`wheel-placement.json` describes the starting placement; do not regenerate it
over this routed board.
