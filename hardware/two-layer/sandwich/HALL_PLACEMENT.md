# Hall sensor placement

The three sensor centres follow the marked regions in the user's top-copper
image. Coordinates are millimetres in the individual Upper board's top view;
use the same orientation when stacking Lower and Upper.

| Button | Sensor | X | Y | Rotation | ADC input |
| --- | --- | ---: | ---: | ---: | --- |
| Left | U7 | 17.50 | 11.00 | 0° | U10 AIN0 / HALL_L |
| Middle | U8 | 35.50 | 12.25 | 180° | U10 AIN1 / HALL_M |
| Right | U9 | 54.25 | 11.75 | 0° | U10 AIN2 / HALL_R |

C16, C17 and C18 move with their sensors and retain local supply bypassing.
C88 moves to (31.80, 4.00) mm to clear the centre sensor's bypass capacitor.
U8's in-plane rotation keeps the perpendicular magnetic sensing axis and
places its supply pin toward C17. Channel names, pin connections and component
values are unchanged.

The former J104.3 position overlapped the middle mark. Matching PWR_5V wire
pads J103.3 and J104.3 move together to (43.00, 2.00) mm. Their net and pin
number are unchanged; see [the wiring map](WIRE_MAP.md).
Upper's front-right panel tab moves 3 mm to x = 48.75 mm to clear the new
power-pad routing. Board outlines, mounting holes and panel positions stay fixed.

The wire array consists of separate solder lands with no connector body between
them. The assembly-spacing check measures the same 2 mm gap to each actual
land rather than to an imaginary body spanning the array.

Align one moving magnet with each new sensor centre in the mechanism CAD.
Check released/pressed clearance, polarity, usable field range and repeatable
calibration on the assembled device. This placement update does not constitute
physical magnet or button-travel validation.

The saved KiCad boards and shared wire-pad footprint are authoritative.
`hall-relocation.json` records the explicit changes; the one-time placement
migration refuses replay. Historical placement baselines remain unchanged.

`validate_hall.py` checks the three channel assignments, sensor coordinates,
local bypass paths without vias, matched power-pad coordinates, and short
power-feed paths. It also invokes the independent routing release checks,
including native DRC/parity and USB ground coverage.
