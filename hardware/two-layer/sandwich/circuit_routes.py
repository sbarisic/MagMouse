# SPDX-License-Identifier: GPL-3.0-or-later
"""Local route completion for the reviewed circuit corrections (KiCad Python)."""
import argparse
import collections
import json
import math
import subprocess
import sys

from circuit_fixes import BOARDS, WORK, EVIDENCE, p, xy
from route_main import CLI, track, via
from export_quote import polygons
from shapely.geometry import Point, LineString
from shapely.ops import unary_union, nearest_points
from region_routes import connect
from standard_vias import obstacles
from continuous_routes import board_interior
from copper_graph import CopperGraph, uid
from shapely import STRtree


def copper_shape(t):
    return (Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2)
        if isinstance(t,p.PCB_VIA) else LineString([p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2))


def check(name,board):
    print(name,'build connectivity',flush=True)
    board.BuildConnectivity()
    print(name,'fill zones',flush=True)
    p.ZONE_FILLER(board).Fill(board.Zones())
    print(name,'save',flush=True)
    p.SaveBoard(str(BOARDS[name]),board)
    target=WORK/(name+'-drc.json')
    subprocess.run([str(CLI),'pcb','drc','--format','json','--schematic-parity','-o',str(target),str(BOARDS[name])],check=True,stdout=subprocess.DEVNULL)
    d=json.loads(target.read_text())
    print(name,'DRC',dict(collections.Counter(v['type'] for v in d['violations'])),
        'unconnected',len(d['unconnected_items']),'parity',len(d.get('schematic_parity',[])),flush=True)
    return d


def priority(name):
    board=p.LoadBoard(str(BOARDS[name]));fs={f.GetReference():f for f in board.GetFootprints()}
    pads={(r,q.GetNumber()):q for r,f in fs.items() for q in f.Pads() if q.GetNumber()}
    if name=='Wheel':
        for r in ('U40','U41','R147','R148','R149','R150','C102','C103','C104'):
            group='Package_TO_SOT_SMD' if r.startswith('U') else ('Resistor_SMD' if r.startswith('R') else 'Capacitor_SMD')
            fs[r].SetFPID(p.LIB_ID(group,str(fs[r].GetFPID().GetLibItemName())))
    routes=([
        ('U2','2','C1','1',[(50.25,27.75),(49.775,26.9)],.25,.6),
        ('U35','5','C86','1',[],.35,.35),
        ('U35','4','C83','1',[],.35,.35),
        ('U35','3','C85','1',[],.35,.35),
    ] if name=='Lower' else [
        ('U21','6','C47','2',[(24.2,27.75)],.25,.35),
        ('U21','7','C47','1',[(24.2,28.25)],.25,.35),
        ('U21','25','C48','1',[(30.8,28.75)],.25,.35),
        ('U23','8','C58','1',[],.25,.25),
        ('U23','7','C57','1',[(25.75,13.7)],.25,.35),
        ('U23','10','C56','1',[(23.7,15.75)],.25,.35),
        ('U21','8','C46','1',[(24.2,28.75),(23.45,30.7),(23.45,31.8)],.25,.35),
    ])
    dedicated={'WHEEL_CPL','WHEEL_CPH','ADC2_DECAP','WHEEL_CP'}
    for t in list(board.GetTracks()):
        if t.GetNetname() in dedicated:board.Remove(t);t.thisown=False
    for r,pin,c,cp,mid,escape,width in routes:
        a,b=pads[r,pin],pads[c,cp];net=a.GetNetname();assert net==b.GetNetname()
        points=[tuple(p.ToMM(a.GetPosition())),*mid,tuple(p.ToMM(b.GetPosition()))]
        for i,(start,end) in enumerate(zip(points,points[1:])):
            w=escape if i==0 else width
            corridor=LineString([start,end]).buffer(w/2+.16)
            for t in list(board.GetTracks()):
                if t.GetNetname()==net or (not isinstance(t,p.PCB_VIA) and t.GetLayer()!=p.F_Cu):continue
                if corridor.intersects(copper_shape(t)):board.Remove(t);t.thisown=False
            track(board,net,[start,end],w,p.F_Cu)
        print('priority',name,r,pin,c,cp,net,flush=True)
    check(name,board)


def shapes(item):
    result={}
    for layer in (p.F_Cu,p.B_Cu):
        if not item.IsOnLayer(layer):continue
        if isinstance(item,p.PAD):
            poly=p.SHAPE_POLY_SET();item.TransformShapeToPolygon(poly,layer,0,p.FromMM(.001),p.ERROR_OUTSIDE)
            result[layer]=unary_union(polygons(poly))
        else:result[layer]=copper_shape(item)
    return result


def direct(board,net,a,b):
    """Try short straight/45-degree/L routes before triangulating a whole layer."""
    start=tuple(p.ToMM(a.GetPosition()));end=tuple(p.ToMM(b.GetPosition()))
    x,y=start;u,v=end;dx,dy=u-x,v-y
    inner=board_interior(board)
    paths=[[start,end],[start,(x,v),end],[start,(u,y),end]]
    if abs(dx)>abs(dy):
        paths += [[start,(x+math.copysign(abs(dy),dx),v),end],
                  [start,(u-math.copysign(abs(dy),dx),y),end]]
    else:
        paths += [[start,(u,y+math.copysign(abs(dx),dy)),end],
                  [start,(x,v-math.copysign(abs(dx),dy)),end]]
    power=net in ('PWR_5V','ACT_5V','+3V3','OPT_3V3','OPT_1V9','OPT_VDDPIX','DRV_AVDD','WHEEL_CP','WHEEL_BUCK_OUT')
    for layer in (p.F_Cu,p.B_Cu):
        if not a.IsOnLayer(layer) or not b.IsOnLayer(layer):continue
        foreign=obstacles(board,net,layer)
        for width in ([.5,.25,.15] if power else [.15]):
            inner=board_interior(board,.501+width/2)
            avoid=foreign.buffer(.151+width/2)
            for points in paths:
                line=LineString(points)
                if inner.covers(line) and not avoid.intersects(line):
                    track(board,net,points,width,layer)
                    print('direct',net,'width',width,'layer',layer,flush=True)
                    return True
    return False


def island(graph,item):
    seen=set();todo=[uid(item)]
    while todo:
        key=todo.pop()
        if key in seen:continue
        seen.add(key);todo.extend(graph.adj.get(key,set())-seen)
    layers=collections.defaultdict(list)
    for key in seen:
        for layer,shape in shapes(graph.items[key]).items():layers[layer].append(shape)
    return {layer:unary_union(parts) for layer,parts in layers.items()}


def join_islands(board,net,first,last):
    class Endpoint:
        def __init__(self,pt,layer):self.pt=xy(pt.x,pt.y);self.layer=layer
        def GetPosition(self):return self.pt
        def IsOnLayer(self,layer):return layer==self.layer
    for layer in first.keys() & last.keys():
        a,b=nearest_points(first[layer].buffer(-.025),last[layer].buffer(-.025))
        if direct(board,net,Endpoint(a,layer),Endpoint(b,layer)):return True
    return connect(board,net,first,last,p.F_Cu,p.F_Cu) or connect(board,net,first,last,p.F_Cu,p.F_Cu,ripup=True)


def clear_conflicts(name):
    board=p.LoadBoard(str(BOARDS[name]));report=check(name,board)
    old=p.LoadBoard(str(WORK/'original'/name/BOARDS[name].name))
    original={uid(t) for t in old.GetTracks()}
    items={uid(t):t for t in board.GetTracks()}
    keep={'WHEEL_CPH','WHEEL_CPL','USB_DP','USB_DM'}
    remove=set()
    for v in report['violations']:
        if v['type'] not in ('shorting_items','clearance','tracks_crossing','hole_clearance','hole_to_hole','solder_mask_bridge'):continue
        choices=[items[i['uuid']] for i in v['items'] if i['uuid'] in items]
        if not choices:continue
        # Preserve fixed pin escapes and the charge-pump pair. Prefer removing
        # a newly introduced conflict over an original working route.
        choices.sort(key=lambda t:(t.GetNetname() in keep,uid(t) in original,
                                  t.GetNetname()=='GND',isinstance(t,p.PCB_VIA)))
        remove.add(uid(choices[0]))
    for key in remove:
        t=items[key];board.Remove(t);t.thisown=False
    print('Removed conflicting copper',len(remove),flush=True)
    check(name,board)


def stitch(name):
    """Join disconnected ground regions, without blanketing the board in vias."""
    board=p.LoadBoard(str(BOARDS[name]))
    for attempt in range(20):
        report=check(name,board)
        if not report['unconnected_items']:return report
        layers=(p.F_Cu,p.B_Cu);regions={};trees={}
        for layer in layers:
            copper=[poly for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname()=='GND' and z.IsOnLayer(layer)
                    for poly in polygons(z.GetFilledPolysList(layer))]
            copper += [shape for t in board.GetTracks() if t.GetNetname()=='GND' for l,shape in shapes(t).items() if l==layer]
            copper += [shape for f in board.GetFootprints() for q in f.Pads() if q.GetNetname()=='GND' for l,shape in shapes(q).items() if l==layer]
            union=unary_union(copper)
            regions[layer]=list(union.geoms) if hasattr(union,'geoms') else [union]
            trees[layer]=STRtree(regions[layer])
        parent={(l,i):(l,i) for l in layers for i in range(len(regions[l]))}
        def root(k):
            while parent[k]!=k:k=parent[k]
            return k
        for t in list(board.GetTracks())+[q for f in board.GetFootprints() for q in f.Pads()]:
            if t.GetNetname()!='GND' or not all(t.IsOnLayer(l) for l in layers):continue
            nodes=[(l,int(i)) for l in layers for i in trees[l].query(Point(p.ToMM(t.GetPosition())),predicate='intersects')]
            for node in nodes[1:]:parent[root(node)]=root(nodes[0])
        forbidden=[]
        for f in board.GetFootprints():
            for q in f.Pads():
                forbidden.extend(shape.buffer(.151) for shape in shapes(q).values())
                if q.GetDrillSize().x:
                    forbidden.append(Point(p.ToMM(q.GetPosition())).buffer(p.ToMM(max(q.GetDrillSize().x,q.GetDrillSize().y))/2+.401))
        forbidden += [Point(p.ToMM(t.GetPosition())).buffer(.551) for t in board.GetTracks() if isinstance(t,p.PCB_VIA)]
        avoid=unary_union(forbidden);options=[]
        for i,front in enumerate(regions[layers[0]]):
            for j in trees[layers[1]].query(front,predicate='intersects'):
                j=int(j)
                if root((layers[0],i))==root((layers[1],j)):continue
                safe=front.intersection(regions[layers[1]][j]).buffer(-.251).difference(avoid)
                if not safe.is_empty and safe.area>.005:options.append(safe)
        if not options:
            print('No safe overlapping ground regions; inspect remaining connection',flush=True);return report
        spot=max(options,key=lambda a:a.area).representative_point()
        via(board,'GND',(spot.x,spot.y),.45,.3)
        print('Ground-region stitch',spot.x,spot.y,flush=True)
    return check(name,board)


def repair(name,limit=150,trim_first=False):
    board=p.LoadBoard(str(BOARDS[name]));report=check(name,board)
    for iteration in range(limit):
        # Old dangling stubs are removed only when native DRC identifies them.
        copper_ids={uid(t) for t in board.GetTracks()} | {uid(q) for f in board.GetFootprints() for q in f.Pads()}
        pending_copper=any(all(i['uuid'] in copper_ids for i in v['items']) for v in report['unconnected_items'])
        ids={i['uuid'] for v in report['violations'] if v['type'] in ('track_dangling','via_dangling') for i in v['items']} if trim_first or not pending_copper else set()
        removed=0
        trim_graph=CopperGraph(board)
        for t in list(board.GetTracks()):
            if t.m_Uuid.AsString() not in ids:continue
            contacts=[trim_graph.items[k] for k in trim_graph.adj.get(uid(t),())]
            # A flagged branch can touch the same conductor twice. Removing
            # such a redundant loop is safer than repeatedly shortening it.
            neighbors=set(trim_graph.adj.get(uid(t),()))
            seen=set();todo=list(neighbors)[:1]
            while todo:
                key=todo.pop()
                if key in seen or key==uid(t):continue
                seen.add(key);todo.extend(trim_graph.adj.get(key,set())-seen-{uid(t)})
            if len(neighbors)<=1 or neighbors<=seen:
                board.Remove(t);t.thisown=False;removed+=1
                continue
            if not isinstance(t,p.PCB_VIA) and p.ToMM(t.GetLength())>.4 and len(contacts)>1:
                line=LineString([p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())])
                distances=[]
                for other in contacts:
                    area=shapes(other).get(t.GetLayer())
                    if area is None:continue
                    hit=line.intersection(area)
                    if not hit.is_empty:
                        if isinstance(other,p.PCB_TRACK) and not isinstance(other,p.PCB_VIA):
                            center=line.intersection(LineString([p.ToMM(other.GetStart()),p.ToMM(other.GetEnd())]))
                            distances.append(line.project(center.centroid if not center.is_empty else hit.centroid))
                        else:
                            distances.append(line.project(Point(p.ToMM(other.GetPosition()))))
                if len(distances)>1 and max(distances)-min(distances)>.001:
                    a=line.interpolate(min(distances));c=line.interpolate(max(distances))
                    # Trim along the original centreline. Snapping sideways
                    # to a neighbouring trace can reduce foreign-net clearance.
                    t.SetStart(xy(a.x,a.y));t.SetEnd(xy(c.x,c.y));removed+=1
                    continue
            board.Remove(t);t.thisown=False;removed+=1
        if removed:
            report=check(name,board)
            continue
        items={t.m_Uuid.AsString():t for t in board.GetTracks()}
        items.update({q.m_Uuid.AsString():q for f in board.GetFootprints() for q in f.Pads()})
        usable=[v for v in report['unconnected_items'] if all(i['uuid'] in items for i in v['items'])]
        if not usable:break
        usable.sort(key=lambda v:math.dist(*[p.ToMM(items[i['uuid']].GetPosition()) for i in v['items']]))
        graph=CopperGraph(board)
        success=False
        for finding in usable:
            a,b=[items[i['uuid']] for i in finding['items']]
            net=a.GetNetname();assert net==b.GetNetname()
            print('repair',iteration,net,tuple(p.ToMM(a.GetPosition())),tuple(p.ToMM(b.GetPosition())),flush=True)
            if join_islands(board,net,island(graph,a),island(graph,b)):
                success=True;break
        if not success:
            print('No local route; retain unresolved items for inspection',flush=True);break
        report=check(name,board)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['priority','repair','check','clear-conflicts','stitch'])
    parser.add_argument('board',choices=['Lower','Upper','Wheel']);parser.add_argument('--limit',type=int,default=150)
    a=parser.parse_args()
    if a.action=='priority':priority(a.board)
    elif a.action=='repair':repair(a.board,a.limit)
    elif a.action=='clear-conflicts':clear_conflicts(a.board)
    elif a.action=='stitch':stitch(a.board)
    else:check(a.board,p.LoadBoard(str(BOARDS[a.board])))
