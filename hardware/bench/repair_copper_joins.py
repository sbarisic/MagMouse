"""Audit cap-only copper contacts and add full-width centerline joins.

KiCad Python + Shapely. Net, layer, width, pad/via positions and USB pair
geometry are preserved. Reports are not fabrication acceptance without DRC,
the existing electrical screens, and exported-Gerber witness verification.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid
import pcbnew as p

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'build/bench-python'))
from shapely.geometry import Point,LineString,Polygon,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
USB={'USB_DP','USB_DM','MCU_USB_DP','MCU_USB_DM'}
TOL=.002

def uid(t):return t.m_Uuid.AsString()
def xy(v):return (v.x/1e6,v.y/1e6)
def line(t):return LineString([xy(t.GetStart()),xy(t.GetEnd())])
def capsule(a,b,width):return LineString([a,b]).buffer(width/2,quad_segs=64)
def polyset(poly):
    def ring(c):return [(c.CPoint(i).x/1e6,c.CPoint(i).y/1e6) for i in range(c.PointCount())]
    return unary_union([Polygon(ring(poly.Outline(i)),[ring(poly.Hole(i,j)) for j in range(poly.HoleCount(i))]) for i in range(poly.OutlineCount())])

def shape(item,layer):
    if type(item)==p.PCB_TRACK:return line(item).buffer(item.GetWidth()/2e6,quad_segs=64)
    if isinstance(item,p.PCB_VIA):return Point(xy(item.GetPosition())).buffer(item.GetWidth(layer)/2e6,quad_segs=64)
    poly=p.SHAPE_POLY_SET();item.TransformShapeToPolygon(poly,layer,0,p.FromMM(.00025),p.ERROR_INSIDE)
    return polyset(poly)

def proposed_join(t,u):
    assert t.GetNetCode()==u.GetNetCode() and t.GetLayer()==u.GetLayer(),'Wrong-net or wrong-layer bridge'
    a,b=nearest_points(line(t),line(u));a=tuple(a.coords)[0];b=tuple(b.coords)[0]
    width=min(t.GetWidth(),u.GetWidth())/1e6
    if Point(a).distance(Point(b))<=.000002:return None
    return dict(net=t.GetNetname(),layer=t.GetLayer(),width_mm=width,a=a,b=b,tracks=[uid(t),uid(u)],net_code=t.GetNetCode())

def covered(join,copper):
    # A full-width capsule (minus the stated 2 um diameter tolerance) must fit
    # in the actual union. This is stronger than nonzero overlap/connectivity.
    witness=LineString(join.get('path',[join['a'],join['b']])).buffer((join['width_mm']-TOL)/2,quad_segs=64)
    return copper.covers(witness) or witness.difference(copper).area<1e-9

def local_full_width_path(join,copper):
    # A corner may have an intentional local bend instead of a direct chord.
    # Erode by the required radius: a connected component containing both
    # centerline endpoints proves a full-width alternative inside this local box.
    a,b=join['a'],join['b'];w=join['width_mm'];r=(w-TOL)/2
    window=box(min(a[0],b[0])-2*w,min(a[1],b[1])-2*w,max(a[0],b[0])+2*w,max(a[1],b[1])+2*w)
    safe=copper.intersection(window).buffer(-r,quad_segs=64)
    pieces=list(safe.geoms) if hasattr(safe,'geoms') else [safe]
    return any(g.covers(Point(a)) and g.covers(Point(b)) for g in pieces)

def audit_land_pairs(board, contacts=None):
    b=board;lands=[q for f in b.GetFootprints() for q in f.Pads() if q.GetNetCode()]+[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)];out=[];tested=0
    for layer in [0,4,6,2]:
        qs=[q for q in lands if q.IsOnLayer(layer)];polys=[shape(q,layer) for q in qs];tree=STRtree(polys);cache={}
        for i,q in enumerate(qs):
            for k in tree.query(polys[i].buffer(TOL),predicate='intersects'):
                k=int(k);u=qs[k]
                if k<=i or u.GetNetCode()!=q.GetNetCode():continue
                a=xy(q.GetPosition());c=xy(u.GetPosition())
                widths=[x.GetWidth(layer)/1e6 if isinstance(x,p.PCB_VIA) else 2*poly.boundary.distance(Point(xy(x.GetPosition()))) for x,poly in [(q,polys[i]),(u,polys[k])]]
                if Point(a).distance(Point(c))<.000002:
                    if contacts is not None:contacts.append(dict(kind='concentric-lands',net=q.GetNetname(),layer=layer,a=a,b=c,width_mm=min(widths)))
                    continue
                incident=[t.GetWidth()/1e6 for t in b.GetTracks() if type(t)==p.PCB_TRACK and t.GetNetCode()==q.GetNetCode() and t.GetLayer()==layer and (line(t).intersects(polys[i]) or line(t).intersects(polys[k]))]
                widths+=incident
                j=dict(net=q.GetNetname(),net_code=q.GetNetCode(),layer=layer,a=a,b=c,width_mm=min(widths),tracks=[],land_uuids=[uid(q),uid(u)],kind='land-pair')
                net=q.GetNetCode()
                if net not in cache:cache[net]=unary_union([polys[z] for z,x in enumerate(qs) if x.GetNetCode()==net]+[shape(t,layer) for t in b.GetTracks() if type(t)==p.PCB_TRACK and t.GetNetCode()==net and t.GetLayer()==layer]+[polyset(z.GetFilledPolysList(layer)) for z in b.Zones() if z.GetNetCode()==net and z.IsOnLayer(layer) and not z.GetIsRuleArea()])
                tested+=1
                if contacts is not None:contacts.append(j)
                if not covered(j,cache[net]) and not local_full_width_path(j,cache[net]):out.append(j)
    return out,tested

def audit(board, contacts=None):
    assert not any(isinstance(t,p.PCB_ARC) for t in board.GetTracks()), 'Arc-width audit requires explicit implementation'
    tracks=[t for t in board.GetTracks() if type(t)==p.PCB_TRACK and t.GetLength()>0]
    groups=defaultdict(list)
    for t in tracks:groups[(t.GetNetCode(),t.GetLayer())].append(t)
    pads=[q for f in board.GetFootprints() for q in f.Pads()]
    vias=[t for t in board.GetTracks() if isinstance(t,p.PCB_VIA)]
    findings=[];tested=0
    for (net,layer),items in groups.items():
        polygons=[shape(t,layer) for t in items];tree=STRtree(polygons)
        lands=[q for q in pads+vias if q.GetNetCode()==net and q.IsOnLayer(layer)]
        extras=[shape(q,layer) for q in lands]
        extras += [polyset(z.GetFilledPolysList(layer)) for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetCode()==net and z.IsOnLayer(layer)]
        copper=unary_union(polygons+extras)
        for i,t in enumerate(items):
            for j in tree.query(polygons[i].buffer(TOL),predicate='intersects'):
                j=int(j)
                if j<=i:continue
                join=proposed_join(t,items[j])
                if join is None:
                    if contacts is not None:
                        at=tuple(nearest_points(line(t),line(items[j]))[0].coords)[0]
                        contacts.append(dict(kind='shared-centerline',net=t.GetNetname(),layer=layer,a=at,b=at,width_mm=min(t.GetWidth(),items[j].GetWidth())/1e6))
                    continue
                tested+=1
                if contacts is not None:contacts.append(join)
                if not covered(join,copper) and not local_full_width_path(join,copper):findings.append(join)
        # Include pad/via entries and near-tangent cap contacts. A polygon
        # approximation may show a tiny gap where analytic round caps touch.
        for land in lands:
            land_shape=shape(land,layer);center=xy(land.GetPosition())
            radius=land_shape.boundary.distance(Point(center))
            if not land_shape.covers(Point(center)) or radius<.001:
                raise AssertionError(('Unsupported land shape',uid(land)))
            for i in tree.query(land_shape.buffer(TOL),predicate='intersects'):
                t=items[int(i)];a=tuple(nearest_points(line(t),Point(center))[0].coords)[0]
                land_width=land.GetWidth(layer)/1e6 if isinstance(land,p.PCB_VIA) else 2*radius
                width=min(t.GetWidth()/1e6,land_width)
                j=dict(kind='via' if isinstance(land,p.PCB_VIA) else 'pad',net=t.GetNetname(),net_code=net,
                    layer=layer,width_mm=width,bridge_width_mm=t.GetWidth()/1e6,a=a,b=center,
                    tracks=[uid(t)],land_uuid=uid(land),
                    land_reference='' if isinstance(land,p.PCB_VIA) else land.GetParentFootprint().GetReference()+'.'+land.GetNumber())
                if Point(a).distance(Point(center))<=.000002:
                    if contacts is not None:contacts.append(j)
                    continue
                tested+=1
                if contacts is not None:contacts.append(j)
                if not covered(j,copper) and not local_full_width_path(j,copper):findings.append(j)
    extra,count=audit_land_pairs(board,contacts)
    return findings+extra,tested+count

def add_bridge(board,join):
    t=p.PCB_TRACK(board)
    t.SetStart(p.VECTOR2I(*(round(v*1e6) for v in join['a'])));t.SetEnd(p.VECTOR2I(*(round(v*1e6) for v in join['b'])))
    t.SetWidth(round(join.get('bridge_width_mm',join['width_mm'])*1e6));t.SetLayer(join['layer'])
    t.SetNetCode(join['net_code'])
    board.Add(t);return t

def save(board,path):
    board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones());board.BuildConnectivity()
    assert p.SaveBoard(str(path.resolve()),board), "Board save failed"

def main():
    ap=argparse.ArgumentParser();ap.add_argument('board',type=Path);ap.add_argument('--repair',action='store_true');ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();board=p.LoadBoard(str(args.board));findings,tested=audit(board)
    result=dict(board=args.board.stem,source_sha256=hashlib.sha256(args.board.read_bytes()).hexdigest(),width_tolerance_mm=TOL,
        audited_cap_contacts=tested,findings=findings)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(args.board.stem,len(findings),'narrow joins of',tested,'cap contacts',flush=True)
    if not args.repair and findings:raise SystemExit(1)
    if args.repair:
        assert not any(j['net'] in USB for j in findings),'USB pair needs coordinated review before mutation'
        for j in findings:j['new_track_uuid']=uid(add_bridge(board,j))
        save(board,args.board)
        result['repaired_sha256']=hashlib.sha256(args.board.read_bytes()).hexdigest()
        args.output.write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
