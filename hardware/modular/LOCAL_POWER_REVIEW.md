# Wheel-local storage and clamp review

2026-09-10. Implemented in [19_Local_Power.kicad_sch](wheel/19_Local_Power.kicad_sch).
This closes the missing local-parts finding at schematic level. Effective
capacitance, startup, braking and cable-fault acceptance still require hardware.

## Parts added

| Ref | Part | Purpose |
| --- | --- | --- |
| C90 | Panasonic 16SVPC100M, [JLC C136275](https://jlcpcb.com/partdetail/16SVPC100M/C136275) | 100 uF/16 V polymer bulk, positive pad 1 to ACT_5V |
| D6 | Littelfuse SMBJ6.0A, C83270 | Wheel-local secondary TVS, cathode pad 1 to ACT_5V |
| R146 | UNI-ROYAL 0603WAF4701T5E, C23162 | 4.7 kohm local discharge path |

All connect to local power GND. Main-board D2 and R69 remain in place. The
autonomous comparator/reference/MOSFET/resistor brake remains on the wheel;
it must function with both cables absent and with the ESP32 held in reset.
Catalog matches do not reserve stock or establish assembly acceptance.

The [Panasonic specification](https://industrial.panasonic.com/ww/products/pt/os-con/models/16SVPC100M)
lists a 6.3 mm diameter, 5.9 mm height, 24 milliohm ESR at 100 kHz, 300 uA
maximum leakage and 2490 mA ripple at 100 kHz/105 C. Do not apply those ESR
or ripple values directly at another frequency or temperature. Reserve at
least 6.0 mm component height plus mechanical clearance in the wheel assembly.

Native footprint `Capacitor_SMD:CP_Elec_6.3x5.9` matches the
[C6 recommended lands](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000COL10.pdf):
2.1 mm inner gap, 9.1 mm overall span, 1.6 mm width. KiCad pads are 3.5 x 1.6 mm
at x = +/-2.8 mm. The land drawing was visually inspected. Check polarity in
assembly preview and include Panasonic's reflow restrictions in assembler review.

The [Littelfuse SMBJ table](https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_smbj_datasheet.pdf.pdf)
specifies 6 V standoff, 6.67–7.37 V breakdown and 10.3 V clamp for SMBJ6.0A
under its specified pulse conditions. **D6 does not enforce the 6.5 V rail
target and cannot replace the active brake.** Review pulse energy, leakage,
repetition and downstream absolute limits using measured waveforms.

## Inventory and calculated screens

C41–C43/C65 provide 0.4 uF nominal; C44/C45/C68/C69 provide 40 uF nominal.
With C90, wheel-local ACT storage is **140.4 uF nominal**. The connected main
and wheel total is **210.7 uF nominal**. Neither total is an effective-capacitance
measurement. Capacitance across other rails is not included.

The [SVPC series datasheet](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000C256.pdf)
specifies +/-20% initial capacitance at 120 Hz/20 C and a further +/-20% change
after its endurance test. Applying both low corners gives 64 uF for C90 alone
(80 uF before endurance), above the 47 uF design floor without MLCC credit.
This selection screen does not bound transient-frequency or operating-temperature
behavior. Effective C >=47 uF remains a measured qualification requirement.

| Screen | Result and scope |
| --- | --- |
| Connected capacitance-only startup | 42.14 mA at the nominal 0.2 V/ms ramp; +20 mA versus the old circuit |
| Wheel stored energy at 6.5 V | 2.966 mJ nominal; excludes motor energy |
| R146 loss at 6.5 V | 8.99 mW |
| Discharge 6.5 V to 0.5 V | 1.69 s at nominal C/R, with no supply or continuing generation |
| Conditional running brake peak | 6.300 V before unmodeled inductance, under the assumptions below |

Startup uses the [TPS25947 application equation](https://www.ti.com/lit/ds/symlink/tps25947.pdf),
SR[V/ms] = 2000/C26[pF], with existing C26 = 10 nF. This is a nominal estimate,
not a maximum inrush guarantee. Active loads, downstream charging, tolerances,
leakage, hot reconnection and source transitions are additional. A discharged
wheel plugged into an already enabled ACT rail does not receive a fresh
controlled ramp. No live mating is an accepted operating mode.

The transient screen uses the existing rounded brake turn-on ceiling of
6.175 V, returned **bus** current <=0.4 A, effective C >=47 uF, response <=10 us
and effective series resistance <=0.100 ohm. The last value is a qualification
ceiling, not a capacitor guarantee. I*dt/C adds 85.1 mV; I*ESR adds 40 mV,
leaving about 200 mV below 6.5 V for effects omitted from this lumped model.
The 200 us comparator cold-start screen from 2.4 V reaches 4.142 V with the
same assumptions. Neither calculation proves motor energy or actual rail peaks.
Retain the existing 0.5 W average braking limit pending thermal measurements.

## Placement and acceptance work

- Place C90 at the wheel VM/brake power junction. Retain U21's close ceramic
  bypasses; keep their return and the Q5/brake return compact and wide.
- Place D6 with short local power connections. Keep its pulse return out of
  ADC2/reference ground paths. R146 must remain connected after separation.
- Measure effective C and impedance at bias and temperature. Check inrush,
  cable ringing, VM droop and brake response under limited supplied and
  generated current, including reset, power loss and restart.
- Check cable current sharing with both harnesses fully connected. Per the
  user's prototype scope, power-GND-open/disconnect survival is not a blocker
  and does not require a separate wheel-feed limiter. Local storage remains
  useful for normal VM transients and regeneration.

`verify_split.py` now checks the added parts, values, footprints, polarity and
rail connections and reports these calculations. Regression mutations cover
reversed bulk/TVS, missing clamp, insufficient replacement bulk and disconnected
bleed. The strict review gate remains open for physical qualification.
