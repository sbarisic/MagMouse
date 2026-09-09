# Optical sourcing and reference review

Checked 2026-09-09. **PAW3950 remains the selected target, but its circuit and
optical footprint are not frozen.** No sensor substitution has been made.

## What can be sourced

| Option | Evidence found | Remaining obstacle |
| --- | --- | --- |
| PAW3950DM-T5QU | [JLC C9900186384](https://jlcpcb.com/partdetail/JLCPCBAssembly-PAW3950DMT5QU/C9900186384), DIP16, wave soldering | Live page shows zero stock, unavailable for purchase, and offers consignment. No verified bare-sensor/lens supplier or exact manufacturer reference obtained. |
| PAW3395DM-T6QU | [JLC C9900026834](https://jlcpcb.com/partdetail/JIALICHUANGSMT-PAW3395DMT6QU/C9900026834), PDIP-16, wave soldering; [LCSC C41346211](https://www.lcsc.com/product-detail/C41346211.html); public PixArt general datasheet | LCSC shows out of stock. JLC inventory was not established. Sensor procurement, initialization documentation and lens drawing are still needed. |
| PMW3389DM-T3QU | [JLC C9900026115](https://jlcpcb.com/partdetail/JLCPCBAssembly-PMW3389DMT3QU/C9900026115), PDIP-16, wave soldering | Listing alone does not establish purchasable stock or lens inclusion. This would require a separate circuit, firmware and optics review. |
| PMW3360 breakout for bench work | [Joe's Sensors and Sundry](https://lectronz.com/products/pmw3360-motion-sensor) lists an assembled, tested board with lens at USD31.50 | Currently out of stock. This is an external development board, not a JLC-assembled motherboard part. |

The PAW3950 page displays an estimated USD0.0204 alongside its consignment
notice. **Do not use this as the sensor material price.** A catalog entry under
“JLCPCB Assembly” is not evidence that JLC can sell us the sensor. No stock has
been reserved and no vendor has been contacted.

PAW3395 is the first alternative to investigate because a public manufacturer
datasheet exists, not because stock or full firmware support has been secured.
The [PixArt general datasheet hosted by LCSC](https://datasheet.lcsc.com/lcsc/2504101957_PixArt-PAW3395DM-T6QU_C41346211.pdf)
names LM19-LSI and LOAE-LSI1 as separate optical parts. Neither the JLC nor LCSC
sensor listing establishes that a lens is included.

If changing assembly houses is preferable, [PCBWay offers partial turnkey and
consigned assembly](https://www.pcbway.com/assembly-faq.html): we may supply the
sensor while they source other parts. This does not resolve the missing sensor
supplier, reference circuit or optical dimensions. JLC also offers
[consignment](https://jlcpcb.com/help/article/245-how-to-consign-parts-to-jlcpcb).
Optical aperture protection, soldering fixture, no-wash process, sensor height
and lens installation must be explicitly covered by the assembly quote.

## Public PAW3950 variant evidence

Inspected [badjeff/paw3395-pcb](https://github.com/badjeff/paw3395-pcb/tree/b71e346fc04ef18c26e0e8638ce0333395d41a14)
at commit `b71e346fc04ef18c26e0e8638ce0333395d41a14`. Its README describes a
PAW3950 variant and includes a photograph. The source is CERN-OHL-P-2.0;
retain its license and modification notices if adapting its design later.
No upstream schematic or footprint has been copied into the project library.

The author's changes are specific: omit R1, short R2, and add 2.2uF between
sensor pins 2 and 3. Tracing the upstream KiCad netlist shows R1 is a MISO
pull-up and R2 feeds LED_P from the 1.8V rail. Thus these changes must not be
misread as a reset pull-up change. The base symbol labels pin 2 as NC, so that
symbol cannot simply be renamed PAW3950 and declared manufacturer-verified.

This evidence supports a possible experimental breakout. It does not establish
the PAW3950 pin definitions, supply limits, sequencing, reset circuit, serial
timing, initialization rights or optical stack tolerances. The public PAW3395
datasheet cannot fill those gaps for a different sensor.

## Next optical deliverable

Obtain a supplier-confirmed sensor/lens pair and the following documents before
integrating the optical circuit into the motherboard:

- Exact PAW3950DM-T5QU pinout, recommended supply circuit, voltage tolerances,
  power/reset sequencing and SPI electrical/timing limits.
- Initialization/register information and terms for distributing any required
  firmware data. Open driver code alone does not establish rights to a blob.
- Exact lens drawing/revision, PCB aperture and locating features, sensor seating
  height, lens-to-surface working distance and tolerances including feet/base.
- Sample quantity, genuine-part provenance, packaging, lead time, price and
  acceptance by the assembly house; quote the lens separately.

The current OPT_CTRL, CS_PAW, SPI2 and PAW_MOTION_N allocation remains reserved.
No optical aperture, assumed working height or enlarged board outline was added.
Continue IMU/RGB and mechanical parameter collection while this evidence is open.
Changing the wheel control update rate alone does not widen a fixed PWM
low-side sampling window; the wheel timing acceptance work remains unchanged.
