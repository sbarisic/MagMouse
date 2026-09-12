# Mechanical design

Status: editable Rev-A bench fixture CAD and optical datums; final shell and
in-mouse mechanisms remain provisional.

- [housing](housing/README.md): enclosure, optics and component packaging.
- [scroll-wheel](scroll-wheel/README.md): wheel, shaft, motor and encoder alignment.
- [button-mechanisms](button-mechanisms/README.md): three contactless haptic buttons.
- [optical](optical/README.md): PMW3360/LM19-LSI stack and aperture reference dimensions.
- [bench](bench/README.md): build123d source, 19 printable PETG part designs,
  STEP/STL exports, removable supports, wire clamps and dimensioned assembly views.

The bench fixture uses build123d 0.11.1. Optical and motor dimensions that lack
supplier evidence remain parameters requiring measurement.
Validate magnet separation with wheel and custom button-coil fields active, including
temperature and full travel. Preserve physical stops and passive return behavior
so loss of power does not depend on actuator control to constrain the mechanism.
The elastic button paddles provide passive return; validate their material,
geometry, print process, creep and fatigue as functional springs.

License: CERN-OHL-S-2.0; see [LICENSE](LICENSE).
Source location: <https://github.com/sbarisic/MagMouse>.
