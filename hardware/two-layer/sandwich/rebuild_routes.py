"""Rebuild routing with fixed-width power trees before 45-degree signal routing.

Run with KiCad Python. Saved boards remain authoritative. Temporary snapshots
are for rollback during this operation and are not manufacturing deliverables.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import argparse, collections, hashlib, heapq, json, math, re, shutil, sys
from pathlib import Path
import numpy as np
from circuit_fixes import BOARDS, p
from route_main import ROOT, HERE, CLI, xy, track, via
from standard_vias import obstacles, smd_shapes
from continuous_routes import board_interior
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
from shapely import contains_xy, prepared
from copper_graph import CopperGraph, uid
from kicad_output import run as atomic_run

WORK=ROOT/'build/route-rebuild'
WIDTHS={'ACT_5V':1.0,'PWR_5V':1.0,'VBUS_USB':1.0,'+3V3':.5,
        'BUCK_SW':.6,'OPT_3V3':.35,'OPT_1V9':.35,'RGB_5V':.5,
        'WHEEL_PHASE_A':.75,'WHEEL_PHASE_B':.75,'WHEEL_PHASE_C':.75,
        'BRAKE_DRAIN':1.0,'DRV_AVDD':.35,'WHEEL_BUCK_SW':.35,
        'WHEEL_BUCK_OUT':.35,'WHEEL_CP':.35,'WHEEL_CPH':.25,'WHEEL_CPL':.25}

def save(b,name):
    b.BuildConnectivity()
    p.SaveBoard(str(BOARDS[name]),b)

def snapshot(name):
    WORK.mkdir(parents=True,exist_ok=True)
    folder=WORK/name;folder.mkdir(exist_ok=True)
    for suffix in ('.kicad_pcb','.kicad_pro'):
        dest=folder/(name+suffix)
        if not dest.exists():shutil.copy2(BOARDS[name].with_suffix(suffix),dest)

def bends(a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];m=min(abs(dx),abs(dy))
    sx,sy=math.copysign(1,dx),math.copysign(1,dy)
    for c in [(a[0]+sx*m,a[1]+sy*m),(b[0]-sx*m,b[1]-sy*m),
              (a[0],b[1]),(b[0],a[1])]:
        pts=[a,c,b];yield [q for i,q in enumerate(pts) if i==0 or q!=pts[i-1]]

def clear_path(pts,avoid,inside):
    line=LineString(pts)
    return inside.covers(line) and not avoid.intersects(line)

def padmap(b):return {(f.GetReference(),q.GetNumber()):q for f in b.GetFootprints() for q in f.Pads()}

def critical(b,name):
    pads=padmap(b)
    def route(a,z,pts,width):
        q,r=pads[a],pads[z];assert q.GetNetname()==r.GetNetname()
        track(b,q.GetNetname(),[tuple(p.ToMM(q.GetPosition())),*pts,tuple(p.ToMM(r.GetPosition()))],width)
    if name=='Lower':
        route(('U2','2'),('U2','3'),[],.25)
        track(b,'PWR_5V',[(51.05,27.75),(50.1,27.75)],.25)
        track(b,'PWR_5V',[(50.1,27.75),(49.775,27.425),(49.775,23.91)],.6)
        track(b,'BUCK_SW',[(52.95,27.75),(53.6,27.75),(54.4,26.95)],.25)
        track(b,'BUCK_SW',[(54.4,26.95),(56.8463,26.95),(57.7063,27.81)],.6)
        route(('U35','5'),('C86','1'),[(43.495,51.04)],.35)
        route(('U35','4'),('C83','1'),[(44.525,52.82)],.35)
        route(('U35','3'),('C85','1'),[(42.495,54.6)],.35)
        route(('C85','1'),('C84','1'),[],.35)
    if name=='Wheel':
        route(('U21','6'),('C47','2'),[(23.105,27.75)],.25)
        route(('U21','7'),('C47','1'),[(23.105,28.25)],.25)
        route(('U21','25'),('C48','1'),[(31.585,28.75)],.25)
        route(('U23','8'),('C58','1'),[(25.25,11.475)],.25)
        # Adjacent motor supply and phase pins share only a short pin escape.
        for pins in [('9','10','11'),('13','14'),('16','17'),('19','20')]:
            for a,c in zip(pins,pins[1:]):route(('U21',a),('U21',c),[],.25)

def escape(b,pad,width):
    """A short, constant-width IC pin escape, never a long narrow power trunk."""
    net=pad.GetNetname();a=tuple(p.ToMM(pad.GetPosition()))
    inside=board_interior(b,.35)
    layer=p.F_Cu if pad.IsOnLayer(p.F_Cu) else p.B_Cu
    foreign=obstacles(b,net,layer)
    if min(p.ToMM(pad.GetSize()))>=width and not foreign.buffer(width/2+.17).intersects(Point(a)):return a
    f=pad.GetParentFootprint();centre=tuple(p.ToMM(f.GetPosition()))
    dx,dy=a[0]-centre[0],a[1]-centre[1]
    directions=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    directions.sort(key=lambda d:-(dx*d[0]+dy*d[1])/math.hypot(*d))
    for length in [1.5,1.25,1.75,2.,1.,.8,.6]:
        for d in directions:
            q=(a[0]+length*d[0]/math.hypot(*d),a[1]+length*d[1]/math.hypot(*d))
            if foreign.buffer(width/2+.17).intersects(Point(q)):continue
            for w in [.25,.15]:
                if clear_path([a,q],foreign.buffer(w/2+.17),inside):
                    track(b,net,[a,q],w,layer)
                    # Reserve the full-width end before routing other supplies.
                    track(b,net,[q,(q[0]+.001,q[1])],width,layer)
                    return q
    offsets=np.arange(-2.5,2.501,.05)
    xx,yy=np.meshgrid(a[0]+offsets,a[1]+offsets,indexing='ij')
    radius=(xx-a[0])**2+(yy-a[1])**2
    mask=(radius>=.5**2)&(radius<=2.5**2)&contains_xy(inside,xx,yy)&~contains_xy(foreign.buffer(width/2+.17),xx,yy)
    candidates=[(round(float(xx[i,j]),6),round(float(yy[i,j]),6)) for i,j in zip(*np.where(mask))]
    candidates.sort(key=lambda q:math.dist(a,q))
    for w in (.25,.15):
        avoid=foreign.buffer(w/2+.17)
        for q in candidates:
            for pts in bends(a,q):
                if clear_path(pts,avoid,inside):
                    track(b,net,pts,w,layer)
                    track(b,net,[q,(q[0]+.001,q[1])],width,layer)
                    print('Bent power escape',f.GetReference(),pad.GetNumber(),net,w,q,flush=True)
                    return q
    raise RuntimeError(f'No short power escape {f.GetReference()}.{pad.GetNumber()} {net}')

def power_escape_room(b,pad,width):
    # Move conflicting short signal/ground fanouts, never reduce a power trunk.
    net=pad.GetNetname();a=Point(p.ToMM(pad.GetPosition()));movable=[]
    for t in list(b.GetTracks()):
        if t.GetNetname() in WIDTHS or t.GetNetname() in ('USB_DP','USB_DM','ADC2_DECAP'):continue
        sh=Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2) if isinstance(t,p.PCB_VIA) else LineString([p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2)
        if sh.distance(a)<2.5:movable.append((t,sh));b.Remove(t);t.thisown=False
    before={uid(t) for t in b.GetTracks()}
    try:end=escape(b,pad,width)
    except RuntimeError:
        for t,sh in movable:b.Add(t)
        return None
    added=[t for t in b.GetTracks() if uid(t) not in before]
    corridor=unary_union([LineString([p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2+.17) for t in added])
    victims=[]
    for t,sh in movable:
        if corridor.intersects(sh):victims.append(t.GetNetname())
        else:b.Add(t)
    print('Power pin corridor',pad.GetParentFootprint().GetReference(),pad.GetNumber(),'relocate',sorted(set(victims)),flush=True)
    return end

class Grid:
    step=.25
    def __init__(self,b,net,width):
        self.b,self.net,self.width=b,net,width
        self.layers=(p.F_Cu,p.B_Cu);self.inside=board_interior(b,width/2+.32)
        self.raw=[obstacles(b,net,l) for l in self.layers]
        self.avoid=[q.buffer(width/2+(.15 if width<=.15 else .17)) for q in self.raw]
        x0,y0,x1,y1=self.inside.bounds
        self.x0=math.floor(x0/self.step)*self.step;self.y0=math.floor(y0/self.step)*self.step
        self.nx=math.ceil((x1-self.x0)/self.step)+1;self.ny=math.ceil((y1-self.y0)/self.step)+1
        self.xs=self.x0+np.arange(self.nx)*self.step;self.ys=self.y0+np.arange(self.ny)*self.step
        xx,yy=np.meshgrid(self.xs,self.ys,indexing='ij')
        material=contains_xy(self.inside,xx,yy)
        self.free=[material & ~contains_xy(q,xx,yy) for q in self.avoid]
        forbidden=[s.buffer(.17) for *_,s in smd_shapes(b)]
        for f in b.GetFootprints():
            for q in f.Pads():
                if q.GetDrillSize().x:forbidden.append(Point(p.ToMM(q.GetPosition())).buffer(p.ToMM(max(q.GetDrillSize().x,q.GetDrillSize().y))/2+.42))
        for t in b.GetTracks():
            if isinstance(t,p.PCB_VIA):forbidden.append(Point(p.ToMM(t.GetPosition())).buffer(.56))
        forbidden.extend(q.buffer(.38 if width<=.5 else .47) for q in self.raw)
        self.viafree=contains_xy(board_interior(b,(.225 if width<=.5 else .3)+.32),xx,yy) & ~contains_xy(unary_union(forbidden),xx,yy)
        self.ready=[prepared.prep(q) for q in self.avoid]
    def pos(self,k):return (float(self.xs[k[0]]),float(self.ys[k[1]]))
    def terminals(self,point,layers):
        ix=round((point[0]-self.x0)/self.step);iy=round((point[1]-self.y0)/self.step)
        opts=[]
        for dx in range(-10,11):
            for dy in range(-10,11):
                i,j=ix+dx,iy+dy
                if not(0<=i<self.nx and 0<=j<self.ny):continue
                for l in layers:
                    if not self.free[l][i,j]:continue
                    q=self.pos((i,j))
                    for pts in bends(point,q):
                        if len(pts)==1 or clear_path(pts,self.avoid[l],self.inside):
                            opts.append((sum(math.dist(a,c) for a,c in zip(pts,pts[1:])),(i,j,l),pts));break
        return sorted(opts,key=lambda q:q[0])[:12]
    def route(self,a,c,al=(0,),cl=(0,),sources=None,targets=None):
        # Prefer a direct short route on a shared layer.
        for l in set(al)&set(cl):
            for pts in bends(a,c):
                if clear_path(pts,self.avoid[l],self.inside):return [(q,l) for q in pts]
        starts=[t for pt,ls in (sources or [(a,al)]) for t in self.terminals(pt,ls)]
        ends={}
        for pt,ls in (targets or [(c,cl)]):
            for d,k,pts in self.terminals(pt,ls):
                if k not in ends or d<ends[k][0]:ends[k]=(d,pts)
        if not starts or not ends:raise RuntimeError(f'{self.net}: inaccessible terminal {a} {c}')
        def heuristic(k):
            q=self.pos(k)
            return min(max(abs(q[0]-pt[0]),abs(q[1]-pt[1]))+.41421356237*min(abs(q[0]-pt[0]),abs(q[1]-pt[1])) for pt,ls in (targets or [(c,cl)]))
        queue=[];cost={};prev={};roots={}
        for d,k,pts in starts:
            if d<cost.get(k,1e20):cost[k]=d;roots[k]=pts;heapq.heappush(queue,(d+heuristic(k),d,k))
        goal=None
        moves=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
        while queue:
            _,g,k=heapq.heappop(queue)
            if g>cost[k]+1e-8:continue
            if k in ends:goal=k;break
            i,j,l=k;point=self.pos(k)
            for dx,dy in moves:
                ni,nj=i+dx,j+dy
                if not(0<=ni<self.nx and 0<=nj<self.ny) or not self.free[l][ni,nj]:continue
                nk=(ni,nj,l);ng=g+self.step*math.hypot(dx,dy)*(1.02 if l==0 else 1.)
                if ng>=cost.get(nk,1e20):continue
                if self.ready[l].intersects(LineString([point,self.pos(nk)])):continue
                cost[nk]=ng;prev[nk]=k;heapq.heappush(queue,(ng+heuristic(nk),ng,nk))
            nk=(i,j,1-l);ng=g+4
            if self.free[1-l][i,j] and self.viafree[i,j] and ng<cost.get(nk,1e20):
                cost[nk]=ng;prev[nk]=k;heapq.heappush(queue,(ng+heuristic(nk),ng,nk))
        if goal is None:raise RuntimeError(f'No fixed-width power route {self.net} {a} {c}')
        nodes=[goal];k=goal
        while k in prev:k=prev[k];nodes.append(k)
        nodes.reverse();pts=[(q,k[2]) for q in roots[k]]+[(self.pos(q),q[2]) for q in nodes]+[(q,goal[2]) for q in reversed(ends[goal][1])]
        # Replace grid staircases with clear straight/45-degree sections only.
        out=[pts[0]];i=0
        while i<len(pts)-1:
            end=i+1
            while end+1<len(pts) and pts[end+1][1]==pts[i][1]:end+=1
            chosen=None
            for j in range(end,i,-1):
                if pts[j][1]!=pts[i][1]:continue
                for shape in bends(pts[i][0],pts[j][0]):
                    if len(shape)==1 or clear_path(shape,self.avoid[pts[i][1]],self.inside):chosen=(j,shape);break
                if chosen:break
            if chosen:
                j,shape=chosen;out.extend((q,pts[i][1]) for q in shape[1:]);i=j
            else:out.append(pts[i+1]);i+=1
        return out

def add_route(b,net,route,width):
    for (a,l),(c,m) in zip(route,route[1:]):
        if l==m:track(b,net,[a,c],width,(p.F_Cu,p.B_Cu)[l])
        else:assert a==c;via(b,net,a,.45 if width<=.5 else .6,.3)

def pin_via(b,pad,outward=False):
    net=pad.GetNetname();start=tuple(p.ToMM(pad.GetPosition()))
    layer=p.F_Cu if pad.IsOnLayer(p.F_Cu) else p.B_Cu
    foreign={l:obstacles(b,net,l) for l in (p.F_Cu,p.B_Cu)}
    forbidden=[v.buffer(.17) for *_,v in smd_shapes(b)]
    forbidden.extend(v.buffer(.38) for v in foreign.values())
    for f in b.GetFootprints():
        for q in f.Pads():
            if q.GetDrillSize().x:forbidden.append(Point(p.ToMM(q.GetPosition())).buffer(p.ToMM(max(q.GetDrillSize().x,q.GetDrillSize().y))/2+.42))
    forbidden.extend(Point(p.ToMM(t.GetPosition())).buffer(.56) for t in b.GetTracks() if isinstance(t,p.PCB_VIA))
    blocked=prepared.prep(unary_union(forbidden));inside=board_interior(b,.55)
    offsets=np.arange(-2.5,2.501,.05)
    xx,yy=np.meshgrid(start[0]+offsets,start[1]+offsets,indexing='ij')
    radius=(xx-start[0])**2+(yy-start[1])**2
    mask=(radius<=2.5**2)&contains_xy(inside,xx,yy)&~contains_xy(unary_union(forbidden),xx,yy)
    if outward:
        cx,cy=p.ToMM(pad.GetParentFootprint().GetPosition());dx,dy=start[0]-cx,start[1]-cy
        if abs(dx)>abs(dy):mask &= (xx-start[0])*math.copysign(1,dx)>=.5
        else:mask &= (yy-start[1])*math.copysign(1,dy)>=.5
    candidates=[(round(float(xx[i,j]),6),round(float(yy[i,j]),6)) for i,j in zip(*np.where(mask))]
    candidates.sort(key=lambda q:math.dist(start,q))
    for width in (.15,.127):
        avoid=foreign[layer].buffer(width/2+.151)
        for end in candidates:
            if width==.127 and math.dist(start,end)>1.5:continue
            for pts in bends(start,end):
                if clear_path(pts,avoid,inside):
                    before={uid(t) for t in b.GetTracks()}
                    track(b,net,pts,width,layer);via(b,net,end,.45,.3)
                    for t in b.GetTracks():
                        if uid(t) not in before:t.SetLocked(True)
                    print('Pin escape',pad.GetParentFootprint().GetReference(),pad.GetNumber(),net,width,end,flush=True)
                    return end
    return None

def negotiated_escape(b,pad):
    # Reserve an IC escape before restoring nearby signal paths. Power,
    # USB, drills and previously reserved pin escapes remain fixed.
    net=pad.GetNetname();start=Point(p.ToMM(pad.GetPosition()))
    layer=p.F_Cu if pad.IsOnLayer(p.F_Cu) else p.B_Cu
    movable=[]
    for t in list(b.GetTracks()):
        if isinstance(t,p.PCB_VIA) or t.IsLocked() or t.GetLayer()!=layer:continue
        if t.GetNetname()==net or t.GetNetname() in WIDTHS or t.GetNetname() in ('GND','USB_DP','USB_DM'):continue
        shape=LineString([p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2)
        if shape.distance(start)<3.5:movable.append((t,shape));b.Remove(t);t.thisown=False
    before={uid(t) for t in b.GetTracks()}
    end=pin_via(b,pad)
    additions=[t for t in b.GetTracks() if uid(t) not in before]
    corridors=[]
    for t in additions:
        if isinstance(t,p.PCB_VIA):corridors.append(Point(p.ToMM(t.GetPosition())).buffer(.38))
        else:corridors.append(LineString([p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2+.151))
    corridor=unary_union(corridors);victims=[]
    for t,shape in movable:
        if end is not None and corridor.intersects(shape):victims.append(t.GetNetname())
        else:b.Add(t)
    if victims:print('Make room for pin escape:',net,'displaced',sorted(set(victims)),flush=True)
    return end

TERMINALS={}

def power_net(b,net,width,only_escape=False):
    if not only_escape:
        terminals=TERMINALS.get(net,[])
        if len(terminals)<2:return
        return power_tree(b,net,width,terminals)
    pads=[q for f in b.GetFootprints() for q in f.Pads() if q.GetNetname()==net]
    if len(pads)<2:return
    b.BuildConnectivity();graph=CopperGraph(b)
    seen=set();groups=[]
    for pad in pads:
        key=uid(pad)
        if key in seen:continue
        todo=[key];group=set()
        while todo:
            k=todo.pop()
            if k in group:continue
            group.add(k);todo.extend(graph.adj.get(k,())-group)
        seen|=group;groups.append([q for q in pads if uid(q) in group])
    if len(groups)<2:return
    # Start from connector/capacitor groups; use one escape for an already
    # connected group of supply pins instead of redundant parallel fanouts.
    groups.sort(key=lambda g:min(0 if q.GetParentFootprint().GetReference().startswith('J') else 1 if q.GetParentFootprint().GetReference().startswith('C') else 2 for q in g))
    terminals=[]
    for group in groups:
        if width<=.15:
            component=set();todo=[uid(group[0])]
            while todo:
                k=todo.pop()
                if k in component:continue
                component.add(k);todo.extend(graph.adj.get(k,())-component)
            existing=[graph.items[k] for k in component if isinstance(graph.items[k],p.PCB_VIA)]
            outside=[q for q in pads if q not in group]
            if existing:
                v=min(existing,key=lambda v:min(math.dist(p.ToMM(v.GetPosition()),p.ToMM(q.GetPosition())) for q in outside))
                terminals.append((tuple(p.ToMM(v.GetPosition())),(0,1)));continue
            small=[q for q in group if q.GetParentFootprint().GetReference().startswith('U')]
            if small:
                end=pin_via(b,small[0])
                if end is None:end=negotiated_escape(b,small[0])
                if end is not None:terminals.append((end,(0,1)));continue
        candidates=sorted(group,key=lambda q:-min(p.ToMM(q.GetSize())))
        chosen=None
        for q in candidates:
            try:
                point=escape(b,q,width) if q.GetAttribute()==p.PAD_ATTRIB_SMD else tuple(p.ToMM(q.GetPosition()))
                chosen=(point,(0,1) if q.GetAttribute()==p.PAD_ATTRIB_PTH else ((0,) if q.IsOnLayer(p.F_Cu) else (1,)));break
            except RuntimeError:continue
        if chosen is None and width>.15:
            for q in candidates:
                point=power_escape_room(b,q,width)
                if point is not None:chosen=(point,(0,));break
        if chosen is None:raise RuntimeError(f'Cannot escape {net}: {[q.GetParentFootprint().GetReference()+q.GetNumber() for q in group]}')
        terminals.append(chosen)
    TERMINALS[net]=terminals

def power_tree(b,net,width,terminals):
    connected={0};pending=set(range(1,len(terminals)))
    while pending:
        pairs=sorted((math.dist(terminals[i][0],terminals[j][0]),i,j) for i in connected for j in pending)
        grid=Grid(b,net,width)
        for _,i,j in pairs:
            try:route=grid.route(terminals[i][0],terminals[j][0],terminals[i][1],terminals[j][1])
            except RuntimeError:continue
            add_route(b,net,route,width);connected.add(j);pending.remove(j)
            print(net,'branch',j,'width',width,'segments',len(route)-1,flush=True);break
        else:raise RuntimeError(f'Unroutable fixed-width power net {net}: {pending}')

def prepare(name):
    snapshot(name)
    b=p.LoadBoard(str(BOARDS[name]));original=p.LoadBoard(str(WORK/name/(name+'.kicad_pcb')))
    for t in list(b.GetTracks()):b.Remove(t);t.thisown=False
    if name=='Lower':
        for t in original.GetTracks():
            if t.GetNetname() in ('USB_DP','USB_DM'):
                q=t.Duplicate();q.SetParent(b);q.SetNet(b.FindNet(t.GetNetname()));b.Add(q)
    for z in b.Zones():
        if not z.GetIsRuleArea():z.UnFill()
    critical(b,name)
    counts=collections.Counter(q.GetNetname() for f in b.GetFootprints() for q in f.Pads())
    # Reserve ALL fine-pitch IC exits before allocating wide power corridors.
    # This also gives the ground plane short, explicit local return vias.
    for f in sorted(b.GetFootprints(),key=lambda f:f.GetReference()):
        if not f.GetReference().startswith('U'):continue
        for q in f.Pads():
            net=q.GetNetname()
            if not net or not q.GetNumber():continue
            if q.GetAttribute()!=p.PAD_ATTRIB_SMD or min(p.ToMM(q.GetSize()))>.9:continue
            if net in WIDTHS or net in ('USB_DP','USB_DM','ADC2_DECAP') or counts[net]<2 or net.startswith('unconnected-'):continue
            end=pin_via(b,q)
            if end is None:print('Review pin exit:',f.GetReference(),q.GetNumber(),net,flush=True)
    save(b,name)
    shutil.copy2(BOARDS[name],WORK/name/(name+'-fanouts.kicad_pcb'))
    for net,width in WIDTHS.items():power_net(b,net,width,only_escape=True)
    order=sorted(WIDTHS,key=lambda n:0 if n.startswith("WHEEL_PHASE_") else 1 if n=="ACT_5V" else 2)
    for net in order:
        power_net(b,net,WIDTHS[net])
        save(b,name)
    shutil.copy2(BOARDS[name],WORK/name/(name+'-prepared.kicad_pcb'))
    export(name)

def resume_power(name):
    b=p.LoadBoard(str(BOARDS[name]))
    for net,width in WIDTHS.items():
        power_net(b,net,width,only_escape=True)
        power_net(b,net,width)
        save(b,name)
    shutil.copy2(BOARDS[name],WORK/name/(name+'-prepared.kicad_pcb'))
    export(name)

def remove_expr(text,pattern):
    match=re.search(pattern,text)
    if not match:return text
    depth=0
    for i in range(match.start(),len(text)):
        if text[i]=='(':depth+=1
        elif text[i]==')':
            depth-=1
            if depth==0:return text[:match.start()]+text[i+1:]
    raise ValueError('Unbalanced Specctra expression')

def export(name):
    b=p.LoadBoard(str(BOARDS[name]));path=WORK/(name+'.dsn')
    assert p.ExportSpecctraDSN(b,str(path))
    s=path.read_text()
    # Preserve GND plane connectivity; route foreign nets with plane_as_obstacle=false.
    # Retain GND pin membership so protected ground escapes remain same-net copper.
    # All power is pre-routed. Remaining signals have one width; preserving
    # existing narrow IC escapes avoids asking a wide netclass to enter a QFN.
    s=re.sub(r'\(width \d+(?:\.\d+)?\)', '(width 150)',s[:s.index('  (wiring')])+s[s.index('  (wiring'):]
    s=re.sub(r'\(clearance \d+(?:\.\d+)?\)', '(clearance 150)',s)
    s=s.replace('(type route)','(type protect)')
    # Keep via drilling at 0.30 mm and use 0.60 mm lands for new signal vias.
    # Preserve each existing via land size, including 0.45 mm pin fanouts.
    path.write_text(s)

def imported(name):
    b=p.LoadBoard(str(BOARDS[name]));assert p.ImportSpecctraSES(b,str(WORK/(name+'.ses')))
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA):t.SetDrill(p.FromMM(.3))
        elif t.GetNetname() not in ('USB_DP','USB_DM') and t.GetWidth()<p.FromMM(.15):t.SetWidth(p.FromMM(.15))
    if name=='Lower':
        old=p.LoadBoard(str(WORK/name/(name+'.kicad_pcb')))
        for t in list(b.GetTracks()):
            if t.GetNetname() in ('USB_DP','USB_DM'):b.Remove(t);t.thisown=False
        for t in old.GetTracks():
            if t.GetNetname() in ('USB_DP','USB_DM'):
                q=t.Duplicate();q.SetParent(b);q.SetNet(b.FindNet(t.GetNetname()));b.Add(q)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());save(b,name)
    check(name)

def check(name):
    out=WORK/(name+'-drc.json')
    atomic_run(CLI,['pcb','drc','--format','json','--schematic-parity','-o',out,BOARDS[name]],check=True)
    d=json.loads(out.read_text());print(name,collections.Counter(v['type'] for v in d['violations']),len(d['unconnected_items']),'unconnected',len(d['schematic_parity']),'parity',flush=True)


def repair_signals(name):
    check(name)
    b=p.LoadBoard(str(BOARDS[name]));d=json.loads((WORK/(name+'-drc.json')).read_text())
    items={uid(t):t for t in b.GetTracks()}
    items.update({uid(q):q for f in b.GetFootprints() for q in f.Pads()})
    badwidth={t.GetNetname() for t in b.GetTracks() if not isinstance(t,p.PCB_VIA) and p.ToMM(t.GetWidth())<.12699}
    nets=set(badwidth)
    for v in d['unconnected_items']:
        nets.update(items[i['uuid']].GetNetname() for i in v['items'] if i['uuid'] in items)
    nets-={'GND','USB_DP','USB_DM'}
    assert not (nets & set(WIDTHS)), ('Incomplete protected power route',nets & set(WIDTHS))
    for t in list(b.GetTracks()):
        if t.GetNetname() in badwidth:b.Remove(t);t.thisown=False
    # Fixed-width, octilinear whole-net routes. Never widen a maze afterwards.
    for net in sorted(nets):
        try:
            power_net(b,net,.15,only_escape=True)
            power_net(b,net,.15)
        except RuntimeError as ex:print('OPEN:',ex,flush=True)
        save(b,name)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());save(b,name);check(name)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=['prepare','export','import','check','repair-signals','resume-power']);a.add_argument('board',choices=['Lower','Upper','Wheel']);args=a.parse_args()
    {'prepare':prepare,'export':export,'import':imported,'check':check,'repair-signals':repair_signals,'resume-power':resume_power}[args.action](args.board)
