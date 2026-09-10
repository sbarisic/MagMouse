# Analog routing and review

2026-09-10, KiCad 10.0.6. The motherboard's analog connections are routed,
including the three previously open Hall outputs. **The analog electrical
review remains open.** The new audit distinguishes continuity/local-filter
checks from unresolved reference and switching-proximity findings.

## Changes

- Repositioned/reoriented C59-C61 so all three ADC2 filter nets stay on F.Cu,
  removing six signal vias. R102-R104 and the 330-ohm/22-pF values are unchanged.
  Local ground returns were reconnected. Saved In1 fill now covers the complete
  copper shadow of all three filtered input nets, including two small void
  overlaps corrected during this pass.
- Routed HALL_L/M/R at the existing sensor and ADC positions. These placements
  remain provisional for mechanical development. Two HALL_EN sections were
  rerouted to free the right sensor output and ADC1 input escapes.
- Rerouted button IPROPI, middle-button VREF and buffered input-current
  telemetry. Right-button current sensing and telemetry take shorter routes;
  some other branches are longer to accommodate input escapes and switching
  copper. Connectivity alone does not establish their noise performance.
- Connected the previously open C36 ground return for ACT voltage telemetry.
- Extended U4's front ground zone by 0.5 mm to retain its reviewed spreading
  area after the new analog escapes. All high-current resistance and ground-area
  checks remain satisfied. Sensor, driver, connector and ADC positions are
  unchanged; the schematic, BOM, outline and mechanical reservations are unchanged.

The [ADS7038 layout guidance](https://www.ti.com/lit/ds/symlink/ads7038.pdf)
calls for analog/digital separation, close bypassing and low-impedance ground
connections; AVDD also supplies the ADC reference. The
[DRV8316 datasheet](https://www.ti.com/lit/ds/symlink/drv8316.pdf) recommends RC
filtering at SOx. The [DRV8231A](https://www.ti.com/lit/ds/symlink/drv8231a.pdf)
uses its IPROPI resistor to generate the sensed voltage and set current
regulation. Routing and sampling changes must therefore be checked for effects
on both measurement and regulation.

## Saved geometry

Lengths below sum every segment on a net, including branches; they are not
end-to-end flight times or extracted parasitic models.

| Net | Before, mm / signal vias | After, mm / signal vias |
| --- | ---: | ---: |
| WHEEL_I_A | 7.71 / 2 | 7.816 / 0 |
| WHEEL_I_B | 11.69 / 2 | 7.454 / 0 |
| WHEEL_I_C | 6.48 / 2 | 5.343 / 0 |
| BTN_L_ISENSE | 46.19 / 4 | 49.434 / 4 |
| BTN_M_ISENSE | 47.04 / 3 | 50.531 / 4 |
| BTN_R_ISENSE | 134.43 / 7 | 81.685 / 8 |
| BTN_M_VREF | 27.09 / 5 | 38.097 / 7 |
| USB_IMON_ADC | 41.51 / 4 | 18.065 / 2 |
| USB_IMON_BUF | 108.73 / 0 | 62.166 / 3 |
| HALL_L | Unrouted | 58.728 / 2 |
| HALL_M | Unrouted | 23.990 / 2 |
| HALL_R | Unrouted | 121.858 / 6 |

The upstream SOA/SOB/SOC routes remain 22.161/24.682/32.532 mm, with two vias
each. The high-current placement constrains these routes; their remaining
proximity findings must be resolved or supported by appropriate analysis and
measurements before routing freeze. The long right Hall route is particularly
likely to change with the paddle/magnet mechanics.

## Open review findings

The audit currently reports **46 analog/aggressor net pairs within the 0.5 mm
screening distance, 10 front-reference shadow findings and three nets longer
than 60 mm**. These counts include fine-pitch device launches; they are review
flags, not 59 independently demonstrated electrical failures. They are not
waived by the passing continuity check.

Prioritize these findings before treating the analog layout as reviewed:

1. SOA/SOB/SOC cross phase copper in projection on In2/B. In1 is above both
   layers and does not separate those conductors. SOA also approaches phase A
   on B.Cu to about 0.168 mm edge clearance. Review the phase/sense placement
   together; preserve the current-path checks during any reroute. A negative
   projected gap in the JSON means overlap on different layers, not a DRC short.
2. The right Hall route has approximately 0.728 mm² of front-track shadow
   outside saved In1 ground after excluding its own via transitions. Its length
   is 121.858 mm. Revisit its route and sensor location with the mechanical
   model; do not freeze this as an accepted low-noise sensing path.
3. Smaller front-shadow findings remain on HALL_L, BTN_L_ISENSE, USB_IMON_ADC,
   USB_IMON_BUF, WHEEL_SOA, ADC_DECAP, both outer-button VREF nets and BRAKE_SENSE.
   Inspect the reported segments/nearby antipads during the whole-board return
   review. ADC2's three filtered nets have zero missing shadow under the traces.
4. Review IPROPI/VREF local resistor placement and the middle reference route.
   The new middle VREF route is longer and uses more vias. Qualify ADC channel
   settling, ground offsets and switching pickup rather than inferring accuracy
   from pad connectivity or the nominal current-trip formula.
5. Complete ADC reference/supply distribution, remaining bypass and spare-input
   ties during the board-wide power pass. Then check SPI3 and shared SPI return
   paths, including ADC sampling disturbance. The reference-shadow screen does
   not establish internal/back-layer return geometry or ground voltage drop.

The [roadmap](../../docs/roadmap.md) now records the requested sequence through
board-wide power, SPI3/SPI2, optical review, return paths, thermal review,
mechanical integration, manufacturing/test access and minimal firmware bring-up.
The whole-board review must precede final routing freeze. Keep Hall and button
interfaces provisional until paddle, magnet, wheel and mounting geometry exists.

## Verification and review gate

Native DRC reports **zero physical violations and zero schematic-parity issues**.
The motherboard has **200 native unrouted connections**, down from 204. All
seven copper checkers pass their connectivity/local-geometry requirements;
the analog checker still reports the findings above. USB continuity, geometry,
ESD grounding and saved In1 reference checks pass. All 51 regression test methods
pass, including six analog methods with four open-net subcases. The analog
tests also exercise a filter layer change, removed ground plane, disconnected
monitor-capacitor return and the unresolved-review gate.

Run with KiCad's Python:

```powershell
$kp = "$env:LOCALAPPDATA/Programs/KiCad/10.0/bin/python.exe"
& $kp hardware/kicad/verify_analog_layout.py
& $kp hardware/kicad/test_analog_layout_checks.py
# This stricter command currently fails because the review findings remain open:
& $kp hardware/kicad/verify_analog_layout.py --require-reviewed
```

`build/pcb-review/analog-layout-checks.json` records all 22 analog nets, ground
checks, front-shadow areas, proximity pairs, PCB item UUIDs, coordinates and
the board SHA-256. The checker does not refill zones before inspection. Its
shadow check covers the actual front-track width, without a reference margin,
and excludes a 0.7 mm radius around each net's own transition vias. Proximity
checks compare tracks/vias, not component pad shapes or electric/magnetic fields;
native DRC remains necessary. Use `--require-reviewed` for the analog review
gate; a default exit status of zero does not mean the findings are closed.

Checked board SHA-256:
`40d3d6096ec49ae80b579dd8a774457422d93cd852782c9f8d3958fc822056c1`.
This is a routing/review draft, not a fabrication or assembly release.
