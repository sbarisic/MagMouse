# Electronics

Active development: [stacked two-layer boards](two-layer/sandwich/README.md),
with passive plastic clicks and Hall sensing. The two 70 × 100 mm Main boards
remain unrouted; Wheel and Encoder are routed. Mechanical integration,
manufacturing review and hardware qualification remain open. Earlier routed
checkpoints and manufacturing packages below retain the superseded button coils.

- [Main project](modular/main/Main.kicad_pro) and [Wheel project](modular/wheel/Wheel.kicad_pro): earlier routed designs.
- [Experimental two-layer boards](two-layer/README.md): separate Main, Wheel and
  Encoder variants with clean reported native CAD checks; electrical, routing
  optimization and manufacturing review remain open.
- [Rev-A bench panel and assembly package](bench/README.md): earlier cost-reduction
  variant, four-layer Encoder, one-population purchasing list and quote-only
  manufacturing files. The derived panel does not replace the source boards.
- [Modular package and reviews](modular/README.md): earlier routing, cable and mechanical status.
- [Original KiCad project](kicad/README.md): retained monolithic reference and circuit documentation.

- [schematics](schematics/README.md): circuit partition and review requirements.
- [pcb](pcb/README.md): layout and release requirements.
- [bom](bom/README.md): candidate component inventory.

Use the [interface allocation](../docs/interfaces.md) and
[power plan](../docs/power.md) as design inputs. Exact package variants, GPIOs,
passive values, protection circuitry and connectors remain to be validated.

License: CERN-OHL-S-2.0; see [LICENSE](LICENSE).
Source location: <https://github.com/sbarisic/MagMouse>.
