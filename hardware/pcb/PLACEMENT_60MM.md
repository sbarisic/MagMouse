# 60 mm motherboard placement

2026-09-09, KiCad 10.0.6. This is a component floorplan for routing review.
It is not a routed motherboard or a manufacturing release. The counts below
record the original widening pass. The subsequent encoder split is documented
in the final section; use the [motherboard README](README.md) for current totals.

## Geometry and placement

The user approved a maximum motherboard width of 60 mm and a separate upright
encoder board. The motherboard now measures **60 x 95 mm**, with 3 mm corner
chamfers and nominal 1.6 mm thickness. Bounds are X=95..155, Y=100..195 mm.
The additional 5 mm on each side keeps the USB connector, ESP32 and optical
centre fixed. The PCB still uses four copper layers.

There are **314 footprints inside the motherboard outline**: 270 BOM parts,
43 test pads and the motor's J5 wire pads. U27 and C62 are the only two
footprints outside it, in a labelled encoder-board planning group. All
motherboard BOM parts remain on F.Cu. TP35/TP36 and TP40..TP43 moved to B.Cu,
bringing the underside test-pad count to 39. These pads need no soldered parts.

| Block | Location and remaining routing work |
| --- | --- |
| U21 wheel driver | (143,153) mm, right of the optical sensor; charge-pump and VM capacitors surround it. Review VM/ground loops, exposed-pad thermal vias and phase exits before routing. |
| U23 ADC2 | (141,165) mm, below U21; phase-current filters and supply capacitors are adjacent. Keep the CSA paths away from phase and brake copper. |
| U22/U24/U25/U26 | PWM gating and SPI isolation have provisional positions. U26 is beside the MCU; review the complete dedicated ADC2 SPI path and return reference before committing to these locations. |
| U28/U29 | Encoder power switch and outgoing SPI buffer remain on the motherboard, near the wheel region. U25 retains the MISO return function. |
| J5 | (137,119) mm, beside the wheel reservation. The phase traces must run from U21 toward these pads; allow access and strain relief for three motor wires. |
| R121..R124 | X=152 mm, Y=152/163/174/185 mm. The four brake resistors use the new right edge, with separation between bodies. This spacing does not establish thermal performance. |
| Q5 and brake control | Q5 is beside the resistor bank. U30/U31 and their bias/feedback parts occupy the left rear. Tighten the comparator divider, hysteresis and filter connections, and review the long rail-sense/gate paths before routing. |
| U32 IMU | (129.5,168.75) mm, behind the optical group. Its local bypass parts are placed; coordinate this position with screw locations and board strain. |
| D5 RGB | (127.25,111.75) mm, near USB for a future light pipe; U33/U34 provide its local power/interface. |

Original left-side circuit groups moved 5 mm left, and front-right groups moved
5 mm right. Internal positions within those groups were largely retained;
selected bias parts moved to make room for the added circuitry. The optical
power switch/LDO moved left of U35. U35, its close bypass capacitors, the USB
connector and the ESP32 retained their positions and orientations.

## Mechanical boundaries

The optical aperture remains a drawing and copper/pad/via keepout. No physical
opening was cut. The underside lens envelope remains 20 x 22 mm and the
optical centre remains (125.5,157.5) mm. The original wheel keepout remains
11.5 x 23 mm. Its label now includes the upright encoder; this small reservation
is not a proven envelope for the motor, wheel, bearings and encoder together.

See the [encoder-board plan](../../mechanical/scroll-wheel/ENCODER_BOARD.md).
U27/C62 are still electrically represented in the common schematic/PCB; the
daughterboard split and connectors have not been added. They must not be
mistaken for extra motherboard assembly parts in an order export.

Mounting holes, wheel supports, paddle magnets, cable bends and the shell remain
to be fitted. Existing Hall positions are provisional. Do not freeze them from
this floorplan without measuring travel and magnetic interference.

## Verification and next pass

Native KiCad physical DRC and schematic parity pass with zero reported issues.
No new rule exclusions were added. All 316 footprints retain their schematic
paths, footprint assignments and pad nets. The board has no tracks or vias;
native connectivity still reports **792 unrouted connections**. The DRC JSON
list returns 499 entries and is not the full connectivity count.

After the encoder interconnect pass below, refine the
critical power/analog/SPI placement with actual escape routes. Select the
production stackup before calculating USB geometry. Brake cooling, motor
feedback timing, optical samples and final mechanics remain acceptance gates.

## Encoder split follow-up, revision 0.8

U27 and C62 have moved into the [separate encoder project](../encoder/README.md).
J6 was added at (113,103.5) mm, rotation 0 degrees, on the front. C24 moved to
(106.75,108.5) mm and R110 to (118.75,109.5) mm, both at 90 degrees. TP34 moved
to B.Cu at its existing (118,103) mm position to clear the connector. The other
motherboard footprint positions, pad nets, optical datum and outline remain as
in the widening pass. There are now **315 motherboard footprints**, all inside
the outline, with 40 back test pads and three front test pads.

The connector replaces the two planning footprints, giving 271 motherboard BOM
parts and **790 native unrouted connections**. Physical DRC and parity still
pass with zero issues. The separate three-part encoder PCB is fully routed with
zero unconnected items. Cable access, axle fit and mechanical retention remain
unverified; routing and fit acceptance for the motherboard remain open.
