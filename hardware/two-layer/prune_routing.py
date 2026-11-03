"""Discard conflicting/orphaned translated copper before re-routing.
Never removes pads or relaxes rules. This is not a post-route DRC fixer.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import argparse,json
import pcbnew as p
from prepare import DEST,signature

ap=argparse.ArgumentParser();ap.add_argument('board');ap.add_argument('drc');args=ap.parse_args()
path=DEST/args.board.lower()/(args.board+'.kicad_pcb')
b=p.LoadBoard(str(path));before=signature(b)
report=json.load(open(args.drc))
ids={i['uuid'] for v in report['violations'] for i in v['items']}
count=0
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in ids:b.Remove(t);t.thisown=False;count+=1
assert signature(b)==before
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
print('Pruned',count,'legacy tracks/vias; connections must be re-routed')
