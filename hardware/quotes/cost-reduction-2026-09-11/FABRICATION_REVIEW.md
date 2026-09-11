# Fabrication cost review

**Pricing interpretation correction, verified in the calculator:** JLCPCB's [published via capability rules](https://jlcpcb.com/capabilities/pcb-capabilities)
state that 0.20/0.25 mm holes incur extra cost when the via diameter is below
0.45 mm. The current 0.20 mm holes have 0.45 mm pads. The earlier quotes used
the premium 0.20 mm / (0.30/0.35 mm) calculator option, so its necessity has
not been established for these boards. The live calculator's via-help text
explicitly confirms that multilayer boards with 0.20 mm holes and pads at
least 0.45 mm have no extra small-via charge. Independent corrected Main/Wheel
jobs now use the standard tier and explicitly state the actual drill/pad
dimensions in their PCB remarks; no holes are enlarged. Filled/capped via charges
are a separate issue and remain subject to manufacturing review. The geometry
screen below is valid for the proposed enlargement, but does not establish
that enlargement is necessary to avoid the premium pricing tier.

Read-only screening of the exact boards used by the 2026-09-11 quote. The
script verifies their SHA-256 hashes against the export snapshot and leaves
CAD unchanged. [Machine-readable findings](fabrication-audit.json) include
the UUID and position of every small via screened.

| Finding | Main | Wheel | Encoder |
| --- | ---: | ---: | ---: |
| Total vias | 875 | 196 | 17 |
| 0.45 mm diameter / 0.20 mm drill | 554 | 56 | 0 |
| 0.60 mm diameter / 0.30 mm drill | 321 | 140 | 17 |
| Drill overlaps any SMD copper | 102 | 36 | 0 |
| Drill overlaps a populated component land | 90 | 36 | 0 |
| Small vias whose enlargement encroaches on nearby copper | 391 | 24 | 0 |

The proposed enlargement is **0.55 mm diameter / 0.30 mm drill**, preserving
the project's minimum 0.125 mm annular ring. Changing only the drill of a
0.45 mm via would leave a 0.075 mm ring and violate that rule. The screen
uses 0.15 mm clearance to different-net pads, tracks and existing vias on
every enabled copper layer. It compares current and proposed sizes. It does
not test simultaneous enlargement of adjacent vias, same-net drill spacing,
board edges, keepouts, zone refill or the complete native rule system.
The 163 Main and 32 Wheel vias without a screened obstacle are candidates
for further review, not approved edits.

If deliberately moving to an all-0.30-mm-drill specification, **every** smaller
via must change. Enlarging only the easy vias does not establish any saving.
This is not established as necessary for lower pricing; see the correction
above. Main requires extensive local rerouting; Wheel is the smaller
possible pilot, but its power, phase-current and brake paths still need all
existing electrical checks after edits. A six-layer price study found only
EUR 29.94 additional fabrication savings across five Main/Wheel boards from
the larger-drill option. That is not a strong reason to disrupt the present
routed prototype on its own.

Filled/capped vias also cannot simply be removed from the quote. Main has
90 vias that overlap populated component lands. Another 12 overlap only
DNP or BOM-excluded lands, including test pads; those are not automatically
equivalent solder-wicking risks. Wheel has 36 component-land overlaps,
including 19 pad hits at U21 and seven at U23. Moving these vias outside
lands would need package-specific escape, return and thermal review.
Do not sacrifice exposed-pad thermal paths or short decoupling returns just
to remove this process. Final solder-mask/paste and fabricator review remain
required even when a drill does not intersect a land in this screening.

The six-layer half-ounce stack remains a separate redesign candidate, with
EUR 65.51 measured fabrication savings for five Main/Wheel boards before
delivery. Its copper and dielectric dimensions differ: USB impedance,
reference paths, actuator resistance and heat spreading must be redesigned
and validated. No current Gerber archive represents that alternative.

## Breakaway-panel readiness

The quoted jobs are three separate designs. They are **not** a single PCB
that can be cut into three modules. The 147 x 135 mm nesting study remains
planning geometry. A production panel needs routed slots and breakaway
tabs, edge rails, fiducials/tooling, connector clearance, assembly access,
unique combined BOM/CPL references and a depaneling method. Functional
connections must use cables, with no functional copper across breakaway tabs.

Do not construct that panel until the [mechanical interfaces](../../modular/MECHANICAL_INTERFACES.md)
are stable. The minimum next mechanical deliverables are a dimensioned
baseplate/mounting drawing, wheel motor/shaft/bearing and encoder support,
optical lens/base/feet stack, connector access and cable bends, and provisional
paddle/coil/Hall envelopes. Final ergonomic shell surfaces can follow later.
The encoder must also migrate from two layers to the chosen common stack
before inclusion. Panelization might reduce repeated assembly overhead, but
larger area, handling and different-design fees can offset that benefit; it
needs an actual quote after those deliverables exist.

Run the screening with KiCad 10 Python:

```powershell
& 'C:/Users/cartm/AppData/Local/Programs/KiCad/10.0/bin/python.exe' hardware/quotes/audit_fabrication_cost.py
```
