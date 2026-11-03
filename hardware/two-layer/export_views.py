"""Export review-only SVGs from the saved two-layer boards.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import subprocess
import sys
from prepare import DEST

cli=Path(sys.executable).with_name('kicad-cli.exe')
out=DEST/'review';out.mkdir(exist_ok=True)
for name in ('Main','Wheel','Encoder'):
    board=DEST/name.lower()/(name+'.kicad_pcb')
    for view,layers in [('front','F.Cu,Edge.Cuts'),('back','B.Cu,Edge.Cuts'),
                        ('placement','F.Fab,Edge.Cuts')]:
        subprocess.run([str(cli),'pcb','export','svg','--layers',layers,
            '--mode-single','--page-size-mode','2','--exclude-drawing-sheet',
            '--output',str(out/(name+'-'+view+'.svg')),str(board)],check=True)
