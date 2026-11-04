"""Migrate the routed boards to JLCPCB's standard 0.30 mm via drill tier.

Run with KiCad Python. Preserve source snapshots under ignored build/.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import argparse, collections, hashlib, json, shutil, sys, math, heapq
from pathlib import Path
import pcbnew as p
from route_main import HERE, ROOT, xy, track, via
from export_quote import BOARDS, polygons
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
from shapely import prepared

SCRATCH=ROOT/'build/sandwich/cost-reduction'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def smd_shapes(board):
    result=[]
    for f in board.GetFootprints():
        for pad in f.Pads():
            if pad.GetAttribute()!=p.PAD_ATTRIB_SMD: continue
            shape=p.SHAPE_POLY_SET()
            pad.TransformShapeToPolygon(shape,pad.GetLayer(),0,p.FromMM(.001),p.ERROR_OUTSIDE)
            result.append((f.GetReference(),pad.GetNumber(),pad.GetNetname(),unary_union(polygons(shape))))
    return result

def intersections(board, margin=0):
    pads=smd_shapes(board); result=[]
    for v in board.GetTracks():
        if not isinstance(v,p.PCB_VIA): continue
        hole=Point(p.ToMM(v.GetPosition())).buffer(p.ToMM(v.GetDrillValue())/2+margin)
        hits=[ref+'.'+num for ref,num,net,shape in pads if shape.intersects(hole)]
        if hits: result.append(dict(uuid=v.m_Uuid.AsString(),xy_mm=list(p.ToMM(v.GetPosition())),net=v.GetNetname(),pads=hits))
    return result

def convert():
    SCRATCH.mkdir(parents=True,exist_ok=True)
    report={}
    for name,path in BOARDS.items():
        backup=SCRATCH/(name+'-before.kicad_pcb')
        assert not backup.exists(), 'Migration already started; use saved snapshots, not a second baseline'
        shutil.copy2(path,backup);shutil.copy2(path.with_suffix('.kicad_pro'),backup.with_suffix('.kicad_pro'))
        project=json.loads(path.with_suffix('.kicad_pro').read_text())
        rules=project['board']['design_settings']['rules']
        # JLCPCB's advertised standard drill/pad pair is 0.30/0.45 mm.
        # This is an explicit fabrication rule change, not an ignored DRC check.
        rules['min_through_hole_diameter']=.3
        rules['min_via_annular_width']=.075
        # Published JLCPCB capability: via hole to track >= 0.20 mm.
        rules['min_hole_clearance']=.2
        for c in project['net_settings']['classes']:
            c['via_drill']=max(.3,c['via_drill'])
        for v in project['board']['design_settings'].get('via_dimensions',[]):
            v['drill']=max(.3,v['drill'])
        path.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
        b=p.LoadBoard(str(path));changed=0
        for v in b.GetTracks():
            if isinstance(v,p.PCB_VIA) and v.GetDrillValue()<p.FromMM(.3):
                v.SetDrill(p.FromMM(.3));changed+=1
        b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
        report[name]=dict(before_sha256=sha(backup),changed_drills=changed,via_in_pad=intersections(b))
        print(name,json.dumps(report[name]),flush=True)
    (SCRATCH/'conversion.json').write_text(json.dumps(report,indent=2)+'\n')

def obstacles(board,net,layer):
    result=[]
    for f in board.GetFootprints():
        for pad in f.Pads():
            if pad.GetNetname()==net or not pad.IsOnLayer(layer):continue
            shape=p.SHAPE_POLY_SET();pad.TransformShapeToPolygon(shape,layer,0,p.FromMM(.001),p.ERROR_OUTSIDE)
            result.extend(polygons(shape))
    for t in board.GetTracks():
        if t.GetNetname()==net:continue
        if isinstance(t,p.PCB_VIA): result.append(Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetWidth(layer))/2))
        elif t.GetLayer()==layer:result.append(LineString([p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2))
    for z in list(board.Zones())+[z for f in board.GetFootprints() for z in f.Zones()]:
        if z.GetIsRuleArea() and z.GetDoNotAllowTracks() and z.GetLayerSet().Contains(layer):result.extend(polygons(z.Outline()))
    return unary_union(result)

def local_path(start,end,avoid,radius=4):
    blocked=prepared.prep(avoid)
    def clear(a,b): return not blocked.intersects(LineString([a,b]))
    if clear(start,end):return [start,end]
    step=.1
    goal=(round((end[0]-start[0])/step),round((end[1]-start[1])/step))
    def pos(k):return (start[0]+k[0]*step,start[1]+k[1]*step)
    queue=[(0,0,(0,0))];cost={(0,0):0};prev={}
    while queue:
        _,g,k=heapq.heappop(queue)
        if g>cost[k]+1e-7:continue
        a=pos(k)
        if math.dist(a,end)<.25 and clear(a,end):
            path=[end,a]
            while k in prev:k=prev[k];path.append(pos(k))
            path=list(reversed(path));simple=[path[0]];i=0
            while i<len(path)-1:
                j=len(path)-1
                while j>i+1 and not clear(path[i],path[j]):j-=1
                simple.append(path[j]);i=j
            return simple
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            q=(k[0]+dx,k[1]+dy)
            if max(abs(q[0]),abs(q[1]))>radius/step:continue
            b=pos(q);ng=g+math.hypot(dx,dy)*step
            if ng>=cost.get(q,1e9) or not clear(a,b):continue
            cost[q]=ng;prev[q]=k;heapq.heappush(queue,(ng+math.dist(b,end),ng,q))
    return None

def relocate_wheel():
    path=BOARDS['Wheel'];b=p.LoadBoard(str(path));affected=intersections(b,margin=.1)
    smd=unary_union([s for *_,s in smd_shapes(b)]).buffer(.251)
    items={v.m_Uuid.AsString():v for v in b.GetTracks() if isinstance(v,p.PCB_VIA)}
    changes=[]
    # Redundant pad-centred GND vias are replaced by off-pad stitches after fill.
    for item in affected:
        if item['net']=='GND':
            v=items[item['uuid']];b.Remove(v);v.thisown=False
            changes.append({**item,'action':'remove ground via; restore off-pad stitching'})
    for item in affected:
        if item['net']=='GND':continue
        v=items[item['uuid']];start=tuple(p.ToMM(v.GetPosition()));net=v.GetNetname()
        foreign={layer:obstacles(b,net,layer) for layer in (p.F_Cu,p.B_Cu)}
        avoid={layer:foreign[layer].buffer(.15+.127/2+.002) for layer in foreign}
        via_avoid=unary_union([smd,*[s.buffer(.15+p.ToMM(v.GetWidth(p.F_Cu))/2+.002) for s in foreign.values()]])
        holes=unary_union([Point(p.ToMM(q.GetPosition())).buffer((p.ToMM(q.GetDrillValue())+.3)/2+.251)
            for q in b.GetTracks() if isinstance(q,p.PCB_VIA) and q!=v])
        candidates=[]
        for ix in range(-40,41):
            for iy in range(-40,41):
                q=(round(start[0]+ix*.05,6),round(start[1]+iy*.05,6));pt=Point(q)
                if not via_avoid.intersects(pt) and not holes.intersects(pt):candidates.append(q)
        candidates.sort(key=lambda q:math.dist(start,q));solution=None
        # Prefer straight bridges on both layers; then permit a short local detour.
        for q in candidates:
            if all(not avoid[layer].intersects(LineString([start,q])) for layer in avoid):
                solution=(q,{layer:[start,q] for layer in avoid});break
        if solution is None:
            for q in candidates[:120]:
                paths={layer:local_path(start,q,avoid[layer]) for layer in avoid}
                if all(paths.values()):solution=(q,paths);break
        if solution is None:
            print('NO LOCAL SOLUTION',item,flush=True);continue
        q,paths=solution;v.SetPosition(xy(*q))
        for layer,points in paths.items():track(b,net,points,.127,layer)
        changes.append({**item,'action':'move and bridge on both copper layers','to_xy_mm':q,'bridges':paths})
        print('Moved',net,start,'->',q,flush=True)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
    (SCRATCH/'wheel-relocations.json').write_text(json.dumps(changes,indent=2)+'\n')
    print('Remaining',json.dumps(intersections(b)),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['convert','inspect','relocate-wheel']);args=parser.parse_args()
    if args.action=='convert':convert()
    elif args.action=='relocate-wheel':relocate_wheel()
    else:
        for name,path in BOARDS.items(): print(name,json.dumps(intersections(p.LoadBoard(str(path))),indent=2),flush=True)
