# Exact stack and file-layer mapping

Order: nominal 1.6 mm, four layers, JLC041611-2116, 1 oz outer/inner, ENIG.
The CAD model uses the following thicknesses; total including both masks is 1.578 mm.
Keep the 0.109 mm outer dielectrics. No stack substitution is authorized.
The source model uses 0.030 mm inner copper for the selected nominal 1 oz construction;
JLC must confirm the construction against this table. Do not silently change it to 0.5 oz.

| Layer/material | Thickness (mm) |
|---|---:|
| Top Solder Mask | 0.01 |
| F.Cu | 0.035 |
| F.Cu/In1.Cu | 0.109 |
| In1.Cu | 0.03 |
| In1.Cu/In2.Cu | 1.23 |
| In2.Cu | 0.03 |
| In2.Cu/B.Cu | 0.109 |
| B.Cu | 0.035 |
| Bottom Solder Mask | 0.01 |

| File | Function |
|---|---|
| Panel-F_Cu.gtl | Copper,L1,Top |
| Panel-In1_Cu.g1 | Copper,L2,Inr |
| Panel-In2_Cu.g2 | Copper,L3,Inr |
| Panel-B_Cu.gbl | Copper,L4,Bot |
| Panel-F_Silkscreen.gto | Legend,Top |
| Panel-B_Silkscreen.gbo | Legend,Bot |
| Panel-F_Mask.gts | SolderMask,Top |
| Panel-B_Mask.gbs | SolderMask,Bot |
| Panel-Edge_Cuts.gm1 | Profile |

USB design target: 90 ohm differential, width 0.1466 mm, gap 0.1501 mm, F.Cu over In1 GND.
Paid impedance control/testing: NO. Exported job metadata reflects this economy selection.
Gerber profile centerlines define 151 x 139 mm. The 0.05 mm drawing stroke does not enlarge the board.
Gerber/drill coordinates: X right, negative Y downward; drawings use positive Y downward.
