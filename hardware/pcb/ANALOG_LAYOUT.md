# Analog routing and review

2026-09-10, KiCad 10.0.6. The motherboard's analog connections are routed,
including the three previously open Hall outputs. **The analog electrical
review remains open.** The new audit distinguishes continuity/local-filter
checks from unresolved reference and switching-proximity findings.

### Follow-up: correct saved reference fill

Refilling the unchanged board with its matching KiCad project and custom rules
removes all nine non-Hall front-reference shadow findings. The earlier saved
fill had been produced through scratch-board workflows without the matching
project context. A controlled refill of the original routing reproduces the
correction; no trace, via, footprint, schematic or manufacturing rule was moved
or changed for this follow-up. The high-current and USB checks still pass.
As a control, refilling a projectless copy reproduces the earlier ten shadow
findings, including the original 0.728411 mm² Hall_R gap. This is a project-context
problem in the filling workflow, not a reason to relax the reference checker.

Use `hardware/kicad/refill_pcb_zones.py` for future fills. It requires the
matching `.kicad_pro` and `.kicad_dru`, checks loaded project settings, rejects
pad/track net propagation and preserves the project files. Its tests compare
routing and placement before/after filling and reject a projectless copy.
The saved-copper checker remains read-only and does not refill away defects.

**This does not close the analog review.** After the subsequent analog and
control copper work there are 36 non-mechanical findings: 35 proximity pairs
and one long net. Six Hall findings are separately deferred pending paddle/magnet CAD.
The strict gate still fails on the 36 fixed
findings. Hall opens also still fail; only Hall geometry can be deferred.

ADC2/filter/bypass placement on the back side is under consideration to put
the analog island beside the DRV8316 sense-pin exits. Assembly-side preference
is pending. No back-side placement or trial reroute has been saved to the
motherboard. BRAKE_GATE, BRAKE_OUT and BRAKE_REF now appear together in the
analog report, with the reduced total copper lengths below. Their
transient/placement review remains open; trace length alone
does not establish the autonomous brake response time.

## Follow-up: remove redundant signal copper

Used native direct-contact connectivity to identify redundant branches and
overlapping fragments on 21 fixed analog/brake nets. Removed 1,081 short track
segments, then refilled with the matching project and checked every required
pad connection. No footprints, vias, Hall routes, supply tracks, phase outputs,
coil outputs or brake-drain tracks were moved or removed. Component values,
assembly sides and mechanical reservations are unchanged.

These figures sum all copper on a net. Removing redundant branches reduces
that sum; it does not shorten every pad-to-pad route by the same amount or
prove settling, noise immunity or brake response.

| Net | Before cleanup, mm | Current, mm | Current signal vias |
| --- | ---: | ---: | ---: |
| BRAKE_OUT | 32.269 | 12.336 | 3 |
| BRAKE_GATE | 84.528 | 80.480 | 5 |
| BRAKE_REF | 18.743 | 14.563 | 4 |
| BRAKE_SENSE | 14.757 | 10.638 | 0 |
| BTN_L_VREF | 8.281 | 4.100 | 0 |
| BTN_M_VREF | 38.097 | 28.945 | 7 |
| BTN_R_VREF | 8.323 | 4.000 | 0 |
| BTN_L_ISENSE | 49.434 | 41.737 | 4 |
| BTN_M_ISENSE | 50.531 | 42.689 | 4 |
| BTN_R_ISENSE | 81.685 | 68.421 | 8 |
| USB_IMON_BUF | 62.166 | 47.778 | 3 |
| USB_IMON_ADC | 18.065 | 12.817 | 2 |
| ACT_VMON | 23.652 | 16.343 | 2 |
| WHEEL_SOA / SOB / SOC | 22.161 / 24.682 / 32.532 | 19.380 / 22.027 / 28.630 | 2 each |
| WHEEL_I_A / B / C | 7.816 / 7.454 / 5.343 | 6.006 / 4.703 / 3.758 | 0 each |

The middle-IPROPI/IN2 proximity finding disappears with the redundant branch,
and buffered power telemetry is below the 60 mm length screen. The other
coupling findings remain. In particular, middle VREF still has seven vias,
right IPROPI still exceeds 60 mm, and the long brake gate still needs placement
and transient review. No rejected placement/routing trials were saved.

The checker now enforces explicit whole-net copper ceilings for the cleaned
reference, IPROPI, telemetry and comparator-output nets. These are regression
limits, not electrical acceptance. A fault-injection test adds unwanted brake
output copper without opening the required pad connections and verifies that
the length guard fails.

## Follow-up: separate control signals from wheel sensing

Rerouted BTN_R_IN2 and DRV_INHC around the existing analog copper. Removed
redundant branches on the six button command nets, DRV_INHA/B/C and
WHEEL_PWM_A/B/C. No analog, brake-control, high-current or Hall tracks were
changed in this pass, and every footprint retains its position and assembly side.
Native object comparison confirms that all track changes are on those 12
control nets: 1,546 items removed and 250 added, including a net reduction of
10 signal vias. The saved ground fill was regenerated with the matching project.

Five fixed proximity findings are removed: SOA/SOB/SOC versus BTN_R_IN2,
SOC versus BTN_R_IN1, and SOC versus DRV_INHC. No new fixed findings appear.
Removing a redundant BTN_L_IN2 branch also clears its proximity finding against
HALL_R, without changing Hall copper or accepting its provisional placement.

| Rerouted control | Before, total mm / vias | Current, total mm / vias |
| --- | ---: | ---: |
| BTN_R_IN2 | 165.742 / 10 | 75.027 / 7 |
| DRV_INHC | 55.103 / 8 | 50.038 / 7 |

The before figures include redundant branches. They are not pad-to-pad path
lengths or measured delays. The reroutes have zero missing saved In1 shadow
under their front traces outside their own via transitions. The checker now
guards these two nets' connectivity, front reference coverage, copper length
and via count, and the five cleared 0.5 mm separation screens. Reintroducing
the former IN2 branch beside the SOA via must fail the default check even while
other review findings remain open. These guards do not waive any findings or
establish coupling, PWM timing or current-loop noise performance.

Front-side SOx rerouting and brake-output/reference separation trials did not
produce an acceptable complete route at the present placement. Those trials,
including temporary fault/control removals and placement searches, were not
applied. The SOx/phase crossings and brake reference/gate review remain open;
back-side ADC2 placement still awaits an explicit assembly-side decision.

## Initial analog pass

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

### Initial pass geometry (before the cleanup above)

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

The current upstream SOA/SOB/SOC routes are 19.380/22.027/28.630 mm, with two
vias each. The high-current placement constrains these routes; their remaining
proximity findings must be resolved or supported by appropriate analysis and
measurements before routing freeze. The long right Hall route is particularly
likely to change with the paddle/magnet mechanics.

## Open review findings

The audit currently reports **39 analog/aggressor net pairs within the 0.5 mm
screening distance, one front-reference shadow finding and two nets longer
than 60 mm**. Six of these 42 findings concern provisional Hall geometry;
36 concern fixed routing. Counts include fine-pitch device launches and are
review flags, not independently demonstrated electrical failures. No fixed
proximity or length findings have been waived.

Prioritize these findings before treating the analog layout as reviewed:

1. SOA/SOB/SOC cross phase copper in projection on In2/B. In1 is above both
   layers and does not separate those conductors. SOA also approaches phase A
   on B.Cu to about 0.168 mm edge clearance. Review the phase/sense placement
   together; preserve the current-path checks during any reroute. A negative
   projected gap in the JSON means overlap on different layers, not a DRC short.
2. The right Hall route has approximately 0.178 mm² of front-track shadow
   outside saved In1 ground after excluding its own via transitions. Its length
   is 121.858 mm. Revisit its route and sensor location with the mechanical
   model; do not freeze this as an accepted low-noise sensing path.
3. All fixed front analog traces now have zero missing saved In1 shadow under
   the actual trace width after excluding their own via transitions. This
   resolves the earlier smaller shadow findings, but does not establish a
   wider return corridor, internal/back-layer shielding or ground voltage drop.
4. Review IPROPI/VREF local resistor placement and the middle reference route.
   Middle VREF still has seven vias despite the reduced copper length. Qualify ADC channel
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
ESD grounding and saved In1 reference checks pass. The regression suite includes
fixed-reference coverage, explicit Hall deferral and project-aware refill tests,
alongside the existing analog methods with four open-net subcases. The analog
tests also exercise a filter layer change, removed ground plane, disconnected
monitor-capacitor return and the unresolved-review gate.
All 59 regression test methods pass on the checked board below. The control
pass adds three methods for separation/reference guards, an injected former
IN2 branch and open control routes. Front/back exports were visually reviewed.
Native object comparison confines this pass to the 12 control nets above;
analog and power copper and all footprint placements are unchanged.
The strict analog command still returns failure as intended for the 36 unresolved
non-mechanical findings.

Run with KiCad's Python:

```powershell
$kp = "$env:LOCALAPPDATA/Programs/KiCad/10.0/bin/python.exe"
& $kp hardware/kicad/verify_analog_layout.py
& $kp hardware/kicad/test_analog_layout_checks.py
& $kp hardware/kicad/test_refill_pcb_zones.py
# This stricter command still fails on the non-mechanical findings:
& $kp hardware/kicad/verify_analog_layout.py --require-reviewed
```

`build/pcb-review/analog-layout-checks.json` records all 22 analog nets, ground
checks, front-shadow areas, proximity pairs, PCB item UUIDs, coordinates and
the board SHA-256. The checker does not refill zones before inspection. Its
shadow check covers the actual front-track width, without a reference margin,
and excludes a 0.7 mm radius around each net's own transition vias. Proximity
checks compare tracks/vias, not component pad shapes or electric/magnetic fields;
native DRC remains necessary. Use `--require-reviewed` for the fixed-placement
analog review gate; a default exit status of zero does not mean findings are
closed. `review_complete` also remains false while mechanical findings exist;
`fixed_placement_review_complete` describes the narrower gate. The JSON keeps
all deferred findings and their reasons visible.

Checked board SHA-256:
`c1b17969a4c42e86c7a810a752be42b7251da311aea35c8c01eb3bb8e7c44131`.
This is a routing/review draft, not a fabrication or assembly release.
