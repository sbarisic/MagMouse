# ACT_5V brake simulation results

24 cases, each run with 200 ns and 100 ns maximum timesteps. All numerical checks pass. Peak rail across the intended-current cases and selected tolerance stresses: **6.1524 V**, below 6.5 V.

**The 10 us response target is not met in every delay-stress case.** The swept delay is comparator transport delay; gate charging and the current measurement criterion add time. Response starts at the comparator input crossing its offset-adjusted threshold and ends at 0.4 A brake current. It excludes sensing-filter delay before that crossing. This is not a claim that the actual comparator takes 10 us.

Ideal thresholds from netlist resistors: 5.982333 V on / 5.725086 V off. Slow-ramp simulation: 5.974928 V / 5.717692 V.

| Case | Peak V | Response us | Bank peak W | Bank energy mJ | Rail target |
|---|---:|---:|---:|---:|---|
| minimum_0.45us_pulse | 5.9900 | 0.553 | 3.037 | 2.101 | PASS |
| minimum_0.45us_repeated | 5.9900 | 0.570 | 3.037 | 4.203 | PASS |
| minimum_0.45us_unplug | 5.9900 | 0.553 | 3.037 | 2.101 | PASS |
| minimum_5us_pulse | 6.0281 | 5.120 | 3.076 | 2.108 | PASS |
| minimum_5us_repeated | 6.0281 | 5.120 | 3.076 | 4.216 | PASS |
| minimum_5us_unplug | 6.0281 | 5.120 | 3.076 | 2.108 | PASS |
| minimum_10us_pulse | 6.0698 | 10.103 | 3.119 | 2.137 | PASS |
| minimum_10us_repeated | 6.0698 | 10.103 | 3.119 | 4.275 | PASS |
| minimum_10us_unplug | 6.0698 | 10.103 | 3.119 | 2.137 | PASS |
| nominal_0.45us_pulse | 5.9780 | 0.577 | 3.025 | 1.416 | PASS |
| nominal_0.45us_repeated | 5.9780 | 0.579 | 3.025 | 3.499 | PASS |
| nominal_0.45us_unplug | 5.9780 | 0.577 | 3.025 | 1.416 | PASS |
| nominal_5us_pulse | 5.9865 | 5.128 | 3.033 | 1.431 | PASS |
| nominal_5us_repeated | 5.9865 | 5.128 | 3.033 | 3.513 | PASS |
| nominal_5us_unplug | 5.9865 | 5.128 | 3.033 | 1.431 | PASS |
| nominal_10us_pulse | 5.9958 | 10.128 | 3.043 | 1.447 | PASS |
| nominal_10us_repeated | 5.9958 | 10.128 | 3.043 | 3.528 | PASS |
| nominal_10us_unplug | 5.9958 | 10.128 | 3.043 | 1.447 | PASS |
| brake_disabled | 13.2666 | n/a | 0.000 | 0.000 | FAIL (diagnostic) |
| excess_regeneration | 10.6301 | 0.553 | 9.565 | 8.476 | FAIL (diagnostic) |
| resistance_stress | 6.0696 | 10.103 | 2.955 | 2.133 | PASS |
| threshold_high | 6.1524 | 10.223 | 3.036 | 2.141 | PASS |
| threshold_low | 5.9883 | 10.204 | 2.877 | 2.125 | PASS |
| threshold_ramp | 6.2178 | 0.561 | 3.272 | 7.438 | PASS |

Bank energy is integrated over the full listed scenario, not necessarily one switching pulse. Per-resistor power and energy are one quarter of the bank values for equal resistors. No resistor temperature or pulse-rating acceptance is inferred.

Repeated pulses are 1 ms on / 6 ms period and have measured average input power below 0.5 W. The single-pulse window average can exceed 0.5 W; it is not a sustained operating point. Unplug occurs 50 us after regeneration starts, when the one-way upstream source is already blocked by the rising rail.

The disabled/excess controls deliberately exceed the target. Because the TVS is omitted, their high voltages indicate inadequate brake absorption, not predicted hardware clamp voltages.

See README.md for model assumptions, provenance, limitations and reproduction instructions. Production boards, panel and the submitted archive remain byte-identical to commit 145d2be.
