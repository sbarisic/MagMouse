# Circuit correction review — 2026-11-05

This revision addresses optical isolation, motor undervoltage handling and
six capacitor-placement findings. The active independent schematics are the
electrical source. The combined migration schematic remains historical.
Firmware implementation, a new supplier quote and ordering are outside scope.
The before measurements refer to Git revision `7674089ca8481ceb03476ed3986a8816dfb864b0`
(Windows CRLF checkout hashes). Saved PCB files are authoritative;
`circuit_fixes.py` is a one-time migration, not a regeneration command for the
completed routing. Compact before measurements remain here.

## Circuit changes

Lower U37 now uses **Nexperia 74LVC125APW,118**. The switched-domain audit also
replaces Lower U25/U29 and Wheel U24/U26 with that exact manufacturer and part.
The TSSOP-14 land pattern and all connections are unchanged. Nexperia explicitly
specifies powered-off isolation for inputs and outputs through Ioff; another
manufacturer's similarly named 74LVC125 is not an approved substitution.
See [Nexperia's datasheet](https://assets.nexperia.com/documents/data-sheet/74LVC125A.pdf).

| Crossing | Decision and power-off contract |
| --- | --- |
| Optical SPI/reset, U37 | Nexperia Ioff buffers; retain the existing reset, chip-select, shutdown and initialization sequence |
| Wheel/host SPI, U25/U29/U24/U26 | Same Nexperia part; a live host or separately powered peripheral must not back-power an off buffer supply |
| Optical host return, U39 | Retain TI SN74LVC1G125; its [datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc1g125.pdf) explicitly supports Ioff |
| RGB data, U34 | Retain SN74LV1T34 under the existing data-low-before-power-off contract. Its [datasheet](https://www.ti.com/lit/ds/symlink/sn74lv1t34.pdf) allows input voltage independent of VCC, but does not establish arbitrary-high-input powered-off leakage with Ioff. Do not extend this to an uncontrolled live-high crossing |

Upper R36–R38 are 10 kOhm each and R39 is 11 kOhm, all 1% 1206. U13's
nominal rail-start threshold is 4.473 V; nominal falling threshold is 4.063 V.
The independent resistor, EN leakage and device threshold corners give
**4.343–4.629 V rising**, before D3 leakage. Equations and corner results are
in [verification.json](verification.json). Source: [TPS25947 datasheet](https://www.ti.com/lit/ds/symlink/tps25947.pdf).

D3 reverse leakage flows from ACT_DRIVE_EN into the divider while enabled,
so it lowers the start threshold rather than raising its upper corner. The
[BAT54 datasheet](https://www.diodes.com/datasheet/download/BAT54.pdf) specifies
2 uA maximum reverse leakage at 25 C and 25 V; that would reduce the threshold
by up to 60.6 mV with the high resistor corner. No guaranteed full-temperature
leakage ceiling is assumed. The local supervisor independently qualifies drive.

Wheel U40 is **TPS3808G01DBVR**, powered from host +3V3. R147/R148 are
105 kOhm / 10 kOhm Vishay TNPW1206 resistors, 0.1%, 25 ppm/K. C102 is
1 nF, C103 is 100 nF, R149 is a 10 kOhm reset-output pull-up. MR receives
ACT_DRIVE_EN; CT is explicitly unconnected. U41 is **SN74LVC1G08DBVR**, with
C104 100 nF and R150 100 kOhm output pulldown. The connections implement:

```
WHEEL_RUN_REQUESTED = WHEEL_RUN_REQ AND ACT_DRIVE_EN
WHEEL_RUN_EN = WHEEL_RUN_REQUESTED AND WHEEL_VM_OK
```

WHEEL_RUN_EN feeds the existing PWM gates, INLA/B/C and Q4. U13 retains its
original ACT_DRIVE_EN control. Neither the supervisor nor its output gates the
rail enable. The current limits, reverse blocking and autonomous regenerative
brake retain their circuits. No connector pin or MCU GPIO is added.

Sources: [TPS3808](https://www.ti.com/lit/ds/symlink/tps3808.pdf),
[SN74LVC1G08](https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf),
[precision resistor specification](https://www.vishay.com/docs/28758/tnpw_e3.pdf).

## Voltage and timing limits

The nominal falling threshold is **4.6575 V**. Conservative independent
corners include supervisor threshold accuracy, resistor tolerance and TCR,
±25 nA sense leakage and maximum 3% hysteresis:

| Condition | Falling range | Maximum release threshold |
| --- | --- | --- |
| 25 C | 4.553–4.762 V | 4.905 V |
| Full -40 to +125 C screening envelope | 4.533–4.784 V | 4.927 V |

The divider/sense-capacitor nominal time constant is 9.13 us. CT open gives
12–28 ms release delay after stable voltage and valid manual reset. Recovery
also requires every existing request and heartbeat permission. Low local VM
does not itself reset the MCU or remove logic power. At a marginal supply,
haptics may remain unavailable while mouse operation continues.

The static minimum threshold exceeds DRV8316's 4.5 V operating minimum.
It does **not** guarantee that an abruptly collapsing rail stays above 4.5 V
until drive stops: RC filtering, supervisor propagation, gate delay and driver
response all take time. The behavioral sweep uses 20 us and 100 us assertion
delay cases as screening assumptions, not a guaranteed timing bound. Bench
measurements must establish the actual worst case. Resistor aging and effective
capacitance are also qualification items, not included as invented guarantees.

## Verification and release status

The independent checker records pin parity, approved component changes,
all five harness pairings, component gaps, via holes and the unchanged Encoder
hash in [verification.json](verification.json). It evaluates 128 steady
interlock combinations, 60 transient cases and 16 SPI-selection/power contract
cases. These are analytical and behavioral checks, not firmware execution,
transistor-level IC simulation or hardware acceptance.

All four individual boards pass fresh native ERC, DRC and schematic-to-PCB
parity with zero findings and zero unconnected items under the saved rules.
The refreshed four-board manufacturing panel also passes native DRC with zero
findings and zero unconnected items. Its copied pads, traces, drills and filled
zone copper are checked against the individual boards.
No new ignored categories or exclusions were added. All 1,028 schematic pins
and five harness pairs are checked. The Main outlines, Wheel profile, optical
aperture, antenna keepouts, connector datums and original USB copper are
unchanged. Encoder's PCB is byte-identical to the starting revision.

| Reviewed connection | Before pad centres | After pad centres | After layer / vias |
| --- | ---: | ---: | --- |
| Lower U2.2–C1.1 | 9.55 mm | 4.05 mm | F.Cu / 0 |
| Lower U35.5–C86.1 | 10.33 mm | 4.45 mm | F.Cu / 0 |
| Wheel U21.6–C47.2 | 7.66 mm | 3.45 mm | F.Cu / 0 |
| Wheel U21.7–C47.1 | 7.25 mm | 3.45 mm | F.Cu / 0 |
| Wheel U21.25–C48.1 | 9.56 mm | 3.55 mm | F.Cu / 0 |
| Wheel U23.8–C58.1 | 7.06 mm | 3.35 mm | F.Cu / 0 |

All six <=5 mm placement targets are met. Measured body-and-land gaps are
2.003 mm Lower, 2.025 mm Upper, 2.010 mm Wheel and 2.500 mm Encoder. New
passives are 1206; existing footprints are preserved. All vias have 0.30 mm
drills, and no via holes intersect SMD lands. Both GND layers are filled;
disturbed regions are stitched. TP36 moved to (20,43) mm to clear C42.
The per-connection route objects, layers and before/after measurements are in
[verification.json](verification.json). Contact-graph object lengths exclude
travel through lands and overlapping copper; they are not exact centreline lengths.

[power-paths.json](power-paths.json) records the current resistance screen.
The subsequent routing rebuild uses fixed-width power trunks and short,
explicit pin escapes. See [the routing review](../routing-review/routing-rebuild.md)
for the comparison against the routing before this rebuild.

Lower J103.3 to U2.2 now screens at 19.65 mOhm (19.65 mV and 19.65 mW at
1 A), down from 27.7 mOhm before the USB placement change. Its minimum
width is the short 0.25 mm IC escape. The input capacitor retains a direct
component-side route with no vias.

Wheel J11.1 to U21.9 now screens at 36.2 mOhm (72.5 mV and 144.9 mW at the
separate 2 A case), versus 18.5 mOhm before this routing rebuild. Its main
trunk is 1.0 mm, with a short 0.25 mm escape at the driver pins. The regular
fixed-width route is not the lowest-resistance version; voltage drop and
thermal behavior remain bench checks. Phase A screens at 19.7 mOhm at
0.5 A (9.9 mV, 4.9 mW). These cases do not authorize exceeding the 2 A total
input budget.

The R147 sense branch joins the local VM feed near (24.04,30.31) mm. It
shares approximately 1.50 mm of pin-escape copper with the driver feed,
rather than sensing at the upstream connector. The whole-object resistance
screen gives 8.35 mV of shared-feed error at 2 A and 125 C, and a screened
minimum static driver trip voltage of 4.524 V. This is not a Kelvin connection
at the IC land. Ground bounce, actual shutdown delay, transient droop and
thermal behavior remain unverified. Measure directly across U21 VM/GND
before treating the static margin as hardware acceptance.

The resistance model assumes 35 um copper and 20 um via plating, omits cable,
harness, connector and semiconductor losses, and is not a field/thermal solver.
Those omissions cannot create a false enable from upstream voltage because
U40 measures the local rail, but they can make haptics unavailable on a weak
supply. The existing current limits, reverse blocking and regenerative brake
circuits retain their connections. Existing supplier quotes do not establish
acceptance of the revised design.

The final [release checks](release-checks.json) tie the native reports, geometric
checks, fabrication archives and all five validated 3D models to these sources.

## Bench acceptance — all UNVERIFIED

1. **SPI back-powering:** power host with optical supply off; exercise clock,
   MOSI, reset and each chip select independently. Measure off-domain rail
   voltage and injected current, including host-off/peripheral-on cases.
   Confirm inactive MISO stays high impedance and other SPI devices work.
2. **Optical transitions:** measure reset/select/data timing during shutdown,
   ramp-up and initialization. Verify the unchanged PMW3360 sequence with
   real optics and the actual firmware; software remains to be implemented.
3. **Local undervoltage:** probe U21 VM/GND, U40 SENSE/RESET, WHEEL_RUN_EN,
   driver inputs and phase outputs. Test startup, slow and abrupt droop,
   repeated crossings, reset, missing heartbeat and supply recovery. Measure
   falling/release thresholds and total shutdown delay across temperature.
4. **Interlocks:** with undervoltage recovered, independently hold run request,
   source permission, sensor permission, reset and heartbeat invalid. Drive
   must remain inhibited. Verify no automatic recovery skips driver setup.
5. **Power integrity:** measure regulator input/output ripple, optical rails,
   charge pump, AVDD and ADC supplies with short probe ground connections.
   Include load steps and simultaneous SPI activity.
6. **Motor transients:** use a current-limited supply first. Exercise current
   limits, hot plug, cable drop, motor stall, back-drive, regeneration and
   disconnect. Record rail extremes, return currents and brake heating.
7. **Copper/assembly:** inspect soldering, capacitor polarity where relevant,
   measured voltage drops and temperature rise at the documented 1 A logic,
   2 A input/actuator and 0.5 A phase screening budgets. Confirm actual via
   plating and effective capacitance; resistance estimates are not ampacity
   certification.
