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

- Protected VBUS feeds motor/voice-coil drivers and the logic converter.
- A candidate TLV62569 or TPS62A0569 generates 3.3 V; choose one after checking
  transient load, headroom, thermals, and external components.
- A local TLV74318 supplies the proposed optical 1.8 V rail, following the exact
  PAW3950 reference design and sequencing requirements.
- Size decoupling and bulk capacitance after inrush/transient analysis. Define
  grounding, current return paths and reverse-current protection.

Both [DRV8874](https://www.ti.com/product/DRV8874) and
[DRV8316](https://www.ti.com/product/DRV8316) specify a 4.5 V minimum operating
supply. A nominal 5 V rail needs cable-drop and transient validation.

## Actuator budget

The notes estimate a voice-coil force constant of 0.97 N/A: a 0.5 N request implies
approximately 0.52 A of coil current. This is a preliminary calculation pending
the exact actuator datasheet and mechanism measurements. Proposed 0.3-0.7 A normal
pulses and approximately 1 A strong effects are experimentation targets, not limits
that have been configured or validated.

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
