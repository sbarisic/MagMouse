# Modular PCB and assembly-panel direction

2026-09-10. Design brief and manufacturing research, not fabrication files.

2026-09-11 update: the independent wheel and shaped main are routed.
**Panelization is on hold until both boards have stable placement and
mechanical interfaces.** The nesting study below remains unchanged; no final
panel, tabs or tooling were created in the layout-completion pass.

The [implementation planning package](../modular/README.md) now contains the
native board envelopes, complete proposed component ownership, logical harness
pin map and a live provisional bare-panel price. Target quantity/destination:
five assembled sets, Croatia 43000. [Separate-job assembly and delivery quotes](../quotes/README.md)
are now available, including a completed two-assembled-set cost comparison.
Independent split schematics and connector/bias additions are now implemented;
see [the current interface review](../modular/INTERFACE_REVIEW.md). The finished
breakaway panel remains open. The [mechanical-interface register](../modular/MECHANICAL_INTERFACES.md)
is the authority for unfrozen mounts, cable paths and optical/button geometry.

## Confirmed dimensions and requested delivery

The user confirmed that the hand-drawn dimensions are millimetres and describe
the PCB, not the shell: 125 mm long, 80 mm maximum width and approximately
44 mm across the narrow end. The shell will be larger. These define the new
shaped motherboard envelope; the curves and the location of the width
transitions are implemented in the active shaped Main PCB. They supersede the
old 60 x 95 mm monolithic board, which is retained only as historical reference.

The requested delivery target is one assembled panel containing detachable
modules, joined by routed gaps and perforated breakaway tabs. The user's
stepped corner cutout illustrates this separation method; it does not fix
the wheel module's final dimensions or location.

## Proposed circuit partition

| Finished board | Circuit ownership |
| --- | --- |
| Shaped main board | USB-C and USB data path, input/actuator power protection, ESP32, optical system, IMU/RGB, three button drivers, ADC1 and button/system sensing |
| Wheel-control board | DRV8316, ADC2 and its reference/filter/bypass network, local motor supply storage, complete autonomous brake, local output-disable logic and required interface buffers |
| Upright encoder board | MA735, local bypass and connector; retain the shaft-facing mechanical role |

Keep SOA/SOB/SOC, their ADC filters and the brake comparator/gate/reference
connections on the wheel-control board. Preserve local high-current loops
and returns. Inter-board links carry power and digital controls; no motor
current-sense output should cross the main-to-wheel harness.

The ESP32 remains the controller in this proposal. The wheel harness must
account for dedicated ADC2 SPI3, SPI2 driver configuration and encoder access,
three PWM commands, enable/run, fault, supplies and ground returns. The
existing encoder connection can be carried through the wheel module, but its
buffer ownership, cable timing and power-domain behavior must be explicitly
redesigned. The module is not an autonomous motor controller without a host.

Provide connectors and cables for every functional board-to-board connection.
Breakaway tabs are mechanical supports: no functional traces or copper planes
cross them. This permits the same connector-based electrical tests before and
after separation. Each finished board needs its own mounting/support and
accessible test points. The prototype assumes fully connected internal cables;
the user accepts possible child-board damage after a disconnect. Disconnect
survival is not a placement/release blocker. Connected reset defaults and
normal power/regeneration behavior remain required.

## Manufacturing panel

Generate a separate assembly panel from the individually maintained KiCad
boards. The panel includes each board once, routed separation gaps, tabs,
tooling rails, holes and fiducials. One fully assembled panel then supplies one
set of mouse electronics. The panel's orientation and nesting need not match
the final in-mouse arrangement.

The 125 x 80 mm envelope applies to the finished shaped motherboard, not to
the shipping/assembly frame. Nest the modules into spare panel space where
useful; do not remove needed motherboard routing or mounting area merely to
reduce panel size. The exact panel dimensions remain open. The current nesting
study reserves 147 x 135 mm, including a provisional 55 x 60 mm wheel envelope.

All units fabricated in one rigid panel must share its layer stack, thickness,
copper and finish. Retain the selected four-layer JLC041611-2116 stack as the
starting point; including the existing two-layer encoder requires a reviewed
four-layer conversion. Keep assembly on one face as the starting arrangement;
panelization does not authorize moving ADC2 to the back of a populated board.

For the stepped or curved cut lines, use routed gaps with perforated tabs.
JLCPCB's current guide recommends 1.6-2 mm typical panel gaps and sets of 5-8
holes at 0.60 mm diameter; use 2 mm as a preliminary gap reservation. Final
tab count, placement, edge clearances and tooling must follow the accepted
panel drawing and component loading. Keep tab-removal areas clear of copper,
components and connector overhangs, with access to support and cut the tabs
after assembly. Do not rely on bending an assembled circuit to separate it.

Prepare panel-coordinate placement data and one consolidated assembly BOM
with unambiguous references. Preserve mapping back to the individual boards.
Check panel and unit Gerbers, drill files, BOM and placement data together.

## Ordering and cost boundary

The target is a customer-supplied panel with three different circuit designs.
JLCPCB explicitly counts separable, different circuits as different designs,
even if traces connect them before separation. A single panel/order therefore
does not imply single-design pricing or lower total cost. Obtain a quote for
the complete mixed-design assembled panel, including delivery with tabs intact,
and compare it with separately assembled boards shipped together. Cable
assemblies and final in-mouse installation are separate from SMT assembly.

Public panel guidance establishes the manufacturing approach, not acceptance
of this unimplemented design. The current board still has 36 fixed analog
review findings and 200 unrouted connections; none are waived by this plan.
After the split, migrate the useful unit checks and add harness/partition
checks rather than carrying over a passing status from the old board.

## Next implementation steps

1. Draw the 125/80/44 mm shaped-board envelope and reserve the optical stack,
   wheel assembly, mounts, connectors and cable bends.
2. Inventory the wheel-owned components and define a complete harness pin map,
   return conductors and normal connected-operation power budget.
3. Extract the wheel circuit and update both schematics and net checks. Place
   the driver/ADC/brake together on the new board before routing its interfaces.
4. Rework main-board placement within the shaped envelope, and convert the
   encoder stackup if all three boards will share the panel.
5. Finish and validate each board and the harness, then generate the routed
   assembly panel and release-matched manufacturing data for supplier review.

## Manufacturer sources checked 2026-09-10

- [Mouse-bite panelization guide](https://jlcpcb.com/blog/mouse-bite-panelization-guide)
- [Different designs in PCB files](https://jlcpcb.com/help/article/different-design-in-your-pcb-files)
- [Ordering a panel](https://jlcpcb.com/help/article/how-do-i-order-a-panel)
- [Assembly rails and fiducials](https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order)

Tab geometry and order/service eligibility must be checked again at release.
