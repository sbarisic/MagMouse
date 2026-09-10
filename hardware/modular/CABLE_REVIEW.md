# Main/wheel cable qualification brief

2026-09-10. Schematic pin numbers are defined. The user accepts possible
child-board damage after internal cable disconnection for this prototype.
Assume cables remain fully connected during operation. Disconnect, partial
insertion, open-return faults and hot-plug survival are outside acceptance.
Normal cable loading, mating fit, pin orientation and loaded timing remain
in scope. No dedicated protection is required solely for cable-disconnect faults.

## FFC candidate

Wurth **687630050002**, Type 1, is a concrete 30-contact/0.5 mm/50 mm candidate.
Its [manufacturer drawing](https://www.we-online.com/components/products/datasheet/687630050002.pdf)
specifies 0.3 +/-0.02 mm conductor width, 0.05 +/-0.01 mm conductor thickness,
15.5 mm cable width, 0.29–0.34 mm mating-end thickness and 4 +/-1 mm stripped
ends. Electrical limits include 0.5 A, 1.4 ohm/m conductor resistance and
20 milliohm contact resistance. The operating range starts at -30 C; this
candidate cannot support a -40 C assembly rating. The listed current rating
is at 25 C and needs derating review at other temperatures.

This is a **trial candidate**, not a frozen order MPN. The reviewed
[Hirose FH12 catalog, bottom-contact cable drawing](https://www.hirose.com/en/product/document?clcode=CL0586-0525-1-55&documentid=D31648_en&documenttype=Catalog&lang=en&productname=FH12-30S-0.5SH%2855%29&series=FH12)
requires at least 3.5 mm stripped length; Wurth's 4 +/-1 mm can be only 3 mm.
Hirose specifies total pitch span 14.5 +/-0.05 mm and width 15.5 +/-0.07 mm;
Wurth allows +/-0.08 mm for both. Thickness 0.29–0.34 mm fits Hirose's
0.30 +/-0.05 mm range. Nominal fit does not close these tolerance differences:
select a conforming alternative or establish sample/supplier acceptance before
ordering the harness. The connector footprint and placement can proceed.

## Physical contact order, now implemented

Both boards face component-side up, their bottom-contact headers face one
another, and the same-side-contact FFC runs flat without a twist. Looking down
on the board pair, one header's numbered pad row runs in the opposite direction
to the other. Therefore **J8.N connects to J9.(31-N)**. The previous same-number
assumption was corrected in the wheel schematic and machine contract.

J8 odd contacts and J9 even contacts are GND. For example, J8.2 clock reaches
J9.29; J8.30 +3V3 reaches J9.1; J8.1 GND reaches J9.30. J9 is rotated 180 degrees
in the wheel PCB (mouth toward its upper edge). The future main J8 must face
it in the assembly. Folding the cable with a different board orientation needs
a fresh contact-order check; never introduce a twist just to repair numbering.
Verify continuity against this mapping when the actual harness is available.
The separate JST power cable remains pin 1 to pin 1 and pin 2 to pin 2.

The manufacturer does not guarantee mixed-vendor mating reliability. Purchase
and assembly of the cable are separate from populating the JLCPCB board BOM.

## Connected return paths and excluded fault cases

J10/J11 use a separate ACT_5V/GND pair. The FFC also bonds board grounds at
15 contacts, so current divides between both harnesses even in normal use.
Opening the power GND diverts wheel load into the FFC. Local capacitors and
TVS do not eliminate this DC path.

At 2.02 A (the existing U13 nominal trip setting, **not** its guaranteed maximum
or a wheel operating budget), ideal equal sharing would be 135 mA/contact.
That number proves nothing about the highest-loaded contact. A partial insertion
with only one ground contact could expose it to the whole current until
protection reacts, above the candidate's 0.5 A rating. The split presently has
no independently qualified wheel-only feed limiter.

| Case | Prototype review status |
| --- | --- |
| Both cables fully seated | Measure return sharing, drop and connector temperature at allowed combined loads |
| Power GND open, ACT pin connected | Outside scope; possible damage accepted |
| Partial FFC insertion or damaged ground contacts | Outside scope; possible damage accepted |
| Signal cable absent | Outside scope; existing bias remains, survival unqualified |
| Power cable absent, signal cable present | Outside scope; survival unqualified |
| Both cables attached, USB power lost or rails switched | Review normal rail sequencing, reset and autonomous braking |
| Wheel stopped, source removed | Measure discharge; spinning motor invalidates the simple R146 time constant |

The fault arithmetic above is retained as information, not a release blocker
or evidence of survival. Do not add a dedicated wheel limiter or redesign the
interconnect solely to cover those excluded cases. Connector placement can
proceed after normal cable fit, pin numbering and routing needs are reviewed.
Existing pull resistors and local power parts remain fitted; they also support
startup defaults, rail stability and normal regeneration. Removing them would
be a separate circuit simplification, not necessary to adopt this scope.

## Timing bench sequence

The SPI3 report budgets the ADC plus forward/return buffer path at 28 ns under
datasheet loading. It excludes cable/board flight time, actual loading, receiver
setup and ESP32-S3 input sampling delay. No cable delay is invented from length
alone. The FFC changes signal return and crosstalk, as well as propagation time.

Start with motor disabled and 1 MHz register/data transfers. Characterize the
full cable at 10 MHz, then evaluate sample phase and 20 MHz. Probe clock at ADC2
and returned data at U25/ESP32; test concurrent PWM/SPI2 activity, supply corners,
and reset/power sequencing. Validate conversion start, channel ordering, stale
sample handling and the low-side acquisition window in firmware. The 10 MHz
nominal burst consumes 10 us of the proposed 12 us quiet window before software;
revise cadence/modulation if measured latency cannot fit. No waveform or FOC
acceptance is claimed by the static arithmetic.
