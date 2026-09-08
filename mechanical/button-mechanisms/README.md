# Button mechanisms

Selected direction as of 2026-09-08: three elastic paddles with custom
moving-magnet electromagnetic actuators. This follows the supplied analysis's
second revision: the paddle/flexure provides passive return, while a stationary
wound coil modifies click feel. No dimensioned CAD or measured actuator exists yet.

## Mechanism

Each left, middle and right button assembly contains:

- A deliberately designed elastic paddle/flexure, attachment points and hard stops.
- A moving sensing magnet and a fixed TMAG5253 position sensor.
- A separate moving actuator magnet and a stationary wound-copper coil/former.
- A DRV8231A bidirectional driver on the PCB, with IPROPI feedback to ADS7038.
- Optional soft-steel back iron/yoke to compare during magnetic-circuit trials.

The flexure supplies baseline resistance and returns the paddle without actuator
power. The coil adds a transient force peak, drop, brief assistance pulse, or
release click. End the effect with zero commanded coil current, including when a
finger continues to hold the button. Resting electronics still consume power.

Treat the flexure as a functional spring, not an arbitrary thin area of the
cosmetic shell. Prototype a long compliant section with controlled strain and
replaceable mounting. PA12/nylon is a material candidate from the analysis;
material, print process/orientation, stiffness, creep and fatigue life require
tests. Stops must prevent overtravel, coil/magnet collision and excessive strain.
For middle click, define the wheel assembly's load path and preserve encoder
alignment through the full press; do not assume the left/right paddle geometry
transfers directly.

## Initial prototype targets

These are exploration targets from the revised analysis, not fabrication
dimensions, acceptance measurements, or guaranteed force/current performance.

| Property | Starting target / unresolved detail |
| --- | --- |
| Coil outside diameter | Approximately 6-8 mm |
| Coil height | Approximately 2-4 mm |
| Coil inside diameter, wire gauge and turns | TBD from winding fit, resistance, inductance and force measurements |
| Actuator magnet | Approximately diameter 4-5 mm x thickness 1.5-2 mm, N52 candidate |
| Actuator gap and yoke | TBD; maintain clearance over full travel and tolerances |
| Sensing magnet and Hall gap | Separate geometry; choose to avoid saturation and resolve full paddle travel |
| Fingertip paddle travel | Approximately 0.5-0.8 mm; actuator travel depends on leverage |
| Passive paddle resistance | Approximately 20-40 gf (0.20-0.39 N) at a defined press position |
| Peak electromagnetic force | Approximately 0.2-0.4 N at the actuator; measure resulting fingertip force |
| Effect duration | A few milliseconds initially; exact pulse/duty/repeat limits TBD |
| Coil current between effects | Zero commanded current; passive return does not require holding current |

The earlier 8-10 mm coil, AWG 36-38, 100-200 turns, 4-8 ohms and 0.5-1 A
suggestions do not define a proven winding for this smaller geometry. Select a
buildable winding after testing on the available 5 V rail. Likewise, example
positive/negative current waveforms are ideas for testing, not firmware defaults.

Do not assume equal and opposite total force when reversing current. Map force
versus position and both current polarities, including zero-current attraction
to optional steel. A yoke must not latch the paddle down or defeat passive return.
Verify current reversal time as well as static force before tuning snap effects.

## One-button experiment before layout

1. Build a flexure/stop fixture with adjustable coil and sensor positions. Measure
   the unpowered fingertip force/travel curve and return, including sustained hold.
2. Wind one coil and record actual dimensions, turns, wire, resistance and
   inductance. Record the magnet grade, dimensions, orientation and working gap.
3. Use a current-limited supply and DRV8231A to sweep bounded current in both
   directions across travel. Measure actuator/fingertip force, current rise/decay,
   IPROPI readings, supply demand and coil/driver temperature.
4. Hold the paddle at known positions while driving its coil, nearby button coils
   and the wheel. Measure Hall and wheel-angle errors, saturation, drift and
   false input thresholds. Separate magnets do not eliminate magnetic crosstalk.
5. Tune bounded press/release pulses. Measure response latency including driver
   wake time; verify repeated clicks and a held button cannot sustain an effect.
6. Test reset, power removal, stale sensing and control timeout. Confirm passive
   return and mechanical clearance with every tested yoke configuration.
7. Cycle and hold-test the flexure using the intended print process. Record
   stiffness drift, permanent set and wear; set a lifetime target before claiming
   durability. Repeat middle-click tests with the actual wheel load path.

Exit: a measured winding/force map, a reproducible mechanical drawing and BOM,
defined pulse/current/temperature limits, and demonstrated passive return and
sensor stability. Freeze PCB coil connectors and magnetic placement only after
these results are reviewed. Power and interface details live in
[power](../../docs/power.md) and [interfaces](../../docs/interfaces.md).
