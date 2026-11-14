# SPDX-License-Identifier: GPL-3.0-or-later
"""Complete and prune fixed-width routes without changing placement or rules."""
import argparse, collections, math
import rebuild_routes as r
from circuit_routes import shapes, stitch
from shapely.geometry import LineString, Point


def straighten(name):
    """Replace clear signal bends with 45-degree paths while retaining endpoints."""
    path=r.BOARDS[name];before=path.read_bytes();b=r.p.LoadBoard(str(path));b.BuildConnectivity();g=r.CopperGraph(b)
    nets=collections.defaultdict(list)
    for t in b.GetTracks():
        if isinstance(t,r.p.PCB_VIA) or t.GetNetname() in set(r.WIDTHS)|{'GND','USB_DP','USB_DM','ADC2_DECAP'}:continue
        a,z=r.p.ToMM(t.GetStart()),r.p.ToMM(t.GetEnd());dx,dy=abs(a[0]-z[0]),abs(a[1]-z[1])
        if min(dx,dy,abs(dx-dy))>.002:nets[t.GetNetname(),t.GetLayer(),t.GetWidth()].append(t)
    changed=0
    for (net,layer,iw),tracks in nets.items():
        width=r.p.ToMM(iw);avoid=r.obstacles(b,net,layer).buffer(width/2+.151);inside=r.board_interior(b,width/2+.31)
        for t in tracks:
            a,z=tuple(r.p.ToMM(t.GetStart())),tuple(r.p.ToMM(t.GetEnd()));points=[Point(a),Point(z)]
            # Do not move a branch that joins the middle of this segment.
            middle=False
            for k in g.adj.get(r.uid(t),set()):
                ss=shapes(g.items[k]).get(layer)
                if ss is not None and not any(ss.buffer(.002).intersects(pt) for pt in points):middle=True;break
            if middle:continue
            for ps in r.bends(a,z):
                line=LineString(ps)
                if line.length>math.dist(a,z)*1.15+.1:continue
                if r.clear_path(ps,avoid,inside):
                    r.track(b,net,ps,width,layer);b.Remove(t);t.thisown=False;changed+=1;break
    b.BuildConnectivity();r.p.ZONE_FILLER(b).Fill(b.Zones());r.save(b,name);r.check(name)
    d=r.json.loads((r.WORK/(name+'-drc.json')).read_text())
    if d['violations'] and not d['unconnected_items'] and all(v['type'] in ['track_dangling','via_dangling'] for v in d['violations']):
        clean_signals(name);d=r.json.loads((r.WORK/(name+'-drc.json')).read_text())
    if d['violations'] or d['unconnected_items']:
        tmp=path.with_suffix('.restore');tmp.write_bytes(before);tmp.replace(path);r.check(name);print('Straightening retained original: native checks changed.',flush=True)
    else:print('Straightened',changed,'signal segments',flush=True)


def clean_signals(name):
    """Prune signal stubs only when every pad retains its connectivity group."""
    b=r.p.LoadBoard(str(r.BOARDS[name]))
    def signature(net):
        b.BuildConnectivity();g=r.CopperGraph(b);seen=set();result=[]
        for key,q in g.items.items():
            if not isinstance(q,r.p.PAD) or q.GetNetname()!=net or key in seen:continue
            todo=[key];group=set()
            while todo:
                k=todo.pop()
                if k in group:continue
                group.add(k);todo.extend(g.adj.get(k,set())-group)
            seen|=group;result.append(tuple(sorted(k for k in group if isinstance(g.items[k],r.p.PAD))))
        return tuple(sorted(result))
    for attempt in range(20):
        b.BuildConnectivity();r.p.ZONE_FILLER(b).Fill(b.Zones());r.save(b,name);r.check(name)
        d=r.json.loads((r.WORK/(name+'-drc.json')).read_text());ids={i['uuid'] for v in d['violations'] if v['type'] in ['via_dangling','track_dangling'] for i in v['items']}
        changed=0
        for t in list(b.GetTracks()):
            if r.uid(t) not in ids or t.GetNetname() in set(r.WIDTHS)|{'GND','USB_DP','USB_DM'}:continue
            net=t.GetNetname();before=signature(net);b.Remove(t);t.thisown=False
            if signature(net)==before:changed+=1;continue
            b.Add(t);b.BuildConnectivity();g=r.CopperGraph(b)
            if isinstance(t,r.p.PCB_VIA):
                centre=Point(r.p.ToMM(t.GetPosition()));added=[]
                for k in g.adj[r.uid(t)]:
                    q=g.items[k]
                    if not isinstance(q,r.p.PCB_TRACK) or isinstance(q,r.p.PCB_VIA):continue
                    line=LineString([r.p.ToMM(q.GetStart()),r.p.ToMM(q.GetEnd())]);pt=line.interpolate(line.project(centre))
                    if pt.distance(centre)<.002:continue
                    oldids={r.uid(a) for a in b.GetTracks()};r.track(b,net,[tuple(pt.coords[0]),tuple(centre.coords[0])],.15,q.GetLayer())
                    added.extend(a for a in b.GetTracks() if r.uid(a) not in oldids)
                b.Remove(t);t.thisown=False
                if signature(net)==before:changed+=1;continue
                b.Add(t)
                for a in added:b.Remove(a);a.thisown=False
            else:
                line=LineString([r.p.ToMM(t.GetStart()),r.p.ToMM(t.GetEnd())]);ds=[]
                for k in g.adj[r.uid(t)]:
                    q=g.items[k];ss=shapes(q).get(t.GetLayer())
                    if ss is None:continue
                    hit=line.intersection(ss)
                    if not hit.is_empty:ds.append(line.project(hit.centroid))
                if len(ds)>1 and max(ds)-min(ds)>.002:
                    old=(t.GetStart(),t.GetEnd());aa,zz=line.interpolate(min(ds)),line.interpolate(max(ds))
                    t.SetStart(r.xy(aa.x,aa.y));t.SetEnd(r.xy(zz.x,zz.y))
                    if signature(net)==before:changed+=1;continue
                    t.SetStart(old[0]);t.SetEnd(old[1])
        print('Safe signal cleanup',changed,flush=True)
        if not changed:return


def anchors(name):
    """Finish geometric joins at actual via centres and trace centre lines."""
    r.check(name);b=r.p.LoadBoard(str(r.BOARDS[name]));tracks=list(b.GetTracks());added=0
    d=r.json.loads((r.WORK/(name+'-drc.json')).read_text());ids={i['uuid'] for v in d['violations'] if v['type'] in ['via_dangling','track_dangling'] for i in v['items']}
    b.BuildConnectivity();graph=r.CopperGraph(b)
    ids|={j for key in list(ids) for j in graph.adj.get(key,set())}
    for t in tracks:
        if r.uid(t) not in ids:continue
        if isinstance(t,r.p.PCB_VIA) or t.GetNetname() in set(r.WIDTHS)|{'USB_DP','USB_DM','GND'}:continue
        for end in [tuple(r.p.ToMM(t.GetStart())),tuple(r.p.ToMM(t.GetEnd()))]:
            pt=Point(end);choices=[]
            for q in tracks:
                if q==t or q.GetNetname()!=t.GetNetname() or not q.IsOnLayer(t.GetLayer()):continue
                if isinstance(q,r.p.PCB_VIA):
                    z=tuple(r.p.ToMM(q.GetPosition()));d=math.dist(end,z)
                    if .002<d<r.p.ToMM(q.GetWidth(r.p.F_Cu))/2:choices.append((d,z))
                else:
                    ln=LineString([r.p.ToMM(q.GetStart()),r.p.ToMM(q.GetEnd())]);z=ln.interpolate(ln.project(pt));d=pt.distance(z)
                    if .002<d<r.p.ToMM(q.GetWidth())/2:choices.append((d,tuple(z.coords[0])))
            if choices:
                d,z=min(choices);r.track(b,t.GetNetname(),[end,z],min(.15,r.p.ToMM(t.GetWidth())),t.GetLayer());added+=1
    print(name,'copper joins anchored',added,flush=True)
    b.BuildConnectivity();r.p.ZONE_FILLER(b).Fill(b.Zones());r.save(b,name);r.check(name)


def open_ground_link(b,first,last):
    """Prioritize a short ground link over crossing signal copper, including vias."""
    from shapely.ops import nearest_points
    protected=set(r.WIDTHS)|{'USB_DP','USB_DM','ADC2_DECAP','GND'}
    fixed={l:[] for l in [r.p.F_Cu,r.p.B_Cu]}
    for f in b.GetFootprints():
        for q in f.Pads():
            if q.GetNetname()=='GND':continue
            for l,s in shapes(q).items():fixed[l].append(s)
    for t in b.GetTracks():
        if t.GetNetname() in protected-{'GND'}:
            for l,s in shapes(t).items():fixed[l].append(s)
    choices=[]
    for l in first.keys()&last.keys():
        a=first[l].buffer(-.14);z=last[l].buffer(-.14)
        if a.is_empty or z.is_empty:continue
        aa,zz=nearest_points(a,z);aa,zz=tuple(aa.coords[0]),tuple(zz.coords[0])
        for ps in [*r.bends(aa,zz),[aa,zz]]:
            line=LineString(ps);corridor=line.buffer(.276)
            if not r.board_interior(b,.45).covers(line) or r.unary_union(fixed[l]).intersects(corridor):continue
            victims=[t for t in b.GetTracks() if t.GetNetname() not in protected and l in shapes(t) and shapes(t)[l].intersects(corridor)]
            if victims:choices.append((len(victims)*10+line.length,ps,l,victims))
    if not choices:return False
    _,ps,l,victims=min(choices,key=lambda a:a[0])
    for t in victims:b.Remove(t);t.thisown=False
    r.track(b,'GND',ps,.25,l)
    print('Prioritize ground return; reroute',sorted({t.GetNetname() for t in victims}),flush=True);return True


def ground(name):
    """Stitch a spanning forest of overlapping ground regions in batches."""
    import circuit_routes as c
    b=r.p.LoadBoard(str(r.BOARDS[name]));ls=(r.p.F_Cu,r.p.B_Cu)
    for attempt in range(60):
        b.BuildConnectivity();r.p.ZONE_FILLER(b).Fill(b.Zones())
        regions={};trees={}
        for l in ls:
            arr=[s for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname()=='GND' and z.IsOnLayer(l) for s in c.polygons(z.GetFilledPolysList(l))]
            arr += [s for t in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()] if t.GetNetname()=='GND' for lay,s in shapes(t).items() if lay==l]
            u=r.unary_union(arr);regions[l]=list(u.geoms) if hasattr(u,'geoms') else [u];trees[l]=c.STRtree(regions[l])
        parent={(l,i):(l,i) for l in ls for i in range(len(regions[l]))}
        def root(k):
            while parent[k]!=k:k=parent[k]
            return k
        for t in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]:
            if t.GetNetname()!='GND' or not all(t.IsOnLayer(l) for l in ls):continue
            ns=[(l,int(i)) for l in ls for i in trees[l].query(Point(r.p.ToMM(t.GetPosition())),predicate='intersects')]
            for n in ns[1:]:parent[root(n)]=root(ns[0])
        avoid=[]
        for f in b.GetFootprints():
            for q in f.Pads():
                avoid.extend(s.buffer(.17) for s in shapes(q).values())
                if q.GetDrillSize().x:avoid.append(Point(r.p.ToMM(q.GetPosition())).buffer(r.p.ToMM(max(q.GetDrillSize().x,q.GetDrillSize().y))/2+.401))
        avoid += [Point(r.p.ToMM(t.GetPosition())).buffer(.551) for t in b.GetTracks() if isinstance(t,r.p.PCB_VIA)]
        blocked=r.unary_union(avoid);options=[]
        for i,a in enumerate(regions[ls[0]]):
            for j in trees[ls[1]].query(a,predicate='intersects'):
                j=int(j);aa=(ls[0],i);zz=(ls[1],j)
                if root(aa)==root(zz):continue
                safe=a.intersection(regions[ls[1]][j]).buffer(-.251).difference(blocked)
                if not safe.is_empty and safe.area>.005:options.append((safe.area,aa,zz,safe))
        count=0;added=[]
        for _,a,z,safe in sorted(options,key=lambda q:-q[0]):
            if root(a)==root(z):continue
            if added:safe=safe.difference(r.unary_union(added))
            if safe.is_empty:continue
            pt=safe.representative_point();r.via(b,'GND',(pt.x,pt.y),.45,.3);added.append(pt.buffer(.551));parent[root(z)]=root(a);count+=1
        print(name,'ground stitches',count,flush=True)
        if not count:
            components={}
            for k in parent:components.setdefault(root(k),[]).append(k)
            if len(components)<2:break
            ordered=sorted(components.values(),key=lambda ks:-sum(regions[l][i].area for l,i in ks))
            main={l:r.unary_union([regions[ll][i] for ll,i in ordered[0] if ll==l]) for l in ls}
            candidates=[]
            from shapely.ops import nearest_points
            for ks in ordered[1:]:
                for l,i in ks:
                    a=regions[l][i].buffer(-.13)
                    if a.is_empty:a=regions[l][i].buffer(-.03)
                    if a.is_empty:continue
                    for m,dest in main.items():
                        z=dest.buffer(-.13)
                        if z.is_empty:continue
                        aa,zz=nearest_points(a,z)
                        candidates.append((aa.distance(zz),tuple(aa.coords[0]),tuple(zz.coords[0]),ls.index(l),ls.index(m)))
            r.Grid.step=.25;grid=r.Grid(b,'GND',.25)
            for _,a,z,l,m in sorted(candidates)[:30]:
                try:route=grid.route(a,z,(l,),(m,))
                except RuntimeError:continue
                r.add_route(b,'GND',route,.25);count=1;print('Ground bridge',len(route)-1,flush=True);break
            if not count:
                from region_routes import connect
                for ks in ordered[1:]:
                    first={l:r.unary_union([regions[ll][i] for ll,i in ks if ll==l]) for l in ls}
                    first={l:s for l,s in first.items() if not s.is_empty}
                    dest={l:s for l,s in main.items() if not s.is_empty}
                    if connect(b,'GND',first,dest,ls[0],ls[0],width=.25):count=1;break
                    refs=[(f.GetReference(),q.GetNumber()) for f in b.GetFootprints() for q in f.Pads() if q.GetNetname()=='GND' and any(q.IsOnLayer(l) and s.covers(Point(r.p.ToMM(q.GetPosition()))) for l,s in first.items())]
                    print('Isolated ground lands',refs,flush=True)
                    high_current=any(ref in ['J11','Q5','C42','C43'] or (ref=='U21' and pin=='41') for ref,pin in refs)
                    if not high_current and connect(b,'GND',first,dest,ls[0],ls[0],width=.15):count=1;break
                    if connect(b,'GND',first,dest,ls[0],ls[0],ripup=True,width=.25):count=1;break
                    if open_ground_link(b,first,dest):count=1;break
            if not count:print('Ground region needs manual connection',flush=True);break
        r.save(b,name)
    b.BuildConnectivity();r.p.ZONE_FILLER(b).Fill(b.Zones());r.save(b,name);r.check(name)


def region_signals(name):
    """Finish narrow signal corridors at a constant 0.15 mm; no power rip-up."""
    import circuit_routes as c
    from region_routes import connect
    b=r.p.LoadBoard(str(r.BOARDS[name]));r.check(name)
    for attempt in range(40):
        d=r.json.loads((r.WORK/(name+'-drc.json')).read_text());b.BuildConnectivity();g=r.CopperGraph(b)
        findings=[v for v in d['unconnected_items'] if all(i['uuid'] in g.items for i in v['items'])]
        success=False
        for v in findings:
            a,z=[g.items[i['uuid']] for i in v['items']];net=a.GetNetname()
            if net=='GND' or net in r.WIDTHS or net in ['USB_DP','USB_DM']:continue
            first,last=c.island(g,a),c.island(g,z)
            if connect(b,net,first,last,r.p.F_Cu,r.p.F_Cu) or connect(b,net,first,last,r.p.F_Cu,r.p.F_Cu,ripup=True):success=True;break
        if not success:break
        b.BuildConnectivity();r.p.ZONE_FILLER(b).Fill(b.Zones());r.save(b,name);r.check(name)


def reserve_pin(board, pad):
    """Move nearby signal/ground fanouts to reserve a trapped pin exit."""
    net=pad.GetNetname(); point=Point(r.p.ToMM(pad.GetPosition()))
    for radius in [1.25,2.5]:
        moved=[]
        for t in list(board.GetTracks()):
            if t.GetNetname()==net or t.GetNetname() in r.WIDTHS or t.GetNetname() in ('USB_DP','USB_DM','ADC2_DECAP'):continue
            sh=shapes(t)
            if any(s.distance(point)<radius for s in sh.values()):
                moved.append((t,sh));board.Remove(t);t.thisown=False
        before={r.uid(t) for t in board.GetTracks()};end=r.pin_via(board,pad)
        added=[t for t in board.GetTracks() if r.uid(t) not in before];victims=set()
        for t,sh in moved:
            collision=False
            if end is not None:
                collision=any(l in sh and s.buffer(.151).intersects(sh[l]) for a in added for l,s in shapes(a).items())
                if isinstance(t,r.p.PCB_VIA) and math.dist(r.p.ToMM(t.GetPosition()),end)<.51:collision=True
            if collision:victims.add(t.GetNetname())
            else:board.Add(t)
        if end is not None:
            print('RESERVED',net,end,'move',sorted(victims),flush=True);return end
    return None


def groups(board, net):
    board.BuildConnectivity(); g=r.CopperGraph(board); seen=set(); result=[]
    for key,item in g.items.items():
        if not isinstance(item,r.p.PAD) or item.GetNetname()!=net or key in seen:continue
        todo=[key]; component=set()
        while todo:
            k=todo.pop()
            if k in component:continue
            component.add(k);todo.extend(g.adj.get(k,set())-component)
        seen|=component; points=set()
        for k in component:
            t=g.items[k]
            ls=tuple(i for i,l in enumerate([r.p.F_Cu,r.p.B_Cu]) if t.IsOnLayer(l))
            pts=[r.p.ToMM(t.GetPosition())] if not isinstance(t,r.p.PCB_TRACK) or isinstance(t,r.p.PCB_VIA) else [r.p.ToMM(t.GetStart()),r.p.ToMM(t.GetEnd())]
            points.update((tuple(pt),ls) for pt in pts)
        result.append(points)
    return result


def signals(name):
    r.check(name);b=r.p.LoadBoard(str(r.BOARDS[name]))
    d=r.json.loads((r.WORK/(name+'-drc.json')).read_text())
    items={r.uid(t):t for t in b.GetTracks()}
    items.update({r.uid(q):q for f in b.GetFootprints() for q in f.Pads()})
    nets={items[i['uuid']].GetNetname() for v in d['unconnected_items'] for i in v['items'] if i['uuid'] in items}-{'GND'}
    assert not(nets & set(r.WIDTHS))
    for net in sorted(nets):
        print('JOIN',name,net,flush=True)
        for attempt in range(12):
            gs=groups(b,net)
            if len(gs)<2:break
            pairs=sorted((math.dist(a[0],c[0]),i,j,a,c) for i,g in enumerate(gs) for j,h in enumerate(gs) if i<j for a in g for c in h)
            success=False
            for step in [.25]:
                r.Grid.step=step;grid=r.Grid(b,net,.15); tried=set()
                for _,i,j,a,c in pairs:
                    # Try distinct accessible contacts, not just the nearest via.
                    if (i,j) in tried:continue
                    try:route=grid.route(a[0],c[0],a[1],c[1],sources=gs[i],targets=gs[j])
                    except RuntimeError:
                        tried.add((i,j));continue
                    r.add_route(b,net,route,.15);r.save(b,name)
                    print('JOINED',net,step,len(route)-1,flush=True);success=True;break
                if success:break
            if not success:
                print('OPEN',net,len(gs),flush=True);break
    b.BuildConnectivity();r.p.ZONE_FILLER(b).Fill(b.Zones());r.save(b,name);r.check(name)


def prune(name):
    """Remove native-identified redundant stubs; never route missing nets here."""
    b=r.p.LoadBoard(str(r.BOARDS[name]))
    for _ in range(30):
        b.BuildConnectivity();r.p.ZONE_FILLER(b).Fill(b.Zones());r.save(b,name);r.check(name)
        d=r.json.loads((r.WORK/(name+'-drc.json')).read_text())
        before=r.BOARDS[name].read_bytes();open_count=len(d['unconnected_items'])
        ids={i['uuid'] for v in d['violations'] if v['type'] in ('track_dangling','via_dangling') for i in v['items']}
        if not ids:return
        graph=r.CopperGraph(b)
        for t in list(b.GetTracks()):
            if r.uid(t) not in ids:continue
            contacts=[graph.items[k] for k in graph.adj.get(r.uid(t),())]
            if not isinstance(t,r.p.PCB_VIA) and r.p.ToMM(t.GetLength())>.4 and len(contacts)>1:
                line=LineString([r.p.ToMM(t.GetStart()),r.p.ToMM(t.GetEnd())]);ds=[]
                for other in contacts:
                    if isinstance(other,r.p.PCB_TRACK) and not isinstance(other,r.p.PCB_VIA):
                        hit=line.intersection(LineString([r.p.ToMM(other.GetStart()),r.p.ToMM(other.GetEnd())]))
                        if not hit.is_empty:
                            if hit.geom_type=='Point':ds.append(line.project(hit))
                            elif hit.geom_type=='LineString':ds.extend(line.project(Point(q)) for q in [hit.coords[0],hit.coords[-1]])
                        else:ds.append(line.project(Point(r.p.ToMM(other.GetPosition()))))
                    else:ds.append(line.project(Point(r.p.ToMM(other.GetPosition()))))
                if len(ds)>1 and max(ds)-min(ds)>.001:
                    a=line.interpolate(min(ds));c=line.interpolate(max(ds))
                    t.SetStart(r.xy(a.x,a.y));t.SetEnd(r.xy(c.x,c.y));continue
            b.Remove(t);t.thisown=False
        b.BuildConnectivity();r.p.ZONE_FILLER(b).Fill(b.Zones());r.save(b,name);r.check(name)
        after=r.json.loads((r.WORK/(name+'-drc.json')).read_text())
        if len(after['unconnected_items'])>open_count:
            temporary=r.BOARDS[name].with_suffix('.kicad_pcb.restore')
            temporary.write_bytes(before);temporary.replace(r.BOARDS[name]);r.check(name)
            print('Retained copper bridge: removing it would break connectivity; inspect its endpoint joins.',flush=True)
            return
    raise RuntimeError('Stub cleanup did not converge')


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=['signals','prune','stitch','regions','ground','anchors','clean','straighten']);a.add_argument('board',choices=['Lower','Upper','Wheel']);args=a.parse_args()
    {'signals':signals,'prune':prune,'stitch':stitch,'regions':region_signals,'ground':ground,'anchors':anchors,'clean':clean_signals,'straighten':straighten}[args.action](args.board)
