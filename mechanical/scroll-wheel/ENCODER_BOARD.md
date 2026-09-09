# Upright wheel encoder board

The user selected a separate upright MA735 board on 2026-09-09. Its
[KiCad project, routed PCB and harness specification](../../hardware/encoder/README.md)
are now implemented. The provisional board measures **14 x 18 mm**, nominal
1.6 mm thick. Design the wheel/shaft support and shell around the motherboard
and this interface after checking the purchased mechanical parts.

For the intended horizontal, left-to-right axle, the encoder board stands in
the YZ plane beside one shaft end. Its sensor faces the shaft magnet along X.
Set its height from the actual axle centre. A rigid support must maintain the
magnet gap and alignment without putting middle-click loads through the PCB.
Verify the chosen magnet and motor field using the
[MPS MA735 datasheet](https://www.monolithicpower.com/en/documentview/productdocument/index/version/2/document_type/Datasheet/lang/en/sku/MA735GGU/)
and measurements; orientation alone does not establish correct sensing.

## Implemented interface

U27 and C62 are on the daughterboard. U28, its supply/discharge components,
U29 outgoing SPI buffer and U25 return buffer remain on the motherboard.
J6 and J7 use matching eight-pin JST SH right-angle headers, C160407. Their
pin-to-pin harness carries switched power, four buffered SPI signals and three
separate ground conductors. No new GPIO or index output is allocated.

The [electrical README](../../hardware/encoder/README.md) gives the complete
pin table, connector/harness parts and board coordinates. The proposed 50 mm
wire length is a prototype target, not a verified signal-integrity limit.
Verify operation at the planned 10 MHz clock; add source termination only if
the waveform/loading review calls for it.

## Mechanical work still needed

1. Fit the purchased wheel, GB1806 variant, bearings, shaft and magnet. Confirm
   sensor centre height, magnet orientation/gap and motor-field interference.
2. Design a rigid support around the provisional side clip lands. There are no
   mounting holes yet. Maintain access to the sensor-facing surface and prevent
   wheel or middle-click force from bending the board.
3. Reserve space for both mating housings, cable bends and strain relief. Check
   J6 access near the motherboard's front edge against USB and the shell.
4. Check cable continuity and power-off behaviour, then measure angle stability
   through rotation and button/coil operation before freezing the assembly.

The motherboard wheel reservation is still an unverified planning envelope.
Zero encoder ERC/DRC/unconnected items establish the current electrical CAD
checks, not axle fit or magnetic performance. Fabrication release remains open.
