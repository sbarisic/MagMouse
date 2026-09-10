# Upright wheel encoder

Revision 0.8, 2026-09-09, KiCad 10.0.6. The separate **14 x 18 mm** encoder PCB
is fully routed. ERC, physical DRC and schematic parity pass; there are zero
unconnected items. These checks do not establish mechanical fit or operation.
**This is a prototype design, not a fabrication release.**

Open [Encoder.kicad_pro](Encoder.kicad_pro), then its
[schematic](Encoder.kicad_sch) and [PCB](Encoder.kicad_pcb). Keep the repository
directory structure: the library tables reference the shared MagMouse libraries
in `../kicad`. U27 and C62 have been removed from the motherboard project.

## Parts and connection

The encoder assembly BOM contains U27 MA735GGU-P, C62 local 1 uF bypass and
J7. The motherboard BOM contains J6, the switched encoder supply U28 and the
existing U29/U25 SPI buffers. No ESP32 pin allocation changed.

Both connectors use **JST SM08B-SRSS-TB(LF)(SN)**, an eight-pin, 1 mm pitch,
right-angle SMT SH header, [JLCPCB C160407](https://jlcpcb.com/partdetail/JST-SM08B_SRSS_TB_LF_SN/C160407).
The catalog listing was checked on 2026-09-09; refresh stock and assembly
eligibility when quoting. Use KiCad's standard
`Connector_JST:JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal` footprint.

| Motherboard J6 | Encoder J7 | Signal |
| --- | --- | --- |
| 1 | 1 | ENC_3V3, switched supply |
| 2 | 2 | GND |
| 3 | 3 | ENC_SCLK_LOCAL, buffered clock |
| 4 | 4 | GND |
| 5 | 5 | ENC_MOSI_LOCAL, buffered data |
| 6 | 6 | ENC_CS_LOCAL, buffered select |
| 7 | 7 | GND |
| 8 | 8 | ENC_MISO_LOCAL, return to U25 |

[harness.json](harness.json) is the machine-checked wiring specification.
Use eight separate conductors, including all three ground contacts. Check
continuity by pin number; connector appearance and wire colours do not prove
correct ordering. Do not substitute an unverified mirrored cable.

The harness needs two **SHR-08V-S-B** housings and sixteen **SSH-003T-P0.2-H**
contacts. JST specifies AWG 28-32 wire with 0.4-0.8 mm insulation diameter for
these contacts. The prototype wire-length target is **50 mm**, subject to fit
and waveform measurements. Housings, crimp contacts, wire and harness assembly
are separate from the two SMT assembly BOMs. See the
[JST SH drawing and contact specification](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf).

## Placement and mechanical datums

The two-layer board has nominal 1.6 mm thickness and bounds X=50..64,
Y=50..68 mm in KiCad. All three components are on the front.

- U27 centre: (57,55.5) mm, 7 mm from the left edge and 5.5 mm from the top.
  The front of the sensor faces the shaft magnet.
- C62 centre: (56.8,52.2) mm. Its supply-pad-to-VDD route is 1.525 mm.
- J7 centre: (57,64.5) mm. Its mating direction is toward +Y, past the lower edge.
- Dwgs.User lines at X=51.5/62.5, Y=50..60 reserve provisional side clip lands.
  There are no mounting holes. The mating housing, cable bend and support need
  separate clearance beyond the PCB outline.

Signals use 0.15 mm tracks; the incoming supply uses 0.25 mm tracks.
Ground pours cover both copper layers with local return and stitching vias.
Through vias are 0.60/0.30 mm. The project uses 0.15 mm default clearance and
a 0.127 mm absolute minimum; final stackup and stencil review remain open.

For the proposed horizontal axle the board stands beside a shaft end. Sensor
height, magnet dimensions/gap and support geometry must follow the actual
wheel assembly. The 14 x 18 mm outline is provisional. A routed board does not
prove it fits the motherboard wheel reservation. See
[mechanical integration](../../mechanical/scroll-wheel/ENCODER_BOARD.md) and the
[MA735 datasheet](https://www.monolithicpower.com/en/documentview/productdocument/index/version/2/document_type/Datasheet/lang/en/sku/MA735GGU/).

## Reproduce the checks

Run from the repository root with Python 3 and KiCad 10:

    python hardware/kicad/export_review.py
    python hardware/kicad/export_review.py --schematic hardware/encoder/Encoder.kicad_sch
    python hardware/kicad/verify_encoder.py
    python hardware/kicad/test_encoder_checks.py
    python hardware/kicad/verify_wheel.py
    python hardware/kicad/test_wheel_checks.py
    python hardware/kicad/export_pcb_review.py
    python hardware/kicad/export_pcb_review.py --board hardware/encoder/Encoder.kicad_pcb --require-routed

Encoder outputs go to `build/encoder-review` and `build/encoder-pcb-review`;
motherboard outputs remain in their existing review directories. Each project
gets a separate draft BOM. The wheel checker reads both netlists. The encoder
checker validates the connector identities, switched/buffered boundaries, pin
ordering, local bypass and component split against the harness specification.
Eight encoder tests include seven injected faults. Five wheel tests also pass.

The motherboard has 317 footprints. Its [actuator distribution routing pass](../pcb/ACTUATOR_DISTRIBUTION_LAYOUT.md)
reduces native unrouted connections to 247. Physical DRC and parity pass, but
board-wide routing remains open. Before releasing either
board, verify cable continuity, 10 MHz SPI waveforms under concurrent operation,
power-off isolation, angle repeatability, magnetic interference and mechanical
retention. No Gerbers or placement files are released for ordering.

Motherboard J6 is now rotated 180 degrees at (113, 103.5) mm and mates toward
minus Y, the front edge. Check shell/USB clearance and harness bend radius.
Encoder J7 and the pin-to-pin harness map are unchanged.
