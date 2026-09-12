> Rev-A bench update: internal interfaces now use soldered through-hole arrays.
> The active manufacturing-review package is `hardware/bench/`; its HARNESS_REVIEW.md
> and generated wire maps supersede historical FFC/JST details below. Order scope
> is five bare three-board panels, one component population and one stencil.
> No final-shell or supplier/CAM acceptance is claimed.

# Mechanical interface register

2026-09-11. The user has no wheel/shaft/bearing parts or mechanical CAD yet
and explicitly chose to keep mechanics provisional while fixed main-board
power routing proceeds. **No mechanical interface freeze is claimed.**

The main-board envelope is approved: 125 mm long, 80 mm maximum width and
44 mm front edge. The shell will be larger. Curvature and width-transition
locations still follow draft assumptions. Main coordinates below are footprint
origins in mm, viewed from the component side; Y=0 is the front, Y increases
toward the rear, and the centre line is X=40. They are routing datums, not
the connector opening or optical centre dimensions from a mechanical drawing.

| Interface | Current CAD datum / reservation | Still needed before freeze |
| --- | --- | --- |
| Main mounting | No mounting-hole pattern defined | Baseplate supports, screw size, tool access and component/trace clearances |
| USB-C J1 | (40, 4), 180 degrees | Plug and shell opening, strain relief, insertion clearance |
| Wheel mechanism | All-copper reservation X=34.5..46, Y=28..51 | GB1806 exact variant, shaft, bearings, wheel diameter, supports and full travel envelope; present rectangle is only a reservation |
| Wheel electronics | Separate routed 55 x 60 mm board | Position, height, orientation, supports, motor-wire exits and clearance over both boards |
| Encoder J6 | Main (28, 18.5), 180 degrees; separate upright MA735 board | Shaft magnet, sensor gap/alignment, upright support and cable route |
| Signal cable J8 | Main (63, 70), 0 degrees; front exit reservation X=51..75, Y=75..81 | Actual FFC mating tolerances, cable length, bend radius, latch access, stack height and strain relief |
| Power cable J10 | Main (72, 91), 0 degrees | Mating housing, wire gauge/length, bend and connector access |
| Optical U35 | (40.5, 72.5), -90 degrees; underside lens drawing 20 x 22 mm | Sampled PMW3360/lens stack, baseplate aperture, lens retention, board thickness/feet and lens-to-surface height |
| Buttons / Hall | J2 (17,35), J3 (17,60), J4 (63,35); U7 (17,41.5), U8 (24,60), U9 (63,41.5) | Paddles/flexures, middle-click travel, coil/magnet gaps, Hall magnet paths and hard stops |
| ESP32 antenna | Existing footprint RF/copper keepout, partly beyond rear edge | Shell material and clearance from fasteners, cables and wheel/button hardware |
| Test access | 37 main B-side pads; wheel local test points | Probe access with baseplate and mechanism fitted |

The optical aperture is a copper/pad/via keepout, **not a fabricated hole**.
The lens drawing and wheel reservation must be checked against actual parts
before any cutouts, supports or final sensitive placement are accepted.

Changes to a protected routing datum require rechecking placement, copper,
return paths and harness pin orientation. Keep Hall/paddle routing provisional
until the mechanism establishes those positions. Fixed power/control circuits
can proceed within the current reservations.

Panelization requires stable main and wheel placement **and** reviewed
mechanical interfaces. Before that release, also close the matched FFC/header
choice, common encoder stackup, filled/capped-via assembly, test access and
manufacturing review. Existing nesting drawings remain historical planning;
they are not a production panel or final quote package.
