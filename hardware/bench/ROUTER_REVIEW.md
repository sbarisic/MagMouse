# Rev-A panel routing review

Final validation: 71 bench/panel/router tests, 60 modular tests and 14
native/electrical checks PASS. Exported routing has eight closed openings;
minimum perforation-to-slot web is 0.4385236 mm. All 40 retained corner
patches were inspected. Source boards and stencil aperture geometry are
unchanged. See router-images/index.html for the corner review gallery.

Design basis: nominal 2.00 mm router, 1.00 mm internal radius, 0.002 mm
geometric verification tolerance. Factory cutter selection and CAM acceptance
remain pending. These verification paths are not machine G-code.

All eight openings are generated as cutter envelopes, with rounded tab ends.
Wide waste pockets include clearing paths in the coverage model. Exactly
2 mm corridors retain a 0.001 mm-wide numerical centre corridor instead of
being lost by polygon erosion. The nominal 2 mm sweep is checked within
0.002 mm; published removal contours are clipped to the original permitted
removal region. Contours are simplified by at most 0.00025 mm and snapped
to KiCad's grid before serialization; the final Gerber must still pass the
0.002 mm sweep comparison and have exactly closed, non-branching contours.
All individual source-board outlines remain unchanged.

The frame's curved offsets now use finer arc tessellation. The router pass
also corrects a tight transition near the encoder opening. Retained material
is permitted only near convex corners/curves; a narrow passage or inaccessible
pocket cannot silently disappear. Convex external board corners remain valid.

Panel size, board positions/outlines, tab centres, fifty 0.6 mm perforations,
four tooling holes and all functional copper remain unchanged. Tabs are checked
against the actual routed material for a full 5 mm bridge into board and frame,
with at least 0.2 mm of material from perforation edges to routing. Hole-to-hole
webs remain 0.3 mm. Factory routing tolerances still require CAM confirmation.

The panel manifest records the cutter paths, retained corner patches and tab
web measurements. Independent mechanical-Gerber validation is recorded in
package/evidence/router-gerber.json. Source hashes, electrical acceptance,
fixture validation and test logs accompany the local package. Bench fixtures
support individual depanelled boards; remove tab remnants to the documented
unit outline before seating boards in the saddles.

No stencil aperture or source board changed. The submitted 2026-09-12 archive
is preserved separately. This package is local and unsubmitted.
