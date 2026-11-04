"""Checked local two-layer path repair for remaining Wheel connections.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import sys, math, heapq, json, subprocess, collections
from pathlib import Path
from standard_vias import BOARDS, SCRATCH, obstacles, smd_shapes, intersections, p, xy, track, via, Point, LineString, unary_union
from route_main import CLI
import numpy as np
from shapely import intersects_xy, prepared

STEP=.05

def route_pair(b,net,start,end,start_layer,end_layer):
    foreign=[obstacles(b,net,layer) for layer in (p.F_Cu,p.B_Cu)]
    avoid=[shape.buffer(.15+.127/2+.001) for shape in foreign]
    ready=[prepared.prep(shape) for shape in avoid]
    xs=np.arange(0,55+STEP/2,STEP);ys=np.arange(0,60+STEP/2,STEP)
    nx=len(xs);ny=len(ys);xx,yy=np.meshgrid(xs,ys)
    blocked=np.stack([intersects_xy(shape,xx,yy) for shape in avoid])
    pad_block=unary_union([s for *_,s in smd_shapes(b)]).buffer(.251)
    holes=[]
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA):holes.append(Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetDrillValue())/2+.15+.251))
    for f in b.GetFootprints():
        for pad in f.Pads():
            if pad.GetDrillSize().x:holes.append(Point(p.ToMM(pad.GetPosition())).buffer(p.ToMM(max(pad.GetDrillSize().x,pad.GetDrillSize().y))/2+.15+.251))
    via_avoid=unary_union([pad_block,*holes,*[s.buffer(.15+.225+.001) for s in foreign]])
    blocked_via=intersects_xy(via_avoid,xx,yy)
    # An existing same-net via is already a valid layer transition. Do not
    # treat its drill keepout as a barrier to traversing the existing route.
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA) and t.GetNetname()==net:
            vx,vy=p.ToMM(t.GetPosition());i,j=round(vx/STEP),round(vy/STEP)
            blocked_via[j,i]=False
    def point(i,j):return (round(i*STEP,6),round(j*STEP,6))
    def clear(a,c,l):return not ready[l].intersects(LineString([a,c]))
    def key(i,j,l):return (l*ny+j)*nx+i
    def decode(k):i=k%nx;k//=nx;return i,k%ny,k//ny
    starts=[]
    si,sj=round(start[0]/STEP),round(start[1]/STEP)
    for i in range(si-3,si+4):
        for j in range(sj-3,sj+4):
            if 0<i<nx-1 and 0<j<ny-1 and not blocked[start_layer,j,i] and clear(start,point(i,j),start_layer):starts.append((i,j,start_layer))
    if not starts:return None
    queue=[];cost={};prev={};iterations=0
    for i,j,l in starts:
        k=key(i,j,l);g=math.dist(start,point(i,j));cost[k]=g;heapq.heappush(queue,(g+math.dist(point(i,j),end),g,k))
    while queue:
        _,g,k=heapq.heappop(queue)
        if g>cost.get(k,1e9)+1e-8:continue
        i,j,l=decode(k);a=point(i,j);iterations+=1
        if l==end_layer and math.dist(a,end)<=.22 and clear(a,end,l):
            route=[(end,l),(a,l)]
            while k in prev:k=prev[k];u,v,w=decode(k);route.append((point(u,v),w))
            route.append((start,start_layer));route.reverse()
            simplified=[];chunk=[];last=None
            for pt,layer in route:
                if last is not None and layer!=last:
                    simplified.extend(simplify(chunk,last,clear));chunk=[]
                chunk.append(pt);last=layer
            simplified.extend(simplify(chunk,last,clear))
            print('Path',net,'nodes',iterations,'length',round(g,2),'points',len(simplified),flush=True)
            return simplified
        neighbors=[]
        for di,dj in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            u=i+di;v=j+dj
            if not (1<u<nx-2 and 1<v<ny-2) or blocked[l,v,u]:continue
            if di and dj and (blocked[l,j,u] or blocked[l,v,i]):continue
            neighbors.append((u,v,l,STEP*math.hypot(di,dj)))
        if not blocked_via[j,i] and not blocked[1-l,j,i]:neighbors.append((i,j,1-l,2.0))
        for u,v,w,delta in neighbors:
            nk=key(u,v,w);ng=g+delta
            if ng>=cost.get(nk,1e9):continue
            cost[nk]=ng;prev[nk]=k;h=math.dist(point(u,v),end)+(0 if w==end_layer else .5)
            heapq.heappush(queue,(ng+h,ng,nk))
        if iterations>1500000:break
    print('No path',net,start,end,'nodes',iterations,flush=True)
    return None

def simplify(points,layer,clear):
    out=[(points[0],layer)];i=0
    while i<len(points)-1:
        j=len(points)-1
        while j>i+1 and not clear(points[i],points[j],layer):j-=1
        out.append((points[j],layer));i=j
    return out

def add_path(b,net,path):
    for (a,la),(c,lc) in zip(path,path[1:]):
        if la!=lc:
            assert math.dist(a,c)<1e-7
            existing=next((v for v in b.GetTracks() if isinstance(v,p.PCB_VIA) and v.GetNetname()==net and math.dist(a,p.ToMM(v.GetPosition()))<.04),None)
            if existing:
                for layer in (p.F_Cu,p.B_Cu):track(b,net,[a,tuple(p.ToMM(existing.GetPosition()))],.127,layer)
            else:via(b,net,a,.45,.3)
        else:track(b,net,[a,c],.127,p.F_Cu if la==0 else p.B_Cu)

def check(b):
    path=BOARDS['Wheel'];b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
    subprocess.run([str(CLI),'pcb','drc','--format','json','--schematic-parity','-o',str(SCRATCH/'Wheel-repair-drc.json'),str(path)],check=True,stdout=subprocess.DEVNULL)
    return json.loads((SCRATCH/'Wheel-repair-drc.json').read_text())

def main():
    b=p.LoadBoard(str(BOARDS['Wheel']));report=check(b);changes=[]
    # Remove unused fanout vias and new ground stitches in newly routed space.
    bad=set()
    for violation in report['violations']:
        for item in violation['items']:
            if violation['type'] in ('clearance','hole_to_hole') and 'Via [GND]' in item['description']:bad.add(item['uuid'])
    for t in list(b.GetTracks()):
        if t.m_Uuid.AsString() in bad and isinstance(t,p.PCB_VIA):b.Remove(t);t.thisown=False
    report=check(b)
    for iteration in range(30):
        items={t.m_Uuid.AsString():t for t in b.GetTracks()}
        items.update({pad.m_Uuid.AsString():pad for f in b.GetFootprints() for pad in f.Pads()})
        usable=[v for v in report['unconnected_items'] if all(i['uuid'] in items for i in v['items'])]
        if not usable:break
        success=False
        for finding in usable:
            a,c=[items[i['uuid']] for i in finding['items']];net=a.GetNetname()
            start=tuple(p.ToMM(a.GetPosition()));end=tuple(p.ToMM(c.GetPosition()))
            la=0 if a.IsOnLayer(p.F_Cu) else 1;lc=0 if c.IsOnLayer(p.F_Cu) else 1
            path=route_pair(b,net,start,end,la,lc)
            if path:
                add_path(b,net,path);changes.append(dict(net=net,points=path));success=True;break
        if not success:break
        report=check(b);print('Remaining',len(report['unconnected_items']),'violations',collections.Counter(v['type'] for v in report['violations']),flush=True)
    (SCRATCH/'wheel-path-repairs.json').write_text(json.dumps(changes,indent=2)+'\n')
    print('Final',len(report['unconnected_items']),len(report['violations']),'via-in-pad',len(intersections(b)),flush=True)

if __name__=='__main__':main()
