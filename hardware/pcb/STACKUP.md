# Prototype stackup and USB geometry

Selected 2026-09-09 using the live
[JLCPCB impedance calculator](https://jlcpcb.com/pcb-impedance-calculator).
Saved inputs and results are in [stackup-calculation.json](stackup-calculation.json).
This is a design selection, not an accepted manufacturing quote.

Use **JLC041611-2116**, four layers, nominal 1.6 mm order thickness,
**1 oz outer and 1 oz inner copper**. The calculator labels this option
1.58 mm finished thickness, ±10%. The 1 oz inner-copper option matters:
the similarly named half-ounce stackup has different dielectric dimensions.

| Layer | Thickness (mm) | Use |
| --- | --- | --- |
| F.Cu | 0.035 | Components and signals, including USB |
| 2116 RC54% prepreg | 0.109 | Dielectric |
| In1.Cu | 0.030 | GND reference |
| FR4 core | 1.230 | Dielectric; calculator labels core plus copper 1.3 mm 1/1 oz |
| In2.Cu | 0.030 | Power and slower signals |
| 2116 RC54% prepreg | 0.109 | Dielectric |
| B.Cu | 0.035 | Signals and test pads |

The copper/dielectric sum is **1.578 mm**, now recorded in the KiCad board
thickness and explicit stackup. KiCad mask thickness entries of 0.010 mm are
editor placeholders; they are not supplier-confirmed mask data. No supplier
dielectric constant or loss tangent was provided by the displayed calculation.
KiCad writes default epsilon_r = 4.5 and loss_tangent = 0.02 when saving;
these are unverified placeholders, not manufacturer evidence.
ENIG is recorded as the prototype finish choice; manufacturing approval remains open.
The earlier monolithic USB review identified six 0.60/0.30 mm filled,
copper-capped vias: four in U21's exposed pad, one in U1's ESD ground land
and one in C32's supply land. That is a historical subset, not the current
modular-board inventory. The [current quote via maps](../quotes/2026-09-11/MANUFACTURING_NOTES.md)
identify 102 Main and 36 Wheel vias whose drill disks intersect SMD copper.
The [cost audit](../quotes/cost-reduction-2026-09-11/fabrication-audit.json)
distinguishes 90 Main component-land overlaps from 12 overlaps limited to
DNP/BOM-excluded pads; all 36 Wheel overlaps involve populated components.
Obtain fabricator/assembler acceptance of the fill/cap process and affected
land/paste geometry. See [the historical USB layout review](USB_LAYOUT.md).

## USB result

Calculator inputs: 90 ohms, **Differential Pair (Non coplanar)**, with solder
mask, signal layer L1, reference L2, spacing input 0.15 mm, no top reference.
The output is **0.1466 mm trace width and 0.1501 mm pair gap**. The saved USB
netclass applies those dimensions to USB_DP/DM and MCU_USB_DP/DM.
The calculator's 0.5% setting is solver tolerance, not fabrication tolerance.

The [USB route and copper audits](USB_LAYOUT.md) now implement those dimensions
on F.Cu, with no signal vias and continuous saved In1 ground beneath the
traces and their 0.327 mm reference margin. Connector/pad fanouts and nearby
front copper still require signal-integrity review against the non-coplanar
model. Request this exact stackup and 90-ohm controlled impedance in the
quote; confirm impedance tolerance, coupon/test provision, finished copper
and CAM adjustments before accepting fabrication data.

The enclosure and optical height must accommodate actual laminate thickness
and tolerance. The numerical CAD thickness change is 0.022 mm from the former
1.6 mm placeholder; it does not freeze the lens/feet/mechanical stack.
