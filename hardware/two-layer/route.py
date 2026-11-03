"""Export/import a two-layer routing session without touching four-layer boards.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import argparse
import re
import pcbnew as pcb
from prepare import ROOT, DEST, signature


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board', choices=['Main', 'Wheel', 'Encoder'])
    ap.add_argument('action', choices=['export', 'import'])
    args = ap.parse_args()
    name = args.board
    path = DEST/name.lower()/(name+'.kicad_pcb')
    scratch = ROOT/'build/two-layer'/name
    b = pcb.LoadBoard(str(path))
    before = signature(b)
    if args.action == 'import':
        assert pcb.ImportSpecctraSES(b, str(scratch/(name+'.ses')))
        assert signature(b) == before, 'Router changed pad net assignments'
        b.BuildConnectivity()
        pcb.ZONE_FILLER(b).Fill(b.Zones())
        pcb.SaveBoard(str(path), b)
    else:
        assert pcb.ExportSpecctraDSN(b, str(scratch/(name+'.dsn')))
        dsn = scratch/(name+'.dsn')
        text = dsn.read_text()
        # Permit movement of digital/control traces; freeze power, analog and USB.
        movable = ('SPI', 'PWM', 'CS_', 'RUN_', 'FAULT', 'MCU_EN', 'CC_OUT',
                   'BTN_', 'IMU_INT', 'PAW_MOTION', 'PAW_RESET', 'LED_DATA')
        sensitive = ('ISENSE', 'VREF', 'OUT', 'COIL', 'USB_', 'HALL', 'GND')
        def wire(m):
            block = m[0]
            net = re.search(r'\(net ([^)]*)\)', block)
            if net and any(t in net[1] for t in movable) and not any(t in net[1] for t in sensitive):
                block = block.replace('(type route)', '(type normal)')
            return block
        text = re.sub(r'^    \((?:wire|via) .*?\(type route\)\)', wire, text, flags=re.M|re.S)
        text = text.replace('(width 250)', '(width 150)')
        # Use the already-supported small through-via geometry for signal routing.
        start = text.index('(class kicad_default')
        end = text.find('(class ', start+1)
        if end < 0:
            end = text.index('(wiring')
        text = text[:start]+text[start:end].replace(
            '(use_via "Via[0-1]_600:300_um")',
            '(use_via "Via[0-1]_450:200_um")')+text[end:]
        dsn.write_text(text)


if __name__ == '__main__':
    main()
