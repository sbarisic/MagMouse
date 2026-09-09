# Mechanical design

Status: requirements and optical reference datums; no manufacturing CAD models.

- [housing](housing/README.md): enclosure, optics and component packaging.
- [scroll-wheel](scroll-wheel/README.md): wheel, shaft, motor and encoder alignment.
- [button-mechanisms](button-mechanisms/README.md): three contactless haptic buttons.
- [optical](optical/README.md): PMW3360/LM19-LSI stack and aperture reference dimensions.

Choose an editable CAD format and document its tool/version when modeling begins.
Validate magnet separation with wheel and custom button-coil fields active, including
temperature and full travel. Preserve physical stops and passive return behavior
so loss of power does not depend on actuator control to constrain the mechanism.
The elastic button paddles provide passive return; validate their material,
geometry, print process, creep and fatigue as functional springs.

License: CERN-OHL-S-2.0; see [LICENSE](LICENSE).
Source location: <https://github.com/sbarisic/MagMouse>.
