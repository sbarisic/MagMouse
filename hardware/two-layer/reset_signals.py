"""Rip up Main logic routes for a clean two-layer route, preserving power/analog.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import pcbnew as p
from prepare import DEST, signature

path=DEST/'main/Main.kicad_pcb'
b=p.LoadBoard(str(path))
before=signature(b)
preserve={'GND','+3V3','ACT_5V','PWR_5V','VBUS_USB','MCU_USB_DM','MCU_USB_DP',
          'USB_DM','USB_DP','HALL_L','HALL_M','HALL_R','ADC_DECAP',
          'BTN_L_ISENSE','BTN_M_ISENSE','BTN_R_ISENSE',
          'BTN_L_VREF','BTN_M_VREF','BTN_R_VREF','ACT_VMON',
          'USB_IMON_BUF','USB_IMON_ADC','BUCK_SW','OPT_1V9','OPT_3V3',
          'OPT_VDDPIX','OPT_RAMP_CT','OPT_LED_P'}
removed=0
for t in list(b.GetTracks()):
    n=t.GetNetname()
    if n not in preserve and not any(s in n for s in ('COIL','OUT1','OUT2')):
        b.Remove(t)
        t.thisown=False
        removed+=1
assert signature(b)==before
b.BuildConnectivity()
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(path),b)
print('Removed',removed,'logic tracks/vias; preserved power, USB and sensing')
