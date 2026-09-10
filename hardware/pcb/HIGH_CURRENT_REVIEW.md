# Actuator high-current review

2026-09-10, KiCad 10.0.6. This pass improves the existing actuator layout and
adds checks for its current paths, local ground spreading and rail storage.
The 60 x 95 mm outline, 317 footprints, schematic and BOM are unchanged.

The subsequent [analog pass](ANALOG_LAYOUT.md) reroutes signal copper and extends
U4's front ground spreader. The measurements and hash below describe this
high-current pass; use the regenerated reports for the latest saved board.

## Copper changes

Thirty-one existing tracks are wider. The three button-driver VM escapes are
now 0.35 mm; their former 0.25 mm output escapes are 0.30 mm. U21's six ground
pin returns are now 0.35 mm instead of 0.20 mm. The main supply and phase
trunks retain their previous widths. Native DRC confirms the wider tracks fit.

Ten named local GND zones add front/back spreading at U4, U5, U6, U21 and Q5.
They use solid pad connections, 0.20 mm zone clearance and removal of unconnected
islands. Existing tracks and vias provide the local connections. This follows
the ground-plane/thermal-via approach in the
[DRV8231A layout guidance](https://www.ti.com/lit/ds/symlink/drv8231a.pdf).
The [DRV8316 guidance](https://www.ti.com/lit/ds/symlink/drv8316.pdf) also calls
for short bulk-current paths, wide copper and multiple transition vias.
These additions improve available spreading area; their thermal performance
has not been measured.

| Device | Front filled area at device ground, mm² | Back filled area reached by local vias, mm² |
| --- | ---: | ---: |
| U4, left button | 22.795 | 30.588 |
| U5, middle button | 19.545 | 18.602 |
| U6, right button | 43.003 | 40.910 |
| U21, wheel | 33.500 | 38.285 |
| Q5, brake | 2.937 | 5.653 |

Areas count saved filled polygons at the device/locally connected vias and
subtract holes. They exclude other fragments of the same zone. They are
geometric regression measurements, not equivalent thermal areas for a
datasheet junction-to-ambient calculation. Narrow connections within a polygon
can still limit heat flow. The checker requires local front-track connections
to at least four vias per driver, and one for Q5; a remote connection through
the ground plane alone cannot satisfy this check.

No vias or soldered parts were added. The existing six soldered-land vias at
U1, C32 and U21 still require filled/capped processing and stencil review.
In1 remains the ground reference; USB copper and its reference checks pass.

## Resistance screening

`verify_high_current_layout.py` finds a path using KiCad's direct copper contacts
for each of 27 source/destination pairs. It counts the full length of every
traversed track and a full barrel for every traversed via. It gives no credit
for parallel tracks/vias. Mid-track contacts can therefore overstate the metal
length charged to a path. This is a trace/barrel screening estimate, not a
complete circuit resistance or field simulation.

The model assumes copper at 80°C, resistivity 0.01724 ohm mm²/m at 20°C with
0.00393/°C temperature coefficient, 0.035 mm outer copper, 0.030 mm inner copper,
1.578 mm barrel length and 0.020 mm hole plating. Saved stack dimensions are
checked; actual finished copper/plating still need manufacturer confirmation.
Pads, solder, connectors, cable, silicon, ground-plane resistance, inductance
and temperature rise are excluded. The 80°C scenario is not a predicted or
approved operating temperature.

| Path group | Screened resistance, mΩ | Project regression ceiling, mΩ |
| --- | ---: | ---: |
| U12 output to U13 input | 36.196 | 50 |
| U13 output to button VM | 48.131–66.499 | 85 |
| U13 output to all three wheel VM pins | 26.761–27.675 | 40 |
| Each button output to its connector | 7.501–15.841 | 25 |
| Each of six wheel phase pins to J5 | 28.380–41.218 | 55 |
| U13 output to each brake resistor | 47.302–72.693 | 100 |
| Q5 drain to each brake resistor | 12.184–47.116 | 65 |

These ceilings protect the reviewed routes against regressions. They are not
datasheet limits or ampacity ratings. For scale, applying 2 A to the entire
U12-output-to-U13-input path gives about 72 mV of modeled drop. Applying 2 A
through that path and the complete longest button supply route gives about
205 mV. The latter deliberately puts the full current through a branch that
normally shares load with other branches. It still excludes the losses listed
above, so measure the voltage at each driver's VM/GND pads under combined load.

At the provisional 0.333 A button trip setting, the two left output routes
contribute about 9.8 mV together. This does not include driver RDS(on), wiring
or the winding. Main-feed resistance does not currently justify a major reroute;
low-supply-voltage margin and heating remain unqualified.

The 2.02 A nominal U13 fault threshold is not an actuator operating allocation.
The [source ceilings](../../docs/power.md) apply to total USB input, including
logic and optical startup. Motor phase current and coil recirculation current
are not interchangeable with average USB or ACT bus current. Measure both and
use a source-aware combined power budget before enabling simultaneous effects.

## Corrected capacitor inventory

The board has eleven 10 µF capacitors directly across ACT_5V/GND:
C8/C11/C14, C37–C40, C44/C45 and C68/C69. Seven 100 nF bypasses are
C7/C10/C13/C41/C42/C43/C65. The nominal total is **110.7 µF**. The earlier
80 µF wheel-review figure omitted the three button-driver bulk capacitors;
the older 70 µF power overview also predates the wheel/brake additions.

At the nominal 0.2 V/ms ramp, capacitor-only inrush is **22.14 mA**. R69's
1 kΩ bleed gives a nominal **110.7 ms** time constant. Neither calculation
includes active loads or secondary-rail charging. The checker guards the
inventory and values, and records these estimates alongside the PCB hash.
At least 47 µF effective storage remains a bench requirement; nameplate values
do not establish capacitance under bias, tolerance and temperature.

## Brake and combined-load work still required

Q5's source still has one short local ground-via connection, now augmented by
the two local ground pours. Its small area is not evidence of a particular
power rating. Use the [AO3400A test conditions](https://www.aosmd.com/res/data_sheets/AO3400A.pdf)
when assessing RDS(on), transient switching and SOA; the datasheet thermal
fixture does not represent this board or its enclosure.

The brake placement is unchanged: BRAKE_GATE has 84.528 mm total trace length,
BRAKE_OUT 32.269 mm and BRAKE_REF 18.743 mm. These are whole-net lengths,
including branches. The gate and reference paths still require a transient/
pickup review and may need relocation or rerouting. The added ground copper
does not establish the 10 µs response target or quiet reference behavior.

Use these measurements to close the actuator acceptance gates:

1. With commands disabled, capture U13 soft-start, input current and the voltage
   directly at each driver. Probe PWR_5V at TP11, ACT_5V at TP12, and enable at
   TP13; use local capacitor/driver pads and short ground connections for fast
   ripple measurements. TP34 is a remote ACT pad and does not substitute for
   measuring local VM droop. Check at least 4.7 V before the first effect and
   confirm shutdown before a driver is operated below its minimum supply.
2. Characterize one coil in both polarities at J2, then J3/J4: winding R/L,
   current rise/decay, force, pulse energy and temperature versus duty cycle.
   Retain the provisional 0.333 A nominal trip setting until these results
   justify a change. Compare current telemetry with an external current probe.
3. Characterize the wheel initially at or below 0.5 A phase current. Measure
   phase current, ACT bus current, input demand and VM droop separately. Add
   button loads one at a time while retaining the documented source ceilings.
   Record driver, winding, resistor, board and enclosure temperatures through
   thermal settling; peak-current arithmetic does not qualify sustained use.
4. Measure brake reference at TP35, comparator output at TP36, and Q5 gate
   **relative to its source**, together with local ACT voltage. Exercise MCU
   held in reset, disabled U13, unplug, startup from a discharged rail, repeated
   detents, continuous hand rotation and abrupt stops. Confirm that brake
   operation does not depend on firmware or USB absorbing returned energy.
5. Retain the unverified envelope of 0.4 A peak returned rail current, 0.5 W
   average returned power, at least 47 µF effective ACT storage, response
   within 10 µs and peak ACT below 6.5 V. Compare integrated returned energy
   with resistor dissipation and capacitor energy change. Reduce the test
   envelope or revise the circuit/layout if a target is not met. The four
   resistors dissipate about 3.06 W while on at 6 V; their summed 8 W nameplate
   rating does not permit 8 W continuously inside the mouse.

## Verification

The saved PCB has **0 physical DRC violations, 0 schematic-parity issues and
204 native unrouted connections**. No rule or exclusion was added. The remaining
unrouted connections are outside this completed copper subset. All six native
copper checkers and 45 test methods pass: buck 3, input 11, actuator 10,
distribution 3, USB 10 and high-current 8. The new tests include four power-open
subcases, a still-connected narrowed phase, missing/empty ground copper,
thermal-relief substitution, a changed bulk capacitor and changed copper
thickness. Power, wheel and encoder static checks also pass. Front/back exports
were visually reviewed.

Run the new checker and tests with KiCad's Python:

```powershell
$kp = "$env:LOCALAPPDATA/Programs/KiCad/10.0/bin/python.exe"
& $kp hardware/kicad/verify_high_current_layout.py
& $kp hardware/kicad/test_high_current_layout_checks.py
```

`build/pcb-review/high-current-layout-checks.json` records paths, selected copper
UUIDs, area/inventory checks, assumptions and PCB SHA-256. The checked board hash
is `e4d6157cb696f7c79b6a43efbde1e4189829a9c7c2fa59417a945968d2509088`.
Run the other copper checks and native DRC after further routing or zone edits.
This pass does not release a fabrication or assembly package.
