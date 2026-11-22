"""Simplify routed copper without moving components, vias or electrical junctions.

Use KiCad Python. Saved boards are authoritative. Native DRC and the independent
USB return-copper check remain the release gates; this is a geometry optimizer.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import argparse, collections, hashlib, json, math, shutil
from integrated_encoder import p, BOARDS, HERE, ROOT, CLI
from route_main import track
from standard_vias import obstacles
from export_quote import polygons
from usb_return import SIGNALS, actual_ground
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

WORK=ROOT/'build/sandwich/routing-cleanup'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def uid(t):return t.m_Uuid.AsString()
def coord(q):return (q.x,q.y)
def mm(q):return (q[0]/1e6,q[1]/1e6)
def line(t):return LineString([p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())])
def copper(t):
    return Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2) if isinstance(t,p.PCB_VIA) else line(t).buffer(p.ToMM(t.GetWidth())/2)

def snapshot():
    WORK.mkdir(parents=True,exist_ok=True)
    for name,path in BOARDS.items():
        folder=WORK/name
        if not folder.exists():shutil.copytree(path.parent,folder)

def chains(board):
    """Extract paths bounded by pads, vias, branches, or width changes."""
    groups=collections.defaultdict(list)
    all_tracks=collections.defaultdict(list);lands=collections.defaultdict(list)
    for t in board.GetTracks():
        if isinstance(t,p.PCB_VIA):
            for l in (p.F_Cu,p.B_Cu):lands[t.GetNetname(),l].append(copper(t))
        else:
            groups[t.GetNetname(),t.GetLayer(),t.GetWidth()].append(t)
            all_tracks[t.GetNetname(),t.GetLayer()].append(t)
    for q in board.GetPads():
        for l in (p.F_Cu,p.B_Cu):
            if q.IsOnLayer(l):
                poly=p.SHAPE_POLY_SET();q.TransformShapeToPolygon(poly,l,0,1000,p.ERROR_OUTSIDE)
                lands[q.GetNetname(),l].extend(polygons(poly))
    result=[]
    for (net,layer,width),ts in groups.items():
        incident=collections.defaultdict(list)
        for t in ts:
            incident[coord(t.GetStart())].append(t);incident[coord(t.GetEnd())].append(t)
        other=all_tracks[net,layer];shapes=[copper(t) for t in other];index=STRtree(shapes)
        anchor=unary_union(lands[net,layer]);fixed=set()
        for t in ts:
            a,c=mm(coord(t.GetStart())),mm(coord(t.GetEnd()))
            endpoints=Point(a).buffer(p.ToMM(width)+.002).union(Point(c).buffer(p.ToMM(width)+.002))
            for j in index.query(copper(t),predicate='intersects'):
                q=other[j]
                if uid(q)==uid(t):continue
                if {coord(t.GetStart()),coord(t.GetEnd())}&{coord(q.GetStart()),coord(q.GetEnd())}:
                    # Group degree already stops at a width change. The adjacent
                    # segment is still eligible for cleanup along its own width.
                    continue
                # An existing mid-track tap must not disappear during simplification.
                if not line(t).intersection(line(q)).difference(endpoints).is_empty:
                    fixed.add(uid(t));break
            if not anchor.is_empty:
                hit=copper(t).intersection(anchor).difference(endpoints)
                if not hit.is_empty:fixed.add(uid(t))
        def stop(k):
            return len(incident[k])!=2 or any(uid(t) in fixed for t in incident[k]) or anchor.distance(Point(mm(k)))<p.ToMM(width)/2+.002
        used=set()
        for initial in ts:
            if uid(initial) in used:continue
            a,c=coord(initial.GetStart()),coord(initial.GetEnd())
            if uid(initial) in fixed:
                used.add(uid(initial));continue
            # Walk backwards to a boundary, then forwards through the whole chain.
            start=a;prev=initial;seen={uid(initial)}
            while not stop(start):
                nxt=next(q for q in incident[start] if uid(q)!=uid(prev))
                if uid(nxt) in seen:break
                seen.add(uid(nxt));start=coord(nxt.GetEnd()) if coord(nxt.GetStart())==start else coord(nxt.GetStart());prev=nxt
            points=[mm(start)];items=[];current=start;prev=None
            while True:
                choices=[q for q in incident[current] if uid(q) not in used and uid(q) not in fixed]
                if not choices:break
                t=choices[0]
                if uid(t) in fixed:break
                used.add(uid(t));items.append(t)
                current=coord(t.GetEnd()) if coord(t.GetStart())==current else coord(t.GetStart());points.append(mm(current));prev=t
                if stop(current) or current==start:break
            if items and len(points)>2 and points[0]!=points[-1]:result.append((net,layer,p.ToMM(width),items,points))
    return result

def turn(a,b,c):
    u=(b[0]-a[0],b[1]-a[1]);v=(c[0]-b[0],c[1]-b[1]);den=math.hypot(*u)*math.hypot(*v)
    return math.degrees(math.acos(max(-1,min(1,(u[0]*v[0]+u[1]*v[1])/den)))) if den>1e-12 else 0

def audit(board):
    cs=chains(board);corners=[];jogs=[]
    for net,layer,w,items,pts in cs:
        for a,b,c in zip(pts,pts[1:],pts[2:]):
            angle=turn(a,b,c)
            if angle>80:corners.append({'net':net,'layer':board.GetLayerName(layer),'xy_mm':b,'turn_deg':round(angle,4)})
        for a,b,c,d in zip(pts,pts[1:],pts[2:],pts[3:]):
            if math.dist(b,c)<.3 and turn(a,b,c)>20 and turn(b,c,d)>20:
                ab=(b[0]-a[0],b[1]-a[1]);bc=(c[0]-b[0],c[1]-b[1]);cd=(d[0]-c[0],d[1]-c[1])
                if (ab[0]*bc[1]-ab[1]*bc[0])*(bc[0]*cd[1]-bc[1]*cd[0])<0:
                    jogs.append({'net':net,'layer':board.GetLayerName(layer),'xy_mm':b,'length_mm':math.dist(b,c)})
    return {'tracks':sum(not isinstance(t,p.PCB_VIA) for t in board.GetTracks()),
        'length_mm':sum(p.ToMM(t.GetLength()) for t in board.GetTracks() if not isinstance(t,p.PCB_VIA)),
        'sharp_corners':corners,'short_reverse_bends':jogs}

def candidates(a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];m=min(abs(dx),abs(dy));sx=math.copysign(1,dx);sy=math.copysign(1,dy)
    yield [a,b]
    for q in [(a[0]+sx*m,a[1]+sy*m),(b[0]-sx*m,b[1]-sy*m)]:
        pts=[a,q,b];yield [v for i,v in enumerate(pts) if i==0 or v!=pts[i-1]]

def optimize(name):
    snapshot();path=BOARDS[name];b=p.LoadBoard(str(path));before=audit(b)
    outline=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(outline,False)
    material=unary_union(polygons(outline))
    inner=unary_union([Polygon(poly.exterior).buffer(-.5).difference(unary_union([Polygon(h).buffer(.4 if name=='Lower' else .5) for h in poly.interiors])) for poly in getattr(material,'geoms',[material])])
    holes=unary_union([Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetDrillValue())/2) for t in b.GetTracks() if isinstance(t,p.PCB_VIA)])
    antipads=unary_union([Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2+.215) for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname() in SIGNALS])
    reference={l:actual_ground(b,l,holes).union(antipads) for l in (p.F_Cu,p.B_Cu)}
    work=chains(b);work.sort(key=lambda v:(v[0] not in SIGNALS,v[0]!='GND',v[0],-len(v[4])))
    changed=[];current_net=None;foreign={}
    for net,layer,width,items,original in work:
        if current_net!=net:
            current_net=net;foreign={l:obstacles(b,net,l) for l in (p.F_Cu,p.B_Cu)}
        old=LineString(original).buffer(width/2)
        forbidden=foreign[layer].buffer(.1505)
        own=[copper(t) for t in b.GetTracks() if t.GetNetname()==net and t.IsOnLayer(layer) and uid(t) not in {uid(q) for q in items} and not isinstance(t,p.PCB_VIA)]
        own=unary_union(own).difference(Point(original[0]).buffer(width+.01).union(Point(original[-1]).buffer(width+.01)))
        def clear(pts):
            if len(pts)<2:return False
            sh=LineString(pts).buffer(width/2)
            added=sh.difference(old.buffer(.000002))
            if added.intersects(forbidden) or not inner.buffer(.000002).covers(added):return False
            if not added.intersection(own).is_empty:return False
            # The broad USB pair is already a straight/45-degree route. Do not
            # independently shortcut one member and change its paired spacing.
            if net in SIGNALS and width>=.5 and not old.buffer(.01).covers(sh):return False
            if net in SIGNALS and sh.difference(reference[p.B_Cu if layer==p.F_Cu else p.F_Cu]).area>.0001:return False
            return True
        points=[original[0]];i=0
        while i<len(original)-1:
            chosen=None
            for j in range(len(original)-1,i+1,-1):
                for route in candidates(original[i],original[j]):
                    if len(route)<=j-i+1 and clear(route):chosen=(j,route);break
                if chosen:break
            if chosen:
                j,route=chosen;points.extend(route[1:]);i=j
            else:points.append(original[i+1]);i+=1
        # Bevel the remaining sharp corners, using the largest safe cut first.
        for iteration in range(3):
            result=[points[0]]
            for i in range(1,len(points)-1):
                a,c,d=result[-1],points[i],points[i+1]
                if turn(a,c,d)<60:result.append(c);continue
                length=min(math.dist(a,c),math.dist(c,d))
                for distance in [min(.8,length*.4),min(.4,length*.3),min(.2,length*.25),min(.1,length*.2),min(.05,length*.15),min(.025,length*.1)]:
                    if distance<.005:continue
                    u=tuple(c[k]+(a[k]-c[k])*distance/math.dist(a,c) for k in (0,1));v=tuple(c[k]+(d[k]-c[k])*distance/math.dist(c,d) for k in (0,1))
                    if clear([a,u,v,d]):result.extend([u,v]);break
                else:result.append(c)
            result.append(points[-1]);points=result
        points=[(round(x,6),round(y,6)) for x,y in points]
        if points==original or not clear(points):continue
        if LineString(points).length>LineString(original).length+.0001:continue
        for t in items:b.Remove(t);t.thisown=False
        for a,c in zip(points,points[1:]):
            if math.dist(a,c)>.000002:track(b,net,[a,c],width,layer)
        changed.append({'net':net,'layer':b.GetLayerName(layer),'before_points':len(original),'after_points':len(points)})
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
    after=audit(b);report={'source_sha256':sha(path),'before':before,'after':after,'changed_paths':changed}
    (WORK/(name+'-cleanup.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(name,'paths',len(changed),'corners',len(before['sharp_corners']),'->',len(after['sharp_corners']),
          'jogs',len(before['short_reverse_bends']),'->',len(after['short_reverse_bends']),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['snapshot','apply','audit']);ap.add_argument('names',nargs='*');args=ap.parse_args()
    if args.action=='snapshot':snapshot()
    else:
        for name in args.names or list(BOARDS):
            if args.action=='apply':optimize(name)
            else:
                d=audit(p.LoadBoard(str(BOARDS[name])));print(name,'corners',len(d['sharp_corners']),'jogs',len(d['short_reverse_bends']))
