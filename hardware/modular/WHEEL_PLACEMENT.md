# Independent wheel PCB: first placement

Historical starting placement below. The 2026-09-11
[power and analog routing pass](WHEEL_ROUTING.md) supersedes its unrouted status
and adjusts nearby driver/brake parts. The live PCB has 61 unconnected items;
`wheel-placement.json` remains the original placement recipe. Current placement
guard results are in `wheel-placement-review.json`.

2026-09-10. Open [wheel/Wheel.kicad_pro](wheel/Wheel.kicad_pro) and its PCB.
The editable board contains **87 footprints on a 55 x 60 mm, four-layer outline**.
All assembly parts are on the front. Native physical DRC and schematic parity
both report zero issues. There are **233 unconnected items, no tracks/vias and
no zones**. This is a placement draft, not an orderable board.

## Placement decisions

- J9 is at the upper edge, rotated 180 degrees, with its cable mouth pointing
  out of the board. The [cable contract](CABLE_REVIEW.md) maps J8.N to J9.(31-N).
  J11 power is also on the upper edge, separated from the signal header.
- U21 is central. ADC2/U23 and its RC filters sit above the SOA/SOB/SOC pins.
  The phase pads face downward toward J5. Keep the eventual phase copper in
  that lower corridor, away from the current-sense/filter island.
- U26 sits between J9 and ADC2; U24 serves driver configuration. U22/Q4 and
  the PWM command bias sit on the digital side of U21.
- C90 and D6 are on the power-entry side; U21 retains close VM/charge-pump/buck
  support parts. The brake comparator/reference and Q5 share the lower-left
  region, with the four brake resistors along the lower edge.
- The right/lower-right region remains available for routing and mechanical
  integration. Mounts, supports, motor-wire clearance and cable bends are not
  finalized. Do not infer a shell fit from a clean courtyard check.

Measured **airwire** distances through the filter resistors, excluding their
internal pin-to-pin length, are 6.28/5.65/8.15 mm for A/B/C. ADC input to filter
capacitor spans are 3.21/2.55/2.86 mm. U30 output to Q5 gate through R119 is
8.15 mm. These measures guard compact placement; they are neither copper
lengths nor evidence of analog performance. Refine capacitor placement during
local routing if pad escapes show a shorter, quieter arrangement.

In1 is available in the retained JLC041611-2116 stackup. No ground plane has
been poured yet. Its eventual continuity, thermal vias, current-return paths
and USB/SPI reference checks must be established from the routed copper.
The original motherboard and its existing routes remain unchanged.

## Validation

[wheel-placement-review.json](wheel-placement-review.json) records board and
netlist hashes, 295 checked pin assignments, outline/courtyard checks, assembly
side, J9 orientation and the placement distances above. Native DRC includes
clearance, pad shorts, courtyards and schematic parity. Four regression tests
exercise the saved board, a reversed connector, ADC moved to the phase side,
and a swapped current-channel net.

```powershell
$kicadCli = 'C:/Users/cartm/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe'
$kicadPython = 'C:/Users/cartm/AppData/Local/Programs/KiCad/10.0/bin/python.exe'
& $kicadCli pcb drc --format json --schematic-parity --output build/modular/wheel-drc.json hardware/modular/wheel/Wheel.kicad_pcb
& $kicadPython hardware/modular/verify_wheel_placement.py --board hardware/modular/wheel/Wheel.kicad_pcb --netlist build/modular/wheel-review/netlist.xml --drc build/modular/wheel-drc.json --output hardware/modular/wheel-placement-review.json
& $kicadPython -m unittest discover -s hardware/modular -p test_wheel_placement_checks.py
```

`start_wheel_board.py` and `wheel-placement.json` record the initial placement
construction. The generator refuses to overwrite an existing board. The PCB
is now the editable source; future routing should modify it directly.

## Next routing pass

1. Route local VM bypass, phase exits and brake power loops while keeping the
   upper sensing corridor clear. Route the compact comparator/reference/gate
   connections with quiet local returns.
2. Route SOA/SOB/SOC through their RC filters to ADC2 and connect its supplies,
   decoupling/reference and ground. Replace placement-distance checks with
   saved-copper connectivity, length and aggressor/reference checks.
3. Add continuous In1 ground, thermal spreading/vias and remaining supplies;
   inspect where switching and ADC return currents flow.
4. Route SPI3, then SPI2 and commands. The current 20 MHz acquisition target
   still needs ESP32 sampling/loaded-cable validation; retain slower stopped-
   motor bring-up settings. Finish mechanics and manufacturing checks afterward.

Internal cable disconnect survival remains outside the user-approved prototype
scope. Cable mating tolerance and normal connected-operation checks still apply.
