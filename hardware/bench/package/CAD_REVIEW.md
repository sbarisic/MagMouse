# Bench panel review evidence

Review snapshot: 2026-09-11, KiCad 10.0.6. This is not manufacturing release.

- Native DRC: Main, Wheel, Encoder and derived Panel each have zero physical
  violations and zero unconnected items. All three individual boards also
  have zero schematic-parity issues.
- Main strict analog, strict routing, USB/reference/ESD, power and control
  checks passed. `package/evidence/acceptance.json` records source hashes.
- The modular regression suite passed 59 tests. The panel suite passed five
  tests, including deliberately modified source hashes, copper, net mapping
  and tab positions. Logs are in `package/evidence/`.
- Two native panel builds were byte-identical. Panel hash:
  `750b759e8e756b03552c022ffa5819fc0dbf9515f1ae25ec63b37c09a0d3a3d8`.
- Export validation checked 1,196 source pads, 18,323 track/via objects and
  119,734 saved ground-fill vertices under the coordinate transforms. The
  three boards retain separate net namespaces. No functional tab copper.
- The via-only inventory contains 1,088 entries. Component, NPTH, tooling
  and tab perforation holes are excluded from the fill instructions.
- The one-population variant has 291 populated references and 290 SMT
  references. Main U32 paste is excluded; optical sensor fitting is separate.
  The combined stencil contains 1,084 apertures. Rectangle area/perimeter
  screening at 0.10 mm passed; this is not a paste-volume qualification.

Rendered panel F.Cu and In1.Cu views were visually inspected at overview
scale. Copper remains inside the respective board shapes and their original
optical/mechanical/antenna exclusions remain visible. The three reference
planes are separate. The automated source-fill equality checks provide the
more precise evidence that panelization did not change the unit ground
geometry. Overview images do not establish local signal integrity.

The mechanical panel view, stencil view and 1:1 support-jig drawing were
also inspected. They show separate Main/Wheel/Encoder groups, a 100 mm
print scale bar and removable support positions. Final JLC CAM group
positions must be used for the actual jig if the stencil groups are moved.

Still open: manufacturer-specific paste release/windowing/profile review,
fabricator approval of perforated tabs and selective via filling, cable
qualification and physical bench fit. Hardware testing is required for USB,
analog noise, motor/brake behavior and electrical/thermal acceptance.
