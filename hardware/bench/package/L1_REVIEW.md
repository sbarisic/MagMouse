# Main L1 replacement review

2026-09-12. Main now uses Bourns **SRP4020CC-3R3M**. The historical monolithic
design remains unchanged. This is component/layout qualification for a bench
prototype, not a measured converter stability or temperature result.

The [Bourns drawing](https://www.bourns.com/docs/product-datasheets/srp4020cc.pdf)
specifies 3.3 uH +/-20%, 76 mOhm maximum DCR, typical 3.5 A heating current and
4 A saturation current (30% inductance reduction). Operating temperature is
-40 to 125 C including self-heating. These current figures are typical, not
guaranteed minima at every temperature. Compared with the former 91 mOhm part,
the room-temperature DC copper-loss ceiling at 1 A falls from 91 to 76 mW;
this excludes ripple, AC/core losses and temperature dependence.

[TI TPS6216x guidance](https://www.ti.com/lit/ds/symlink/tps62160.pdf), sections
8.3.2 and 9.2.2.4, recommends 3.3 uH at low input voltage. At 5.25 V input,
3.3 V output, 1 A load, 2.64 uH and the typical 2.25 MHz switching frequency,
the calculated ripple is 0.206 A peak-to-peak and peak current is 1.103 A.
This is a nominal-frequency screen, not a worst-case frequency guarantee.
Even a separate 1 MHz sensitivity case gives 1.232 A peak; 20% margin gives
1.479 A. The datasheet's 2.45 A static current-limit maximum at its specified
12 V/25 C test point plus typical propagation overshoot is below the Bourns
typical saturation figure, but is not a full hot/fault guarantee. Preserve
current limiting and measure startup, load steps, ripple and temperature.

No output capacitor value, regulator, feedback path or current budget changed.
The approved existing LC combination still requires effective capacitance and
hardware load-step verification. L1 selection does not increase the 1 A rail rating.

## Land pattern and local copper

The new shared footprint uses two **1.5 x 2.4 mm** rounded lands at **3.7 mm**
centres: 5.2 mm outer span and 2.2 mm internal gap. Body outline is nominal
4.45 x 4.06 mm; the courtyard includes maximum body tolerance and at least
0.25 mm clearance (5.70 x 4.82 mm overall). No unrelated 3D model is assigned.

L1 is rotated 90 degrees at (64.45,23.45) mm; C2 moves from X=67.70 to 67.85 mm.
U2, C1, C3 and C23 stay in place. Existing L1/C2-connected track endpoints
follow the new lands; no signal is moved onto In1. The switch remains on F.Cu
without vias and below the unchanged 5 mm review ceiling. Native DRC/parity,
power, analog, USB and return checks must refer to the new source hash.

The schematic/PCB MPN, footprint and supplier fields agree. The old LCSC part
number was removed rather than attached to the Bourns substitute. Mouser's
earlier 2026-09-12 observation was EUR 0.671, MOQ one; delivery/tax and stock
reservation remain separate. See the generated purchasing list.
