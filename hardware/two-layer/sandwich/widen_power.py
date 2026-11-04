"""Widen power escapes wherever actual pad/track geometry permits.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import sys,argparse,math,collections
import pcbnew as p
from route_main import HERE,ROOT,xy,check
sys.path.insert(0,str(ROOT/'build/two-layer/python'))
sys.path.insert(0,str(HERE.parent))
from finish_copper import polygons
from shapely.geometry import LineString,Point
from shapely.ops import unary_union

def widen(name):
    path=HERE/name.lower()/(name+'.kicad_pcb');board=p.LoadBoard(str(path));changed=collections.Counter()
    for net in ('VBUS_USB','PWR_5V','ACT_5V','+3V3','BUCK_SW','OPT_3V3','OPT_1V9','MA735_3V3','RGB_5V'):
        for layer in (p.F_Cu,p.B_Cu):
            obstacles=[]
            for z in list(board.Zones())+[z for f in board.GetFootprints() for z in f.Zones()]:
                if z.GetIsRuleArea() and z.GetDoNotAllowTracks() and z.GetLayerSet().Contains(layer):
                    obstacles.extend(polygons(z.Outline()))
            for f in board.GetFootprints():
                for pad in f.Pads():
                    if pad.GetNetname()==net or not pad.IsOnLayer(layer):continue
                    poly=p.SHAPE_POLY_SET();pad.TransformShapeToPolygon(poly,layer,0,p.FromMM(.001),p.ERROR_OUTSIDE)
                    obstacles.extend(polygons(poly))
            for t in board.GetTracks():
                if t.GetNetname()==net:continue
                if isinstance(t,p.PCB_VIA):obstacles.append(Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetWidth(layer))/2))
                elif t.GetLayer()==layer:obstacles.append(LineString([p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2))
            forbidden=unary_union(obstacles)
            for t in list(board.GetTracks()):
                if isinstance(t,p.PCB_VIA) or t.GetNetname()!=net or t.GetLayer()!=layer or p.ToMM(t.GetWidth())>=.749:continue
                start,end=map(lambda q:tuple(p.ToMM(q)),(t.GetStart(),t.GetEnd()));length=math.dist(start,end)
                old=p.ToMM(t.GetWidth());count=max(1,math.ceil(length/.3))
                pieces=[]
                for i in range(count):
                    a=tuple(start[k]+(end[k]-start[k])*i/count for k in (0,1));b=tuple(start[k]+(end[k]-start[k])*(i+1)/count for k in (0,1))
                    limit=2*(LineString([a,b]).distance(forbidden)-.151)
                    width=max(old,min(.75,math.floor(limit*1000)/1000))
                    pieces.append((a,b,width))
                if all(w<=old for a,b,w in pieces):continue
                board.Remove(t);t.thisown=False
                # Merge runs with equal widths to avoid gratuitous segmentation.
                runs=[]
                for a,b,w in pieces:
                    if runs and runs[-1][2]==w:runs[-1]=(runs[-1][0],b,w)
                    else:runs.append((a,b,w))
                for a,b,w in runs:
                    q=p.PCB_TRACK(board);q.SetNet(board.FindNet(net));q.SetLayer(layer);q.SetStart(xy(*a));q.SetEnd(xy(*b));q.SetWidth(p.FromMM(w));board.Add(q)
                changed[net]+=1
    board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones());p.SaveBoard(str(path),board)
    print('Widened',dict(changed));check(name)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('board',choices=['Lower','Upper']);widen(a.parse_args().board)
