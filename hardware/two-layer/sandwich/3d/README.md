# PCB 3D models

Models exported directly from the routed 1206 / 2 mm spacing revision. `manifest.json`
records the exact PCB source hashes. Exporting does not modify the KiCad files.

| File prefix | Board size |
| --- | --- |
| Lower | 70 × 100 mm, tapered |
| Upper | 70 × 100 mm, tapered |
| Wheel | 70 × 67 mm, clipped Main profile |
| Encoder | 14 × 18 mm, two 4 mm upper chamfers |
| Panel | 238 × 114 mm, one of each board |

For each prefix:

- `.step`: CAD assembly with the substrate, pads and available component bodies.
- `.glb`: colored 3D viewer model with the available component bodies.
- `-bare.step`: board substrate and holes, without components, for mechanical CAD.
- `-preview.png`: angled image from KiCad's native 3D renderer.

Bare STEP files contain the dielectric only, excluding the 0.035 mm copper and
0.010 mm mask on each side. The existing Main files and derived panel specify
1.578 mm overall thickness, while the manufacturing quote uses nominal 1.6 mm.
The manifest records the exact thickness used for each export.

All four boards remain separate. The panel is a manufacturing arrangement,
not the installed mouse assembly. Stack spacing, wheel position, wires, magnets
and the housing are not defined by these PCB files and are not added here.
Lower's substrate includes the 17.26 × 8.60 mm optical opening with R1 mm
internal corners. The missing
U35 body does not fill this opening in the populated previews.

## Component coverage

The exports include 234 available component bodies. Fourteen fitted parts have
no available body in the installed project libraries:

| Board | Missing bodies |
| --- | --- |
| Lower | D5 LED, L1 inductor, U2, U11, J1 USB-C, U3 ESP32 module, U35 optical sensor |
| Upper | U7, U8, U9, U12, U13 |
| Wheel | U21 motor driver |
| Encoder | U27 magnetic encoder |

Their copper footprints remain present. Solder-wire interfaces are correctly
represented as plated holes/pads, without invented plastic connector bodies.
Use the bare-board models for substrate measurements; the partially populated
assemblies do not establish a complete component-height or enclosure clearance.

`manifest.json` records source hashes, thickness, model omissions and export hashes.
`validation.json` records STEP solid checks and GLB parsing/bounds checks.
KiCad reports overlapping contours while exporting the additional surface
faces in the Lower and Panel GLBs. These warnings are recorded in the manifest;
the separate bare STEP substrate solids are independently checked.

Regenerate with KiCad 10 Python using `../export_3d.py`. Validate with a Python
environment containing build123d and trimesh using `../validate_3d.py`.

Board geometry: CERN-OHL-S-2.0. KiCad library component shapes retain their
upstream licensing. These exports do not change the PCB manufacturing files.
