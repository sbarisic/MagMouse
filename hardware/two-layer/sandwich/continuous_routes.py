"""Geometry-based local routing helpers for the standard-via Wheel revision.

Saved KiCad boards are authoritative; these helpers do not replay the migration.
Run native DRC and refill copper after applying a returned path.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import sys,heapq,math,collections
from pathlib import Path
from repair_wheel import *
from shapely import constrained_delaunay_triangles
from shapely.geometry import box
from export_quote import polygons


def board_interior(b,margin=.4):
 outline=p.SHAPE_POLY_SET()
 assert b.GetBoardPolygonOutlines(outline,False)
 return unary_union(polygons(outline)).buffer(-margin)

def continuous(b,net,start,end,layer):
 avoid=obstacles(b,net,layer).buffer(.2145);interior=board_interior(b);free=interior.difference(avoid)
 regions=list(free.geoms) if hasattr(free,'geoms') else [free]
 region=next((q for q in regions if q.covers(Point(start)) and q.covers(Point(end))),None)
 if region is None:return None
 triangles=list(constrained_delaunay_triangles(region).geoms);edges={};graph=collections.defaultdict(list);centers=[tuple(t.centroid.coords[0]) for t in triangles]
 for i,t in enumerate(triangles):
  pts=list(t.exterior.coords)[:3]
  for a,c in zip(pts,pts[1:]+pts[:1]):
   k=tuple(sorted((tuple(a),tuple(c))))
   if k in edges:
    j=edges[k];m=((a[0]+c[0])/2,(a[1]+c[1])/2);graph[i].append((j,m));graph[j].append((i,m))
   else:edges[k]=i
 first=next(i for i,t in enumerate(triangles) if t.covers(Point(start)));last=next(i for i,t in enumerate(triangles) if t.covers(Point(end)))
 queue=[(0,first)];cost={first:0};prev={}
 while queue:
  d,i=heapq.heappop(queue)
  if i==last:break
  if d>cost[i]:continue
  for j,m in graph[i]:
   nd=d+math.dist(centers[i],m)+math.dist(m,centers[j])
   if nd<cost.get(j,1e20):cost[j]=nd;prev[j]=(i,m);heapq.heappush(queue,(nd,j))
 else:return None
 pts=[end,centers[last]];i=last
 while i!=first:
  i,m=prev[i];pts.extend([m,centers[i]])
 pts.append(start);pts.reverse()
 # Inset centers are safe; boundary midpoints can touch the conservative buffer.
 ready=prepared.prep(avoid.buffer(-.00001))
 result=simplify(pts,layer,lambda a,c,l:interior.covers(LineString([a,c])) and not ready.intersects(LineString([a,c])))
 print('Continuous',net,len(triangles),'triangles',len(result),'points',flush=True)
 return result

def fanout(b,ref,num):
 pad=next(q for f in b.GetFootprints() if f.GetReference()==ref for q in f.Pads() if q.GetNumber()==num);net=pad.GetNetname();start=tuple(p.ToMM(pad.GetPosition()))
 foreign={l:obstacles(b,net,l) for l in (p.F_Cu,p.B_Cu)};favoid=foreign[p.F_Cu].buffer(.2145)
 drilled=[Point(p.ToMM(q.GetPosition())).buffer(p.ToMM(max(q.GetDrillSize().x,q.GetDrillSize().y))/2+.401) for f in b.GetFootprints() for q in f.Pads() if q.GetDrillSize().x]
 avoid=unary_union([unary_union([s for *_,s in smd_shapes(b)]).buffer(.151),*[s.buffer(.376) for s in foreign.values()],*[Point(p.ToMM(q.GetPosition())).buffer(.551) for q in b.GetTracks() if isinstance(q,p.PCB_VIA)],*drilled])
 interior=board_interior(b)
 candidates=[(round(start[0]+ix*.025,6),round(start[1]+iy*.025,6)) for ix in range(-100,101) for iy in range(-100,101)]
 candidates.sort(key=lambda q:math.dist(start,q))
 for end in candidates:
  if interior.covers(Point(end)) and not avoid.intersects(Point(end)) and not favoid.intersects(LineString([start,end])):
   via(b,net,end,.45,.3);track(b,net,[start,end],.127,p.F_Cu);print('fanout',ref,num,end,flush=True);return end
 free=interior.difference(favoid);regions=list(free.geoms) if hasattr(free,'geoms') else [free];region=next((q for q in regions if q.covers(Point(start))),None)
 if region is None:return None
 for end in candidates:
  if region.covers(Point(end)) and not avoid.intersects(Point(end)):
   path=continuous(b,net,start,end,p.F_Cu)
   if path:
    via(b,net,end,.45,.3)
    for (a,l),(c,_) in zip(path,path[1:]):track(b,net,[a,c],.127,p.F_Cu)
    return end
 return None
