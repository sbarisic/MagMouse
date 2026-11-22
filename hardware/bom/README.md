# Current component inventory

The [three-board BOMs](../two-layer/sandwich/quote-package/) and
[combined BOM](../two-layer/sandwich/quote-package/combined-BOM.csv) are the
current PCB purchasing lists. Motor and mechanical items are ordered separately.

| Item | Current requirement |
| --- | --- |
| Scroll motor | TSL/SteadyWin GB1806 with integrated AS5048A SPI encoder |
| Separate encoder board/magnet | Removed; do not purchase MA735 or a separate encoder magnet |
| Encoder power | U28 TPS22919, U42 TLV75533PDBVR; regulated supply shared with U33 |
| Wheel driver | DRV8316R, current sensing and autonomous brake retained |
| Buttons | Three passive plastic click mechanisms, Hall sensors and sensing magnets |
| Bottom test pads | All 37 removed; six top test pads retained |
| Optical assembly | PMW3360DM-T2QU and LM19-LSI lens; physical acceptance pending |
| Harnesses | Main stack and Wheel: 19 wires each; integrated encoder uses Lower J6 |

See [encoder integration](../two-layer/sandwich/ENCODER_INTEGRATION.md) for
the exact motor option, wiring, power allocation and interface requirements.
The former button-coil and separate-encoder inventories remain in Git history.
Supplier stock, assembly acceptance, harness lengths and enclosure fit remain
unverified; BOM exports do not place an order.
