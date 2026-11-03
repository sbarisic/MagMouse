"""Label the experimental variant and declare a nominal two-layer stack.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import re
import pcbnew as p
from prepare import DEST

STACK='''\t\t(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen"))
\t\t\t(layer "F.Paste" (type "Top Solder Paste"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4 - nominal, confirm with fabricator") (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen"))
\t\t\t(copper_finish "ENIG")
\t\t\t(dielectric_constraints no)
\t\t)
'''

for name in ('Main','Wheel','Encoder'):
    path=DEST/name.lower()/(name+'.kicad_pcb')
    b=p.LoadBoard(str(path))
    b.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
    if name!='Encoder' and not any(isinstance(d,p.PCB_TEXT) and '2L-A' in d.GetText() for d in b.GetDrawings()):
        text=p.PCB_TEXT(b);text.SetText(name+' 2L-A / EXPERIMENTAL')
        text.SetLayer(p.F_SilkS);text.SetTextSize(p.VECTOR2I(p.FromMM(1),p.FromMM(1)))
        text.SetTextThickness(p.FromMM(.15))
        text.SetPosition(p.VECTOR2I(p.FromMM(80 if name=='Main' else 30),p.FromMM(245 if name=='Main' else 66)))
        b.Add(text)
    p.SaveBoard(str(path),b)
    text=path.read_text()
    text=re.sub(r'^\t\t\(stackup\n.*?^\t\t\)\n','',text,flags=re.M|re.S)
    text=text.replace('\t(setup\n','\t(setup\n'+STACK,1)
    path.write_text(text,encoding='utf-8')
