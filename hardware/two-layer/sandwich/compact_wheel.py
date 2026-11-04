"""Trim the Wheel variant to 55 x 60 mm without moving components or signal routes.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import hashlib
import json
import sys
import pcbnew as p

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'build/two-layer/python'))
from shapely.geometry import Point, box

WIDTH,HEIGHT=55.0,60.0


def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))


def main():
    path=HERE/'wheel/Wheel.kicad_pcb'
    before=path.read_bytes()
    board=p.LoadBoard(str(path))
    assert board.GetCopperLayerCount()==2
    old=p.SHAPE_POLY_SET();assert board.GetBoardPolygonOutlines(old,False)
    old_size=tuple(p.ToMM(old.BBox().GetSize()))
    assert old_size in ((80.0,75.0),(WIDTH,HEIGHT)),old_size
    if old_size==(WIDTH,HEIGHT):
        print('Wheel already measures 55 x 60 mm');return
    scratch=ROOT/'build/sandwich';scratch.mkdir(exist_ok=True)
    backup=scratch/'Wheel-before-compact.kicad_pcb'
    if not backup.exists():backup.write_bytes(before)
    outline=box(0,0,WIDTH,HEIGHT)
    removed=[]
    # Remove only isolated stitching in the discarded margin. All other copper
    # primitives must already fit within the new edge clearance.
    copper_before={}
    for track in list(board.GetTracks()):
        b=track.GetBoundingBox();x,y=p.ToMM(b.GetPosition());w,h=p.ToMM(b.GetSize())
        bounds=box(x,y,x+w,y+h)
        if outline.buffer(-.3).covers(bounds):
            copper_before[str(track.m_Uuid.AsString())]=(x,y,w,h,track.GetNetname())
            continue
        assert isinstance(track,p.PCB_VIA) and track.GetNetname()=='GND'
        assert not outline.intersects(bounds), 'Only ground stitching outside the new board may be removed'
        removed.append({'uuid':str(track.m_Uuid.AsString()),'position_mm':p.ToMM(track.GetPosition())})
        board.Remove(track);track.thisown=False
    assert len(removed)==2
    for f in board.GetFootprints():
        b=f.GetBoundingBox(False,False);x,y=p.ToMM(b.GetPosition());w,h=p.ToMM(b.GetSize())
        assert outline.covers(box(x,y,x+w,y+h)),f.GetReference()
    edges=[d for d in board.GetDrawings() if d.GetLayer()==p.Edge_Cuts]
    assert len(edges)==4
    points=[(0,0),(WIDTH,0),(WIDTH,HEIGHT),(0,HEIGHT)]
    for edge,a,b in zip(edges,points,points[1:]+points[:1]):
        edge.SetStart(xy(*a));edge.SetEnd(xy(*b))
    for zone in board.Zones():
        assert not zone.GetIsRuleArea() and zone.GetNetname()=='GND'
        zone.Outline().RemoveAllContours();zone.Outline().NewOutline()
        for x,y in points:zone.Outline().Append(p.FromMM(x),p.FromMM(y))
    board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones())
    p.SaveBoard(str(path),board)
    saved=p.LoadBoard(str(path));shape=p.SHAPE_POLY_SET()
    assert saved.GetBoardPolygonOutlines(shape,False)
    assert tuple(p.ToMM(shape.BBox().GetSize()))==(WIDTH,HEIGHT)
    assert saved.GetCopperLayerCount()==2
    copper_after={}
    for track in saved.GetTracks():
        b=track.GetBoundingBox();x,y=p.ToMM(b.GetPosition());w,h=p.ToMM(b.GetSize())
        copper_after[str(track.m_Uuid.AsString())]=(x,y,w,h,track.GetNetname())
    assert copper_after==copper_before
    report={'old_dimensions_mm':old_size,'dimensions_mm':[WIDTH,HEIGHT],
            'area_reduction_percent':45,'copper_layers':2,'removed_margin_ground_vias':removed,
            'all_remaining_tracks_and_vias_unchanged':True,
            'before_sha256':hashlib.sha256(before).hexdigest(),
            'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (HERE/'wheel-size.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
