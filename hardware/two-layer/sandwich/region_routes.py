"""Connect two copper islands using continuous free-space regions on two layers.

This is a local repair helper, not a replacement for native KiCad DRC.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import collections,heapq,math
from continuous_routes import continuous,board_interior
from standard_vias import p,obstacles,smd_shapes
from route_main import track,via
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
from shapely import STRtree

RIP_HISTORY=collections.Counter()

def parts(shape):
 return [g for g in (shape.geoms if hasattr(shape,'geoms') else [shape]) if g.geom_type=='Polygon' and not g.is_empty]

def connect(b,net,start,end,start_layer,end_layer,ripup=False):
 start_shapes=start if isinstance(start,dict) else None;end_shapes=end if isinstance(end,dict) else None
 if start_shapes:start=tuple(unary_union(list(start_shapes.values())).centroid.coords[0])
 if end_shapes:end=tuple(unary_union(list(end_shapes.values())).centroid.coords[0])
 layers=(p.F_Cu,p.B_Cu);foreign={l:obstacles(b,net,l) for l in layers};inside=board_interior(b)
 regions={l:parts(inside.difference(foreign[l].buffer(.2145))) for l in layers}
 trees={l:STRtree(regions[l]) for l in layers}
 def owner(pt,l):
  matches=trees[l].query(Point(pt),predicate='intersects')
  return (l,int(matches[0])) if len(matches) else None
 def endpoints(shapes,point,layer):
  if shapes is None:
   node=owner(point,layer);return {node:point} if node is not None else {}
  result={}
  for l,area in shapes.items():
   for i,region in enumerate(regions[l]):
    overlap=region.intersection(area).buffer(-.002)
    if not overlap.is_empty:result[l,i]=tuple(overlap.representative_point().coords[0])
  return result
 firsts=endpoints(start_shapes,start,start_layer);lasts=endpoints(end_shapes,end,end_layer)
 if not firsts or not lasts:return False
 holes=[Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetDrillValue())/2+.401) for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
 holes += [Point(p.ToMM(q.GetPosition())).buffer(p.ToMM(max(q.GetDrillSize().x,q.GetDrillSize().y))/2+.401) for f in b.GetFootprints() for q in f.Pads() if q.GetDrillSize().x]
 blocked=unary_union([unary_union([s for *_,s in smd_shapes(b)]).buffer(.151),*holes,*[f.buffer(.376) for f in foreign.values()]])
 allowed=board_interior(b,.526).difference(blocked)
 graph=collections.defaultdict(list);guide=LineString([start,end]) if start!=end else Point(start)
 def edge(pt,existing):
  a,c=[owner(pt,l) for l in layers]
  if a is not None and c is not None:
   weight=2+.01*(math.dist(start,pt)+math.dist(pt,end))
   graph[a].append((c,pt,existing,weight));graph[c].append((a,pt,existing,weight))
 for polygon in parts(allowed):
  safe=polygon.buffer(-.002)
  if safe.is_empty:continue
  point=nearest_points(safe,guide)[0];edge(tuple(point.coords[0]),False)
 for item in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]:
  if item.GetNetname()==net and item.IsOnLayer(p.F_Cu) and item.IsOnLayer(p.B_Cu):edge(tuple(p.ToMM(item.GetPosition())),True)
 # Optional negotiated repair: open a short crossing through movable signal
 # copper, then route that displaced net in a later native-DRC repair pass.
 if ripup:
  from export_quote import polygons
  fixed={l:[] for l in layers};movable={l:[] for l in layers}
  for f in b.GetFootprints():
   for pad in f.Pads():
    if pad.GetNetname()==net:continue
    for l in layers:
     if pad.IsOnLayer(l):
      poly=p.SHAPE_POLY_SET();pad.TransformShapeToPolygon(poly,l,0,p.FromMM(.001),p.ERROR_OUTSIDE);fixed[l].extend(polygons(poly))
  for t in b.GetTracks():
   if t.GetNetname()==net:continue
   if isinstance(t,p.PCB_VIA):
    for l in layers:fixed[l].append(Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetWidth(l))/2))
   else:
    l=t.GetLayer();sh=LineString([p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2)
    if t.GetNetname() in ('USB_DP','USB_DM','GND') or p.ToMM(t.GetWidth())>.3:fixed[l].append(sh)
    else:movable[l].append((t,sh))
  for l in layers:
   avoid=unary_union(fixed[l]).buffer(.2145);mt=STRtree([sh for t,sh in movable[l]])
   for t,sh in movable[l]:
    a,c=map(lambda q:tuple(p.ToMM(q)),(t.GetStart(),t.GetEnd()));length=math.dist(a,c)
    if length<.05:continue
    nx,ny=-(c[1]-a[1])/length,(c[0]-a[0])/length;offset=p.ToMM(t.GetWidth())/2+.23
    count=max(1,math.ceil(length/.7))
    for i in range(count):
     x,y=(a[k]+(c[k]-a[k])*(i+.5)/count for k in (0,1));aa=(x+nx*offset,y+ny*offset);cc=(x-nx*offset,y-ny*offset)
     an,cn=owner(aa,l),owner(cc,l)
     if an is None or cn is None or an==cn:continue
     line=LineString([aa,cc])
     if avoid.intersects(line) or not inside.covers(line):continue
     cuts=tuple(int(j) for j in mt.query(line.buffer(.2145),predicate='intersects'))
     victims=tuple(movable[l][j][0] for j in cuts)
     weight=100*len(victims)+sum(p.ToMM(v.GetLength())+1000*RIP_HISTORY[v.GetNetname()] for v in victims)
     graph[an].append((cn,victims,'rip',weight));graph[cn].append((an,victims,'rip',weight))
 queue=[(0,first) for first in firsts];heapq.heapify(queue);cost={first:0 for first in firsts};prev={}
 while queue:
  d,node=heapq.heappop(queue)
  if node in lasts:break
  if d>cost[node]:continue
  for other,pt,existing,w in graph[node]:
   new=d+w
   if new<cost.get(other,1e30):cost[other]=new;prev[other]=(node,pt,existing);heapq.heappush(queue,(new,other))
 else:
  print('No region path',net,'regions',len(regions[p.F_Cu]),len(regions[p.B_Cu]),'portal nodes',len(graph),flush=True);return False
 end=lasts[node];end_layer=node[0];transitions=[]
 while node in prev:
  old,pt,existing=prev[node];transitions.append((old[0],node[0],pt,existing));node=old
 start=firsts[node];start_layer=node[0]
 transitions.reverse();pending=[];at=start;layer=start_layer
 victims={t.m_Uuid.AsString():t for old,new,pt,existing in transitions if existing=='rip' for t in pt}
 if victims:
  for t in victims.values():b.Remove(t);t.thisown=False
  RIP_HISTORY.update(t.GetNetname() for t in victims.values())
  print('Negotiated ripup',net,[(t.GetNetname(),t.m_Uuid.AsString()) for t in victims.values()],flush=True)
  if connect(b,net,start,end,start_layer,end_layer):return True
  for t in victims.values():b.Add(t)
  return False
 for old,new,pt,existing in transitions:
  route=continuous(b,net,at,pt,layer) if at!=pt else [(at,layer)]
  if route is None:return False
  pending.append((route,pt,existing));at=pt;layer=new
 route=continuous(b,net,at,end,layer) if at!=end else [(at,layer)]
 if route is None:return False
 pending.append((route,None,True))
 for route,pt,existing in pending:
  for (a,l),(c,_) in zip(route,route[1:]):track(b,net,[a,c],.127,l)
  if pt is not None and not existing:via(b,net,pt,.45,.3)
 print('Region route',net,'layer changes',len(transitions),flush=True);return True
