"""Apply reviewed ground repairs and remove native-DRC dangling vias.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import argparse
import json
import pcbnew as p
from prepare import DEST

ap=argparse.ArgumentParser()
ap.add_argument('board')
ap.add_argument('--drc',required=True)
args=ap.parse_args()
path=DEST/args.board.lower()/(args.board+'.kicad_pcb')
b=p.LoadBoard(str(path))
report=json.load(open(args.drc))
ids={v['items'][0]['uuid'] for v in report['violations'] if v['type']=='via_dangling'}
for t in list(b.GetTracks()):
    if isinstance(t,p.PCB_VIA) and t.m_Uuid.AsString() in ids:
        b.Remove(t);t.thisown=False
if args.board=='Wheel':
    # This top island grounds C54/R145. The opposite fill was initially removed
    # as an unanchored island; seed it before running finish_copper again.
    position=p.VECTOR2I(p.FromMM(43.25),p.FromMM(10.5))
    if not any(isinstance(t,p.PCB_VIA) and t.GetPosition()==position for t in b.GetTracks()):
        via=p.PCB_VIA(b);via.SetPosition(position)
        via.SetWidth(p.FromMM(.45));via.SetDrill(p.FromMM(.2))
        via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu)
        via.SetNetCode(b.FindNet('GND').GetNetCode());b.Add(via)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(path),b)
