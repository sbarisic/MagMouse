# Mechanical design

Status: optical datums and mechanism plans are retained; final shell and
in-mouse mechanisms remain provisional. The superseded Rev-A fixture CAD and
exports are available through the historical link below.

- [housing](housing/README.md): enclosure, optics and component packaging.
- [scroll-wheel](scroll-wheel/README.md): wheel, shaft, motor and encoder alignment.
- [button-mechanisms](button-mechanisms/README.md): three plastic click mechanisms with Hall sensing.
- [optical](optical/README.md): PMW3360/LM19-LSI stack and aperture reference dimensions.
- [bench](https://github.com/sbarisic/MagMouse/blob/f0acacb170f736648a6b5170140de5a96bac91d5/mechanical/bench/README.md): build123d source, 19 printable PETG part designs,
  STEP/STL exports, removable supports, wire clamps and dimensioned assembly views.

The bench fixture uses build123d 0.11.1. Optical and motor dimensions that lack
supplier evidence remain parameters requiring measurement.
Validate sensing-magnet separation with wheel fields active, including
temperature and full travel. Preserve physical stops and passive return behavior
so loss of power does not depend on actuator control to constrain the mechanism.
The plastic button mechanisms provide click and passive return; validate their material,
geometry, print process, creep and fatigue as functional springs.

License: CERN-OHL-S-2.0; see [LICENSE](LICENSE).
Source location: <https://github.com/sbarisic/MagMouse>.
