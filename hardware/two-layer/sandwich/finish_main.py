"""Fill ground, join overlapping islands, and remove unused router fanout vias.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import argparse,json,sys
import pcbnew as p
from route_main import HERE,ROOT,xy,via,check
sys.path.insert(0,str(ROOT/'build/two-layer/python'))
sys.path.insert(0,str(ROOT/'hardware/common'))
from board_geometry import polygons
from shapely.geometry import Point
from shapely.ops import unary_union

def finish(name):
    path=HERE/name.lower()/(name+'.kicad_pcb');board=p.LoadBoard(str(path))
    # Direct small IC ground lands to copper; keep solder-wire pads thermal.
    for f in board.GetFootprints():
        if f.GetReference().startswith('U'):
            for pad in f.Pads():
                if pad.GetNetname()=='GND':pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
    modes=[]
    for z in board.Zones():
        if not z.GetIsRuleArea():
            modes.append((z,z.GetIslandRemovalMode()));z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_NEVER)
    board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones())
    ground={layer:unary_union([poly for z in board.Zones() if z.GetNetname()=='GND' and not z.GetIsRuleArea()
        and z.GetLayerSet().Contains(layer) for poly in polygons(z.GetFilledPolysList(layer))]) for layer in (p.F_Cu,p.B_Cu)}
    existing=[Point(*p.ToMM(t.GetPosition())) for t in board.GetTracks() if isinstance(t,p.PCB_VIA)]
    forbidden=[]
    for f in board.GetFootprints():
        for pad in f.Pads():
            shape=p.SHAPE_POLY_SET()
            for layer in (p.F_Cu,p.B_Cu):
                if pad.IsOnLayer(layer):pad.TransformShapeToPolygon(shape,layer,p.FromMM(.25),p.FromMM(.005),p.ERROR_OUTSIDE)
            forbidden.extend(polygons(shape))
    avoid=unary_union(forbidden+[q.buffer(.5) for q in existing])
    overlap=ground[p.F_Cu].intersection(ground[p.B_Cu]).buffer(-.25).difference(avoid)
    areas=list(overlap.geoms) if hasattr(overlap,'geoms') else [overlap]
    count=0
    for area in areas:
        if area.is_empty or area.area<.02:continue
        point=area.representative_point()
        if any(point.distance(v)<.65 for v in existing):continue
        via(board,'GND',(point.x,point.y),.45,.3);existing.append(point);count+=1
    for z,mode in modes:z.SetIslandRemovalMode(mode)
    board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones());p.SaveBoard(str(path),board)
    report=check(name)
    dangling={i['uuid'] for v in report['violations'] if v['type']=='via_dangling' for i in v['items']}
    removed=0
    for t in list(board.GetTracks()):
        if isinstance(t,p.PCB_VIA) and t.m_Uuid.AsString() in dangling:
            board.Remove(t);t.thisown=False;removed+=1
    if removed:
        board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones());p.SaveBoard(str(path),board);report=check(name)
    print(name,'ground stitches added',count,'unused vias removed',removed)
    return report
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('board',choices=['Lower','Upper']);finish(a.parse_args().board)
