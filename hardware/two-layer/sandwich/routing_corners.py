"""Independent endpoint-corner inventory, including track-width transitions."""
import collections, json, math, sys
from cleanup_routes import p, BOARDS, coord, mm, turn, polygons, unary_union, Point, copper, line, obstacles, SIGNALS, actual_ground, track, uid
from shapely.geometry import LineString, Polygon

def corners(board, minimum=80):
    nodes=collections.defaultdict(list); lands=collections.defaultdict(list)
    for t in board.GetTracks():
        if isinstance(t,p.PCB_VIA):
            for l in (p.F_Cu,p.B_Cu):
                lands[t.GetNetname(),l].append(Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetWidth(l))/2))
        else:
            for q in (t.GetStart(),t.GetEnd()):nodes[t.GetNetname(),t.GetLayer(),coord(q)].append(t)
    for q in board.GetPads():
        for l in (p.F_Cu,p.B_Cu):
            if q.IsOnLayer(l):
                shape=p.SHAPE_POLY_SET();q.TransformShapeToPolygon(shape,l,0,1000,p.ERROR_OUTSIDE)
                lands[q.GetNetname(),l].extend(polygons(shape))
    lands={k:unary_union(v) for k,v in lands.items()};result=[]
    for (net,layer,xy),items in nodes.items():
        if len(items)!=2:continue  # Branch junction, not a bend.
        b=mm(xy)
        if (net,layer) in lands and lands[net,layer].distance(Point(b))<.002:continue
        ends=[mm(coord(t.GetEnd()) if coord(t.GetStart())==xy else coord(t.GetStart())) for t in items]
        angle=turn(ends[0],b,ends[1])
        if angle>=minimum:
            result.append(dict(net=net,layer=board.GetLayerName(layer),xy_mm=b,turn_deg=angle,
                widths_mm=[p.ToMM(t.GetWidth()) for t in items],uuids=[t.m_Uuid.AsString() for t in items]))
    return result

def staircases(board):
    """Repeated short alternating turns; a single 45-degree offset is not a staircase."""
    from cleanup_routes import chains
    result=[]
    for net,layer,width,items,pts in chains(board):
        run=[]
        for i in range(1,len(pts)-1):
            a,b,c=pts[i-1:i+2];u=(b[0]-a[0],b[1]-a[1]);v=(c[0]-b[0],c[1]-b[1])
            sign=u[0]*v[1]-u[1]*v[0]
            if turn(a,b,c)<20:run=[];continue
            if run and (sign*run[-1][1]>=0 or math.dist(pts[i-1],b)>.35):run=[]
            run.append((i,sign))
            if len(run)==3:result.append(dict(net=net,layer=board.GetLayerName(layer),xy_mm=pts[run[0][0]]))
    return result

def bevel(name):
    board=p.LoadBoard(str(BOARDS[name]));changed=0
    outline=p.SHAPE_POLY_SET();assert board.GetBoardPolygonOutlines(outline,False)
    material=unary_union(polygons(outline))
    inner=unary_union([Polygon(poly.exterior).buffer(-.5).difference(unary_union([Polygon(h).buffer(.4 if name=='Lower' else .5) for h in poly.interiors])) for poly in getattr(material,'geoms',[material])])
    holes=unary_union([Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetDrillValue())/2) for t in board.GetTracks() if isinstance(t,p.PCB_VIA)])
    antipads=unary_union([Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2+.215) for t in board.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname() in SIGNALS])
    reference={l:actual_ground(board,l,holes).union(antipads) for l in (p.F_Cu,p.B_Cu)}
    for iteration in range(4):
        candidates=corners(board,60);count=0;cached={}
        for row in candidates:
            lookup={uid(t):t for t in board.GetTracks()};ids=row['uuids']
            if not all(k in lookup for k in ids):continue
            ts=[lookup[k] for k in ids];net=row['net'];layer=ts[0].GetLayer();b=row['xy_mm'];widths=row['widths_mm']
            ends=[p.ToMM(t.GetEnd()) if math.dist(p.ToMM(t.GetStart()),b)<.000001 else p.ToMM(t.GetStart()) for t in ts]
            a,c=ends;old=unary_union([copper(t) for t in ts]);key=(net,layer)
            # Other-net edits invalidate this cache only between sweeps.
            if key not in cached:cached[key]=obstacles(board,net,layer).buffer(.1505)
            forbidden=cached[key]
            contacts=[];untouched=[]
            others=[(t,copper(t)) for t in board.GetTracks() if uid(t) not in ids and t.GetNetname()==net and t.IsOnLayer(layer)]
            for q in board.GetPads():
                if q.GetNetname()==net and q.IsOnLayer(layer):
                    poly=p.SHAPE_POLY_SET();q.TransformShapeToPolygon(poly,layer,0,1000,p.ERROR_OUTSIDE)
                    others.append((q,unary_union(polygons(poly))))
            for obj,shape in others:
                (contacts if old.intersects(shape) else untouched).append(shape)
            untouched=unary_union(untouched)
            length=min(math.dist(a,b),math.dist(c,b))
            for distance in [min(1,length*.45),min(.6,length*.4),min(.3,length*.35),min(.15,length*.3),min(.075,length*.25),min(.03,length*.2),min(.01,length*.15)]:
                if distance<.002:continue
                u=tuple(round(b[k]+(a[k]-b[k])*distance/math.dist(a,b),6) for k in (0,1))
                v=tuple(round(b[k]+(c[k]-b[k])*distance/math.dist(c,b),6) for k in (0,1))
                segs=[(a,u,widths[0]),(u,v,min(widths)),(v,c,widths[1])]
                sh=unary_union([LineString([x,y]).buffer(w/2) for x,y,w in segs]);added=sh.difference(old.buffer(.000002))
                if added.intersects(forbidden) or not inner.buffer(.000002).covers(added):continue
                if not added.intersection(untouched).is_empty or any(not sh.intersects(s) for s in contacts):continue
                if net in SIGNALS and sh.difference(reference[p.B_Cu if layer==p.F_Cu else p.F_Cu]).area>.0001:continue
                for t in ts:board.Remove(t);t.thisown=False
                for x,y,w in segs:track(board,net,[x,y],w,layer)
                changed+=1;count+=1;break
        print(name,'bevel sweep',iteration,count,flush=True)
        if not count:break
    board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones());p.SaveBoard(str(BOARDS[name]),board)
    print(name,'remaining corners',json.dumps(corners(board)),flush=True)

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='bevel':
        for name in sys.argv[2:] or list(BOARDS):bevel(name)
    else:print(json.dumps({n:corners(p.LoadBoard(str(path))) for n,path in BOARDS.items()},indent=2))
