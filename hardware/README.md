# Electronics

Status: the independent main and wheel PCBs are routed, with zero unrouted
connections and zero physical DRC/parity issues. Mechanical integration,
manufacturing review and hardware qualification remain open.

- [Main project](modular/main/Main.kicad_pro) and [Wheel project](modular/wheel/Wheel.kicad_pro): active editable designs.
- [Modular package and reviews](modular/README.md): current routing, cable and mechanical status.
- [Original KiCad project](kicad/README.md): retained monolithic reference and circuit documentation.

- [schematics](schematics/README.md): circuit partition and review requirements.
- [pcb](pcb/README.md): layout and release requirements.
- [bom](bom/README.md): candidate component inventory.

Use the [interface allocation](../docs/interfaces.md) and
[power plan](../docs/power.md) as design inputs. Exact package variants, GPIOs,
passive values, protection circuitry and connectors remain to be validated.

License: CERN-OHL-S-2.0; see [LICENSE](LICENSE).
Source location: <https://github.com/sbarisic/MagMouse>.
