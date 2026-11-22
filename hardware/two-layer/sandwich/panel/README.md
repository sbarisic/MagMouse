# Three-board quotation panel

One 238 × 114 mm, two-layer panel contains one Lower, Upper and Wheel
board. Five panels provide five complete sets. The individual board outlines,
component positions and copper are preserved by translation; nets are isolated
between boards. The panel uses 2 mm routed gaps, 5 mm tabs and 0.6 mm mousebites
on 0.9 mm pitch. The drill row lies outside each finished board outline.

The November circuit correction moves two Wheel tabs to clear the revised
copper: Wheel now has two tabs on its top edge and two on its bottom edge.
The individual board geometry, mounting holes and harness positions are unchanged.

Upload `MagMouse-panel-gerbers.zip` as **Panel by Customer**, **3 designs**,
**5 panels**, FR4, 1.6 mm, 1 oz, green/white, ENIG 1 µin, 0.30 mm minimum via
drill and tented vias. Components, assembly and stencil are separate.

`panelize.py` generates this folder from the three individual boards and checks
exact translated pads, traces, drills and filled copper; connected substrate;
router access; and native KiCad DRC. `panel-manifest.json` records source hashes.
The individual boards also pass ERC, DRC and schematic parity checks, with zero
unconnected nets and zero via-hole/SMD-pad intersections.

This is a quotation package. Supplier CAM approval and prototype electrical,
thermal and enclosure-fit checks remain necessary before production release.

The former Encoder position is panel waste, without its slots or mouse bites.
The three remaining boards retain their positions and outlines.

`Panel-top.png` and `Panel-bottom.png` show copper, fills, pads, vias, silkscreen
and routed edges across the entire panel. The bottom plot is mirrored to show
the physical underside. SVG originals allow inspection at arbitrary zoom.
Regenerate with `../render_panel.py`.
