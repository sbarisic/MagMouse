"""Measured 2 mm assembly spacing and outline revision. Run with KiCad Python.

Physical envelopes include front fabrication bodies and solder lands. Pins of
one component, wire-pad pitch, and underside test pads are not separate parts.
"""
import argparse, collections, hashlib, json, math, shutil, sys
from pathlib import Path
import pcbnew as p
from export_quote import BOARDS, HERE, ROOT, CLI, polygons
from shapely.geometry import Point, Polygon, box, MultiPoint
from shapely.ops import unary_union
from shapely.affinity import translate
from shapely.prepared import prep

WORK=ROOT/'build/sandwich/assembly-spacing'
GAP=2.0

def xy(a,b): return p.VECTOR2I(p.FromMM(a),p.FromMM(b))

def envelope(f):
    parts=[]
    for pad in f.Pads():
        if not pad.IsOnLayer(p.F_Cu): continue
        ps=p.SHAPE_POLY_SET()
        pad.TransformShapeToPolygon(ps,p.F_Cu,0,p.FromMM(.001),p.ERROR_OUTSIDE)
        parts.extend(polygons(ps))
    points=[]
    for g in f.GraphicalItems():
        if not isinstance(g,p.PCB_SHAPE) or g.GetLayer()!=p.F_Fab: continue
        if g.GetShape() in (p.SHAPE_T_SEGMENT,p.SHAPE_T_RECT):
            a,b=tuple(p.ToMM(g.GetStart())),tuple(p.ToMM(g.GetEnd()))
            points.extend([a,b])
            if g.GetShape()==p.SHAPE_T_RECT: points.extend([(a[0],b[1]),(b[0],a[1])])
        elif g.GetShape()==p.SHAPE_T_CIRCLE:
            parts.append(Point(p.ToMM(g.GetCenter())).buffer(p.ToMM(g.GetRadius())))
    if points: parts.append(MultiPoint(points).convex_hull)
    return unary_union(parts).convex_hull

def active(f):
    return not f.GetReference().startswith(('TP','H')) and not f.IsDNP() and not f.IsFlipped()

def snapshot():
    WORK.mkdir(parents=True,exist_ok=True)
    if (WORK/'baseline.json').exists(): return
    result={}
    for name,path in BOARDS.items():
        dest=WORK/'original'/name;dest.mkdir(parents=True,exist_ok=True)
        for file in path.parent.glob('*.kicad_*'): shutil.copy2(file,dest/file.name)
        b=p.LoadBoard(str(path))
        result[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'components':{
            f.GetReference():{'xy':list(p.ToMM(f.GetPosition())),'angle':f.GetOrientationDegrees(),
                'value':f.GetValue(),'footprint':str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),
                'pads':sorted((q.GetNumber(),q.GetNetname()) for q in f.Pads())}
            for f in b.GetFootprints()}}
    (WORK/'baseline.json').write_text(json.dumps(result,indent=2)+'\n')

def inventory():
    for name,path in BOARDS.items():
        b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()}
        env={r:envelope(f) for r,f in fs.items() if active(f)}
        bad=sorted((round(a.distance(c),3),r,s) for r,a in env.items() for s,c in env.items() if r<s and a.distance(c)<GAP-.001)
        print(name,'parts',len(env),'under 2 mm',len(bad),'worst',bad[:12],flush=True)
        if name in ('Upper','Encoder'):
            for r,f in sorted(fs.items()):
                x,y=p.ToMM(f.GetPosition())
                if name=='Encoder' or x<23 and y<24: print(r,(x,y),tuple(round(v,3) for v in envelope(f).bounds),flush=True)

def verify():
    """Audit saved sources, independently of the placement/routing algorithms."""
    from standard_vias import intersections
    baseline=json.loads((WORK/'baseline.json').read_text()) if (WORK/'baseline.json').exists() else None
    result={'definition':'Minimum 2 mm between front component body-and-land convex envelopes; pins within a component and copper-only test access excluded.',
            'boards':{}}
    for name,path in BOARDS.items():
        b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()}
        env={r:envelope(f) for r,f in fs.items() if active(f)}
        pairs=sorted((a.distance(c),r,s) for r,a in env.items() for s,c in env.items() if r<s)
        assert pairs[0][0]>=2-.00001,(name,pairs[0])
        assert b.GetCopperLayerCount()==2
        assert not intersections(b),(name,'via hole over SMD land')
        assert all(t.GetDrillValue()==p.FromMM(.3) for t in b.GetTracks() if isinstance(t,p.PCB_VIA))
        ps=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(ps,False)
        material=unary_union(polygons(ps));holes=[Polygon(h) for q in polygons(ps) for h in q.interiors]
        if name=='Lower':
            nominal=box(31.2,43.68,39.8,60.94).buffer(-1).buffer(1,quad_segs=128)
            assert len(holes)==1 and holes[0].symmetric_difference(nominal).area<.03
            assert all(abs(a-c)<.00002 for a,c in zip(holes[0].bounds,(31.2,43.68,39.8,60.94)))
            assert tuple(p.ToMM(fs['U35'].GetPosition()))==(35.5,52.5)
        elif name=='Wheel':
            main_outline=p.SHAPE_POLY_SET()
            main=p.LoadBoard(str(BOARDS['Upper']))
            assert main.GetBoardPolygonOutlines(main_outline,False)
            strip=polygons(main_outline)[0].intersection(box(-1,26,71,93))
            assert material.symmetric_difference(translate(strip,-7.5,-29)).area<.0001
        elif name=='Encoder':
            assert abs(material.area-236)<.000001
            assert material.symmetric_difference(Polygon([(54,50),(60,50),(64,54),(64,68),(50,68),(50,54)])).area<.000001
            assert tuple(p.ToMM(fs['J7'].GetPosition()))==(57,64.5)
            assert tuple(p.ToMM(fs['U27'].GetPosition()))==(57,55.5)
        moved={}
        if baseline:
            old=baseline[name]['components'];assert set(fs)==set(old)
            previous=p.LoadBoard(str(WORK/'original'/name/path.name))
            ids={f.GetReference():(str(f.GetFPID().GetLibNickname()),str(f.GetFPID().GetLibItemName())) for f in previous.GetFootprints()}
            for r,f in fs.items():
                assert f.GetValue()==old[r]['value']
                assert (str(f.GetFPID().GetLibNickname()),str(f.GetFPID().GetLibItemName()))==ids[r],r
                assert sorted([q.GetNumber(),q.GetNetname()] for q in f.Pads())==old[r]['pads'],r
                pos=list(p.ToMM(f.GetPosition()))
                if pos!=old[r]['xy'] or f.GetOrientationDegrees()!=old[r]['angle']:
                    moved[r]={'before_xy_mm':old[r]['xy'],'after_xy_mm':pos,'before_angle':old[r]['angle'],'after_angle':f.GetOrientationDegrees()}
        result['boards'][name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'minimum_component_gap_mm':pairs[0][0],'closest_pairs_mm':pairs[:12],
            'measured_component_envelopes':len(env),'board_area_mm2':material.area,
            'edge_cut_holes_mm':[list(q.bounds) for q in holes],
            'via_drill_mm':.3,'via_hole_smd_overlaps':0,'copper_layers':2,
            'component_values_and_pin_nets_preserved':bool(baseline),'moved_footprints':moved}
        result['boards'][name]['footprint_library_ids_preserved']=bool(baseline)
        if name=='Upper':
            boundary=material.boundary
            gaps={r:env[r].distance(boundary) for r in ('R29','R30','R31','R32','R33','R34','R35','R44','C24')}
            assert min(gaps.values())>=3
            result['boards'][name]['circled_component_edge_clearances_mm']=gaps
        print(name,'minimum gap',round(pairs[0][0],4),'mm; moved',len(moved),flush=True)
    lower=p.LoadBoard(str(BOARDS['Lower']));upper=p.LoadBoard(str(BOARDS['Upper']))
    connectors=[]
    for b,r in ((lower,'J103'),(upper,'J104')):
        f=next(f for f in b.GetFootprints() if f.GetReference()==r)
        connectors.append(sorted((q.GetNumber(),tuple(p.ToMM(q.GetPosition()))) for q in f.Pads()))
    assert connectors[0]==connectors[1]
    (HERE/'assembly-spacing-review.json').write_text(json.dumps(result,indent=2)+'\n')

def outlines(b,name):
    if name=='Encoder':
        for g in list(b.GetDrawings()):
            if g.GetLayer()==p.Edge_Cuts:b.Remove(g);g.thisown=False
        pts=[(54,50),(60,50),(64,54),(64,68),(50,68),(50,54)]
        for a,c in zip(pts,pts[1:]+pts[:1]):
            g=p.PCB_SHAPE(b);g.SetShape(p.SHAPE_T_SEGMENT);g.SetLayer(p.Edge_Cuts)
            g.SetStart(xy(*a));g.SetEnd(xy(*c));g.SetWidth(p.FromMM(.05));b.Add(g)
    if name=='Lower':
        # PixArt R1.50 Figure 3, transformed by U35's -90 degree rotation.
        # Nominal rectangular envelope with R1 internal corners for the panel's
        # 2 mm cutter. Corner/lens fit remains a physical assembly check.
        optical_opening(b)

def optical_opening(b):
    x0,y0,x1,y1=31.2,43.68,39.8,60.94
    lines=[((x0+1,y0),(x1-1,y0)),((x1,y0+1),(x1,y1-1)),
           ((x1-1,y1),(x0+1,y1)),((x0,y1-1),(x0,y0+1))]
    for a,c in lines:
        g=p.PCB_SHAPE(b);g.SetShape(p.SHAPE_T_SEGMENT);g.SetLayer(p.Edge_Cuts)
        g.SetStart(xy(*a));g.SetEnd(xy(*c));g.SetWidth(p.FromMM(.05));b.Add(g)
    s=math.sqrt(.5)
    arcs=[((x1-1,y0),(x1-1+s,y0+1-s),(x1,y0+1)),
          ((x1,y1-1),(x1-1+s,y1-1+s),(x1-1,y1)),
          ((x0+1,y1),(x0+1-s,y1-1+s),(x0,y1-1)),
          ((x0,y0+1),(x0+1-s,y0+1-s),(x0+1,y0))]
    for a,m,c in arcs:
        g=p.PCB_SHAPE(b);g.SetShape(p.SHAPE_T_ARC);g.SetLayer(p.Edge_Cuts)
        g.SetArcGeometry(xy(*a),xy(*m),xy(*c));g.SetWidth(p.FromMM(.05));b.Add(g)

def place(name):
    snapshot();path=BOARDS[name]
    b=p.LoadBoard(str(WORK/'original'/name/path.name));outlines(b,name)
    fs={f.GetReference():f for f in b.GetFootprints()}
    if name in ('Lower','Upper'):
        f=fs['J103' if name=='Lower' else 'J104'];f.Move(xy(0,1.25))
    if name=='Lower':
        # Keep USB termination near the paired trunks and the optical bypass
        # group next to the sensor pins while opening up hand-assembly gaps.
        for ref,position in {'R6':(33.65,74.75),'R5':(37.6,74.75),
                             'C83':(46.5,50.5),'C85':(46.5,54.5),'C84':(46.5,58.5)}.items():
            fs[ref].SetPosition(xy(*position))
    if name=='Encoder':fs['C62'].SetOrientationDegrees(90);fs['C62'].SetPosition(xy(52.25,56.25))
    env={r:envelope(f) for r,f in fs.items() if active(f)}
    source={r:tuple(p.ToMM(f.GetPosition())) for r,f in fs.items()}
    ps=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(ps,False)
    material=unary_union(polygons(ps));outer=unary_union([Polygon(q.exterior) for q in polygons(ps)])
    inside=prep(outer.buffer(-.75));strict=prep(outer.buffer(-3))
    fixed={r for r in env if r.startswith('J')}
    fixed.update({'Lower':{'U1','U3','U35'},'Upper':{'U7','U8','U9'},'Wheel':set(),'Encoder':{'U27','C62'}}[name])
    if name=='Lower':fixed.update({'R5','R6','C83','C84','C85'})
    if name=='Lower':fixed.discard('J6')
    occupied=[]
    if name=='Lower':
        fs['U35'].BuildCourtyardCaches();occupied.extend(polygons(fs['U35'].GetCourtyard(p.F_CrtYd)))
    for r,f in fs.items():
        if r.startswith('H'):occupied.append(Point(source[r]).buffer(2.5))
    for z in list(b.Zones())+[z for f in b.GetFootprints() for z in f.Zones()]:
        if z.GetIsRuleArea() and 'ANTENNA' in z.GetZoneName().upper():occupied.extend(polygons(z.Outline()))
    placed={}
    for r in sorted(fixed):
        for s in placed:
            assert env[r].distance(placed[s])>=GAP-.00001,(name,'fixed',r,s,env[r].distance(placed[s]))
        placed[r]=env[r]
    occupied.extend(placed.values())
    circled={'R29','R30','R31','R32','R33','R34','R35','R44','C24'} if name=='Upper' else set()
    moving=[r for r in env if r not in fixed]
    moving.sort(key=lambda r:(0 if r.startswith('U') else 1 if not r.startswith(('R','C')) or env[r].area>15 else 2, -env[r].area,r))
    offsets=sorted(((ix*.5,iy*.5) for ix in range(-100,101) for iy in range(-120,121)),key=lambda t:t[0]**2+t[1]**2)
    icrefs=[r for r in env if r.startswith('U')]
    deltas={}
    for r in moving:
        gx,gy=source[r]
        if r in circled:gx+=6;gy+=5
        elif r.startswith(('C','R','L','D')):
            # Keep local circuits near their original IC while allowing useful space.
            anchor=min(icrefs,key=lambda s:math.dist(source[s],source[r]))
            dx,dy=deltas.get(anchor,(0,0));gx+=dx;gy+=dy
        if name=='Upper' and r=='U12':gx+=5;gy+=5
        obstacle=prep(unary_union(occupied).buffer(GAP+.002))
        bounds=env[r].bounds
        found=False
        for dx,dy in offsets:
            tx=gx+dx-source[r][0];ty=gy+dy-source[r][1]
            candidate=translate(env[r],tx,ty)
            if not (strict if r in circled else inside).covers(candidate):continue
            if not material.buffer(-.3).covers(candidate):continue
            if obstacle.intersects(candidate):continue
            fs[r].SetPosition(xy(source[r][0]+tx,source[r][1]+ty));placed[r]=candidate;occupied.append(candidate)
            deltas[r]=(tx,ty);found=True;break
        assert found,(name,'no 2 mm placement',r)
    pairs=sorted((a.distance(c),r,s) for r,a in placed.items() for s,c in placed.items() if r<s)
    assert pairs[0][0]>=GAP-.00001,(name,pairs[0])
    front=prep(unary_union(list(placed.values())).buffer(.8))
    for r,f in fs.items():
        if not r.startswith('TP') or f.IsFlipped():continue
        shape=envelope(f)
        if shape.is_empty or not front.intersects(shape):continue
        for dx,dy in offsets:
            candidate=translate(shape,dx,dy)
            if material.buffer(-.5).covers(candidate) and not front.intersects(candidate):
                f.Move(xy(dx,dy));break
        else:raise RuntimeError('No front test-pad clearance '+r)
    # Routing belongs to the previous placement. Keep only the established USB
    # transmission-line trunks; regenerate other connections from the netlist.
    for t in list(b.GetTracks()):
        keep=name=='Lower' and not isinstance(t,p.PCB_VIA) and t.GetNetname() in ('USB_DP','USB_DM') and t.GetWidth()==p.FromMM(1.1)
        if not keep:b.Remove(t);t.thisown=False
    for f in b.GetFootprints():
        for pad in f.Pads():
            if pad.GetNetname()=='GND':pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL if f.GetReference().startswith('U') else p.ZONE_CONNECTION_INHERITED)
    for z in b.Zones():
        if not z.GetIsRuleArea():z.UnFill()
    b.BuildConnectivity()
    dest=WORK/(name+'-placed.kicad_pcb');p.SaveBoard(str(dest),b)
    report={'minimum_component_gap_mm':pairs[0][0],'closest_pairs':pairs[:12],
            'fixed':sorted(fixed),'moved':{r:list(p.ToMM(f.GetPosition())) for r,f in fs.items() if tuple(p.ToMM(f.GetPosition()))!=source[r]},
            'circled_edge_gaps_mm':{r:placed[r].distance(outer.boundary) for r in circled},
            'board_area_mm2':material.area}
    (WORK/(name+'-placement.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(name,report,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['inventory','place','verify']);ap.add_argument('names',nargs='*');args=ap.parse_args()
    if args.action=='inventory':snapshot();inventory()
    elif args.action=='verify':verify()
    else:
        for name in args.names or BOARDS:place(name)
