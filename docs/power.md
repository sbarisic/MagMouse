# Power design constraints

The intended full-power source is an externally powered Type-C downstream port
advertising 3 A at 5 V. This is a design target, not an unconditional load allowance.
Detect source advertisement and respect attach, configuration, suspend, and
capability changes. Two Rd resistors alone do not tell firmware how much current
is available. A sink/current detector and its interface remain TBD.

| State | Proposed behavior |
| --- | --- |
| Unattached, unknown capability, reset, or fault | Actuators disabled |
| Default USB power | Conservative input budget for applicable USB state; haptics disabled initially |
| Valid 1.5 A Type-C advertisement | Reduced force envelope after reserving logic power |
| Valid 3 A Type-C advertisement | Full validated force envelope within input and thermal limits |
| Suspend or capability loss | Remove actuator demand and apply permitted state budget |

The original notes mention 500/900 mA together. Do not infer 900 mA for this
USB 2.0 Full-Speed device merely because it is behind a USB 3 hub. Resolve the
applicable USB/Type-C rules during electrical design using the specifications in
[references](references.md).

## Rails

- Protected VBUS feeds wheel and custom button-coil drivers and the logic converter.
- The starter selects TLV62569DBVR with SWPA4020S2R2MT (2.2 uH), a
  100 kOhm / 22.1 kOhm divider and 20 uF nominal output capacitance for 3.315 V.
  Use a provisional 1 A continuous logic-rail target pending thermal tests;
  the inductor's tabulated heat-rating current is 1.85 A. Review transient load,
  headroom, capacitor bias and fault current; see [sourcing review](../hardware/kicad/SOURCING.md).
- A local TLV74318 supplies the proposed optical 1.8 V rail, following the exact
  PAW3950 reference design and sequencing requirements.
- Size decoupling and bulk capacitance after inrush/transient analysis. Define
  grounding, current return paths and reverse-current protection.

Both [DRV8231A](https://www.ti.com/product/DRV8231A) and
[DRV8316](https://www.ti.com/product/DRV8316) specify a 4.5 V minimum operating
supply. A nominal 5 V rail needs cable-drop and transient validation.

## Actuator budget

Elastic paddles provide passive return. The custom button coils apply brief
resistance/assistance pulses, with zero commanded current between effects and
after a click while the button remains held. This eliminates continuous return
current, not driver quiescent current or the need to budget repeated clicks.

The [button prototype plan](../mechanical/button-mechanisms/README.md) targets
0.2-0.4 N peak electromagnetic force with pulses lasting a few milliseconds.
The custom magnetic circuit has no measured force constant: do not reuse the
industrial actuator's force/current conversion. Measure force versus current,
gap, travel and temperature, including paddle leverage and any unpowered yoke
attraction. Reverse voltage does not instantaneously reverse inductive current.

Wire gauge, turns, resistance, inductance and peak current remain TBD. The early
4-8 ohm and 0.5-1 A suggestions are not validated specifications for the smaller
coil. At 5 V, even an ideal 8-ohm coil reaches only 0.625 A at steady state;
driver/cable losses and inductance reduce the available pulse current. Size the
winding and driver together from measured force and thermal requirements.

Set per-effect duration, repeat-rate, duty-cycle and current limits. End effects
on timeout even if a button is held or a sensor value stops changing. Budget
simultaneous button pulses and wheel effects against measured USB input demand.

Coil/phase current is not USB input current. Establish the budget from coil
resistance, duty cycle, driver losses, motor operation, logic consumption and
measured VBUS current. Reserve logic power and transient margin, then allocate
remaining power across all actuators. Do not authorize simultaneous maximum
effects using nominal part peak ratings.

Before enabling haptics, validate coil resistance, stroke, pulse duration,
temperature and force; wheel winding parameters, pole pairs and encoder offset;
VBUS droop, inrush, peak/average current and brownout margin. Account for
regenerative energy and specify its dissipation or storage path. Provide hardware
current limits, safe reset states and driver fault handling. Test shutdown on stale
sensing, control timeout, disconnect and suspend, plus magnetic crosstalk and drift.
For button drivers, fault handling must account for the absence of a fault-output
pin; define the external monitoring/shutdown circuit in the schematic. Verify
unpowered paddle return with the final magnet/yoke geometry and worst-case travel.
