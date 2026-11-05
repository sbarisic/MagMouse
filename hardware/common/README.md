# Shared electronics resources

The active two-layer projects use these symbols, footprints and Python helpers.
Library nicknames are preserved so existing component identities do not change.
See [library licensing](KICAD-LIBRARY-LICENSE.md).

Run board tools with KiCad 10's Python interpreter. Geometry tools use Shapely
2.1.2 from the local environment or `build/two-layer/python`. Panel geometry
regressions can be run with `python -m unittest discover -s hardware/common`.

`copper_graph.py` provides native electrical-contact paths and a resistance
screen. It is not a thermal or current-rating simulation. The active review
sets via resistance from each board's saved thickness.

`gpio-allocation.json` is the inherited circuit allocation reference. The
independent Lower/Upper schematics define the active connections, including
the pins freed by removing the button actuators.
