# Current-board power and interlock simulation

This study addresses the review's startup-current, heartbeat, brownout/recovery,
chip-select bias and unpowered-nSLEEP questions. It uses fresh native KiCad
netlists from the active four-board design. It does not change a circuit,
execute firmware, or turn a simulation result into hardware acceptance.

Read [RESULTS.md](RESULTS.md) for conclusions and remaining tests.
[results/validation.json](results/validation.json) contains the measured results;
[results/inputs.json](results/inputs.json) identifies source hashes, capacitor
inventories and explicit topology checks. The historical brake study is separate
and is not presented as validation of this revision.

## Models and limits

| Part of study | Model | What it can establish |
| --- | --- | --- |
| Voltage supervisor | TI TPS3808G01 transistor macro-model with the actual 105 k/10 k/1 nF network and 10 k pull-up | Nominal transient behavior in this simulator; compare timestep results before accepting a case |
| Source/interlock/PWM gates | Logical evaluation wired from native netlist pins | Steady logical permissions, including each independently missing permission |
| Heartbeat | Event-driven retriggerable one-shot; actual R46/C27 nominal RC | Timeout, stuck-high/low and asynchronous clear behavior under the selected timing assumptions |
| eFuses and startup | Averaged, reverse-blocking, slew-limited/current-limited sources; UVLO hysteresis | Response to imposed load envelopes; not actual IC startup, thermal latching or MCU boot |
| Buck during startup | Ideal voltage conversion for capacitor charging, assumed 85% efficiency | Additional charging demand only; switching, PG/reset timing and regulator dynamics omitted |
| Motor | Prescribed current-equivalent load, with resistive rolloff below 4.5 V | Power-path sensitivity; no winding, back-EMF, mechanical motion or regeneration prediction |
| Independent recovery | RC filter and datasheet threshold/hysteresis/timer state machine | Potential automatic retries under persistent requests; not a substitute for the vendor model or firmware |
| nSLEEP with VM off | No applicable leakage model located | Remains unverified; an absolute-maximum rating is not a powered-off leakage specification |

TI's [TPS3808 model package](https://www.ti.com/lit/zip/slim038b) contains an
unencrypted 2011 PSpice model. The local ngspice adaptation removes nine
always-false `ERROR` annotations and expands ten unity-factor `Cbreak` capacitors
into ordinary capacitors. Component values and transistor circuitry are unchanged.
The adapted model has not been compared against a PSpice run. Copyright headers
remain intact. Original downloads and adapted models stay in ignored build output.

The [TPS25947 model](https://www.ti.com/lit/zip/slvmdj6a) is encrypted for
PSpice. It is inventoried but **not executed**. Do not describe the averaged
startup tests as TI eFuse model results. No applicable DRV8316 transistor model
was located on the manufacturer's product page.

[Model provenance](results/models.json) records archive/library/engine hashes.
All simulation jobs use KiCad 10's ngspice shared library with PSpice compatibility.
The supervisor's accepted imposed-waveform tests compare 2 us and 1 us maximum
timesteps. The supply-only tests compare 4 us and 2 us and check charge balance.
The coupled supplier-model runs use 1 us and 0.5 us after 4/2 us runs disagreed.
A numerical completion is not sufficient if enable edges do not converge.

## Assumptions

- Source voltage and cable loop resistance are imposed cases, not measurements.
  The nominal cases use 5.0 V and 0.15 ohm; the weak-source case uses 4.75 V and
  0.50 ohm. Source protection and cable inductance are omitted.
- The supply model includes the current PCB contact-graph path estimates, a
  nominal 28.3 mOhm per eFuse and an assumed additional 30 mOhm actuator harness/
  return allowance. It does not solve the complete distributed return network.
- PWR_5V and ACT_5V capacitance comes from directly connected schematic capacitors.
  One case uses 40% of nominal capacitance. ESR/ESL, voltage bias and temperature
  are not a validated capacitor model. Charge-pump capacitors are not counted as
  direct rail-to-ground capacitors.
- Logic loads are explicitly input-referred current envelopes. They already
  include assumed continuous conversion losses. The separate 3V3 capacitor
  charging term avoids counting continuous logic power twice.
- eFuse current limits are nominal. No full current-limit tolerance, switch SOA,
  thermal latch, FLT/reset feedback, or fast overcurrent response is modeled.
  The D3 low clamp is represented by permit gating; its leakage is not simulated.
- Supply-only motor loads deliberately remain present below the drive threshold
  to expose insufficient headroom. They do not claim the real motor stays enabled.
  The coupled runs explicitly gate the load using the supervisor.
- Supervisor threshold corners include +/-2%, resistor 0.1% plus 25 ppm/K over
  -40 to 125 C, +/-25 nA sense leakage and 0 to 3% hysteresis. The 8.352 mV shared
  sense-feed allowance is included in the analytical droop screen only.
- Supervisor assertion delays of 20 us and 100 us in the analytical/behavioral
  screens are typical/reference and selected stress assumptions respectively.
  **100 us is not a guaranteed upper bound.** Recovery delay is 12-28 ms per the
  datasheet. Sharp drops can cross 4.5 V before drive is disabled.
- Heartbeat timeouts of 7, 10 and 15 ms are selected sensitivity cases based on
  nominal 10 kOhm/1 uF RC. These do not establish component timing corners.
- CS bias screening uses 3V3 +/-5%, resistors +/-1% and aggregate input leakage
  +/-10 uA. This is a chosen allowance, not an independently proven system bound.
- No processor instruction execution, USB enumeration, optical/Hall magnetic
  model, firmware scheduling, RF, EMI, soldering or mechanical fit is simulated.
- Imposed-waveform enable plots are qualified only above 2.7 V host supply.
  This is a model-validity mask, not an extra hardware gate. Early host-rail
  ramp glitches are not assessed; the actual interlock starts with MR low.

## Reproduce

Use a Windows Python with NumPy and Matplotlib, and KiCad 10. The development
environment used `E:/Projects/CAD/.venv/Scripts/python.exe`. No system packages
or KiCad preferences were changed.

```powershell
python hardware/simulation/power-validation/run.py
python hardware/simulation/power-validation/review.py
```

`run.py` downloads model archives only when absent. Downloads are from TI;
their provenance is recorded on every run. `--reuse` reprocesses local waveforms
only when the generated circuit text is identical, then reruns all measurement
and acceptance checks. This is useful for report-only changes after a complete
simulation. A clean run without that flag executes every SPICE case.

Full waveforms/decks/logs and vendor materials live under ignored
`build/power-validation`. Compact JSON, plots and this review stay with the
source. The local artifact manifest documents optional regenerable files; a
fresh checkout intentionally does not contain them.

## Primary references

- [TPS3808 datasheet, SBVS050N, August 2026](https://www.ti.com/lit/ds/symlink/tps3808.pdf)
- [TPS25947 datasheet, SLVSFC9C, May 2026](https://www.ti.com/lit/ds/symlink/tps25947.pdf)
- [SN74LVC1G123 datasheet, SCES586E, March 2024](https://www.ti.com/lit/ds/symlink/sn74lvc1g123.pdf)
- [Nexperia 74LVC125A, Rev. 12, May 2025](https://assets.nexperia.com/documents/data-sheet/74LVC125A.pdf)
- [DRV8316, SLVSF16B, April 2022](https://www.ti.com/lit/ds/symlink/drv8316.pdf)
- [USB-IF peripheral power policy](https://compliance.usb.org/index.asp?Format=Standard&UpdateFile=Policies)

Supporting code: GPL-3.0-or-later. Vendor model copyrights are unchanged.
