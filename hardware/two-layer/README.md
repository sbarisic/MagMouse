# Active two-layer PCBs

Open the [stacked-board project overview](sandwich/README.md).

| Board | Project | Outline |
|---|---|---|
| Lower Main | [Lower](sandwich/lower/Lower.kicad_pro) | 70 x 100 mm tapered |
| Upper Main | [Upper](sandwich/upper/Upper.kicad_pro) | 70 x 100 mm tapered |
| Wheel | [Wheel](sandwich/wheel/Wheel.kicad_pro) | 70 x 67 mm clipped Main profile |
| Encoder | [Encoder](encoder/Encoder.kicad_pro) | 14 x 18 mm with upper chamfers |

The `sandwich` directory contains the active routing tools, review evidence,
3D exports, current quote packages and four-board panel. `main-circuit` is the
combined schematic reference used to check the Lower/Upper partition; edit the
independent board schematics for development. Shared resources are in
[hardware/common](../common/README.md).

The oversized two-layer experiments and their one-time conversion scripts have
been removed from this checkout. They remain in [Git history](../../docs/history/README.md).
