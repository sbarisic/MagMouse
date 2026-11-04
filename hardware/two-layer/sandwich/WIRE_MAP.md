# Proposed sandwich wire map

This is the exact endpoint map for the unrouted placement study. Wire gauge,
cut lengths and assembled stack height are not yet selected.

Both boards use the same top-view XY orientation; do not mirror the upper
board. Connect like-numbered pads. Upper pads can be soldered from underneath.
There are three shared GND wires: one in the signal array and two in the power array.

| Lower pad | Upper pad | Net | Role / direction |
| --- | --- | --- | --- |
| J101.1 | J102.1 | GND | Shared signal return |
| J101.2 | J102.2 | SPI_SCLK | Lower to Upper |
| J101.3 | J102.3 | SPI_MOSI | Lower to Upper |
| J101.4 | J102.4 | SPI_MISO | Upper to Lower; shared bus |
| J101.5 | J102.5 | ADC_CS | Lower to Upper |
| J101.6 | J102.6 | ACT_REQ | Lower to Upper |
| J101.7 | J102.7 | ACT_HEARTBEAT | Lower to Upper |
| J101.8 | J102.8 | SENS_REQ | Lower to Upper |
| J101.9 | J102.9 | CC_OUT1 | Lower to Upper |
| J101.10 | J102.10 | CC_OUT2 | Lower to Upper |
| J101.11 | J102.11 | VBUS_PRESENT_N | Upper to Lower |
| J101.12 | J102.12 | HALL_EN | Upper to Lower |
| J101.13 | J102.13 | ACT_DRIVE_EN | Upper to Lower / Wheel |
| J101.14 | J102.14 | MCU_EN | Shared reset: Lower pull-up; Upper fault sinks |
| J103.1 | J104.1 | GND | Shared power return |
| J103.2 | J104.2 | VBUS_USB | Lower to Upper |
| J103.3 | J104.3 | PWR_5V | Upper to Lower |
| J103.4 | J104.4 | +3V3 | Lower to Upper |
| J103.5 | J104.5 | GND | Shared power return |

## Pad coordinates

- Signal arrays J101/J102: 14 pins in two columns. Odd pins at x = 6.00 mm,
  even pins at x = 8.54 mm. Rows start at y = 42.00 mm with 2.54 mm pitch.
  Row 1 is pins 1/2; row 7 is pins 13/14 at y = 57.24 mm. Only pin 1 is GND.
- Power arrays J103/J104: five pins at y = 11.00 mm and x = 25.00, 30.08,
  35.16, 40.24 and 45.32 mm. Pins 1 and 5 are shared power grounds.
- Signal pads: 1.8 mm copper diameter / 0.8 mm finished-hole design value.
  Power pads: 2.4 mm copper diameter / 1.2 mm finished-hole design value.
  These are candidate geometries; verify actual wire fit and fabrication tolerances.

Raw VBUS goes up to the protection circuitry; protected PWR_5V returns to
the lower regulator; regulated +3V3 goes back up. ACT_5V stays on Upper and
feeds the existing Wheel power connector J10 from there.

Every original endpoint of every boundary net is listed in partition.json.
USB data/CC, Hall outputs and ADC analog inputs
do not cross this new interface.
