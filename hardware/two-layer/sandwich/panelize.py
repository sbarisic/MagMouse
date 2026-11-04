"""Derive a four-design, two-layer quotation panel without changing unit copper.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import collections, hashlib, json, re, subprocess, sys, uuid, zipfile
from pathlib import Path
import pcbnew as p
from route_main import HERE, ROOT, CLI, xy
from export_quote import BOARDS
sys.path.insert(0,str(ROOT/'build/two-layer/python'))
sys.path.insert(0,str(ROOT/'hardware/bench'))
import build_panel as bp
from router_geometry import make_routable, verify_panel as verify_router, verify_material_tab
from shapely.geometry import Point, Polygon, box
from shapely.affinity import translate
from shapely.ops import unary_union
from shapely import set_precision

OUT=HERE/'panel'
SIZE=(238,114)
ORIGINS={'Lower':(7,7),'Upper':(84,7),'Wheel':(161,7),'Encoder':(161,81)}
TARGETS={'Lower':[(24.75,0),(48.75,0),(0,63),(70,63)],
         'Upper':[(24.75,0),(45.75,0),(0,63),(70,63)],
         'Wheel':[(4.765331,-3),(62.5,35),(13.207003,64),(43.207003,64)],
         'Encoder':[(57,50),(64,57)]}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def stable(item,key):bp.UUID_REPLACEMENTS[item.m_Uuid.AsString()]=str(uuid.uuid5(uuid.NAMESPACE_URL,'MagMouse/sandwich-panel/'+key))
def track_key(t,offset=(0,0),prefix=''):
    v=isinstance(t,p.PCB_VIA);dx,dy=offset
    return (prefix+t.GetNetname(),t.GetStart().x+dx,t.GetStart().y+dy,t.GetEnd().x+dx,t.GetEnd().y+dy,
            t.GetWidth(p.F_Cu) if v else t.GetWidth(),t.GetDrillValue() if v else 0,t.GetLayer())
def fill_vertices(board,offset=(0,0),prefix=''):
    result=collections.Counter();dx,dy=offset
    for z in board.Zones():
        if z.GetIsRuleArea():continue
        for layer in (p.F_Cu,p.B_Cu):
            if not z.IsOnLayer(layer):continue
            shape=z.GetFilledPolysList(layer)
            for i in range(shape.OutlineCount()):
                for c in [shape.Outline(i),*[shape.Hole(i,h) for h in range(shape.HoleCount(i))]]:
                    for j in range(c.PointCount()):
                        a=c.CPoint(j);result[(prefix+z.GetNetname(),layer,a.x+dx,a.y+dy)]+=1
    return result
def pad_key(pad,offset=(0,0),prefix=''):
    dx,dy=offset
    return (pad.GetNumber(),pad.GetPosition().x+dx,pad.GetPosition().y+dy,pad.GetSize().x,pad.GetSize().y,
            pad.GetDrillSize().x,pad.GetDrillSize().y,pad.GetLayerSet().FmtHex(),prefix+pad.GetNetname() if pad.GetNetCode() else '')

def build():
    OUT.mkdir(exist_ok=True)
    (OUT/'fp-lib-table').write_text((BOARDS['Lower'].parent/'fp-lib-table').read_text())
    sections=[s for s in bp.root_sections(BOARDS['Lower'].read_text())
              if s.split()[0] in ('(version','(generator','(generator_version','(general','(paper','(layers','(setup')]
    dest=OUT/'Panel.kicad_pcb';dest.write_text('(kicad_pcb\n'+'\n'.join(sections)+'\n)\n')
    project=json.loads(BOARDS['Lower'].with_suffix('.kicad_pro').read_text());project['meta']['filename']='Panel.kicad_pro'
    dest.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
    panel=p.LoadBoard(str(dest));units={};tabs=[];manifest={};expected_tracks=collections.Counter();expected_fill=collections.Counter();expected_pads={}
    for name,path in BOARDS.items():
        b=p.LoadBoard(str(path));assert b.GetCopperLayerCount()==2
        unit=bp.outline(b);ox=ORIGINS[name][0]-unit.bounds[0];oy=ORIGINS[name][1]-unit.bounds[1];offset=xy(ox,oy)
        units[name]=translate(unit,ox,oy)
        assert box(0,0,*SIZE).buffer(-5).covers(units[name])
        netmap={0:panel.FindNet(0)}
        for code,net in b.GetNetsByNetcode().items():
            if code:
                n=p.NETINFO_ITEM(panel,name+'/'+net.GetNetname());panel.Add(n);netmap[code]=n
        for f in b.GetFootprints():
            ref=name[0]+'_'+f.GetReference();item=bp.duplicate(f);item.SetParent(panel);panel.Add(item);item.Move(offset);item.SetReference(ref);stable(item,name+'/'+f.GetReference())
            for i,(old,pad) in enumerate(zip(f.Pads(),item.Pads())):pad.SetNet(netmap[old.GetNetCode()]);stable(pad,ref+'/pad/'+str(i))
            for kind,children in [('graphic',item.GraphicalItems()),('field',item.GetFields()),('zone',item.Zones())]:
                for i,child in enumerate(children):stable(child,ref+'/'+kind+'/'+str(i))
            expected_pads[ref]=collections.Counter(pad_key(pad,tuple(offset),name+'/') for pad in f.Pads())
        for collection in (b.GetTracks(),b.Zones(),b.GetDrawings()):
            for old in collection:
                if isinstance(old,p.PCB_SHAPE) and old.GetLayer()==p.Edge_Cuts:continue
                item=bp.duplicate(old);item.SetParent(panel);panel.Add(item)
                if hasattr(item,'SetNet'):item.SetNet(netmap[old.GetNetCode()])
                item.Move(offset);stable(item,name+'/'+old.m_Uuid.AsString())
        candidates=bp.tab_candidates(b,unit);chosen=[]
        for target in TARGETS[name]:
            usable=[c for c in candidates if all(Point(c['center']).distance(Point(t['center']))>=8 for t in chosen)]
            best=min(usable,key=lambda c:Point(c['center']).distance(Point(target)))
            assert Point(best['center']).distance(Point(target))<=1.01,(name,target)
            chosen.append(best)
        for i,t in enumerate(chosen):
            t={**t,'board':name,'index':i+1,'center':[t['center'][0]+ox,t['center'][1]+oy],
               'polygon':[(x+ox,y+oy) for x,y in t['polygon']],'holes':[(x+ox,y+oy) for x,y in t['holes']]};tabs.append(t)
        expected_tracks.update(track_key(t,tuple(offset),name+'/') for t in b.GetTracks());expected_fill.update(fill_vertices(b,tuple(offset),name+'/'))
        manifest[name]=dict(source=str(path.relative_to(ROOT)),sha256=sha(path),translation_mm=[ox,oy],footprints=len(list(b.GetFootprints())),tracks_and_vias=len(list(b.GetTracks())))
    for a,poly in units.items():
        for other,q in units.items():
            if a!=other:assert poly.distance(q)>=7-1e-6
    # Internal optical apertures are routed empty, not filled with isolated
    # panel-waste islands. Reserve the full outer envelope of each unit here.
    waste=box(0,0,*SIZE).difference(unary_union([Polygon(q.exterior).buffer(2,quad_segs=128) for q in units.values()])).buffer(-1,quad_segs=128).buffer(1,quad_segs=128)
    for t in tabs:bp.verify_tab_bridge(t,units[t['board']],waste)
    material=unary_union([waste,*units.values(),*[Polygon(t['polygon']) for t in tabs]])
    assert material.geom_type=='Polygon' and material.is_valid
    material,router=make_routable(material)
    material=set_precision(material.simplify(.00025,preserve_topology=True),.000001)
    for ring in [material.exterior,*material.interiors]:
        for a,b in zip(ring.coords,list(ring.coords)[1:]):bp.add_segment(panel,a,b)
    for i,t in enumerate(tabs):
        verify_material_tab(material,t)
        for j,(x,y) in enumerate(t['holes']):
            assert all(Point(x,y).buffer(.3).distance(q)>=.199 for q in units.values())
            bp.add_hole(panel,x,y,.6,f'MB{i+1}_{j+1}')
    for i,(x,y) in enumerate([(2.5,2.5),(SIZE[0]-2.5,2.5),(2.5,SIZE[1]-2.5),(SIZE[0]-2.5,SIZE[1]-2.5)]):bp.add_hole(panel,x,y,2,f'TOOL{i+1}')
    # Existing helper-generated outline/hole IDs are normalized as well.
    panel.BuildConnectivity();p.SaveBoard(str(dest),panel)
    raw=dest.read_text();raw=re.sub(r'\(uuid "([^"]+)"\)',lambda m:'(uuid "'+bp.UUID_REPLACEMENTS.get(m[1],m[1])+'")',raw);dest.write_text(raw)
    panel=p.LoadBoard(str(dest));p.SaveBoard(str(dest),panel)
    # Check exact translated pads, drills, tracks and saved zone vertices.
    assert expected_tracks==collections.Counter(track_key(t) for t in panel.GetTracks()),'Panel track/drill translation differs'
    assert expected_fill==fill_vertices(panel),'Panel copper fill differs from sources'
    for f in panel.GetFootprints():
        if f.GetReference() in expected_pads:assert expected_pads[f.GetReference()]==collections.Counter(pad_key(pad) for pad in f.Pads())
    panel.BuildConnectivity();assert panel.GetConnectivity().GetUnconnectedCount(False)==0,'Panel connectivity'
    verify_router(bp.outline(panel),router)
    for name,path in BOARDS.items():assert sha(path)==manifest[name]['sha256']
    data=dict(status='QUOTATION PANEL / NOT PRODUCTION RELEASE',size_mm=SIZE,designs=4,units=manifest,tabs=tabs,
              routing_gap_mm=2,mousebite_diameter_mm=.6,mousebite_pitch_mm=.9,tab_width_mm=5,router=router,
              exact_translated_pads_tracks_drills_and_zone_copper=True,native_unconnected=0,sha256=sha(dest))
    (OUT/'panel-manifest.json').write_text(json.dumps(data,indent=2)+'\n')
    # Mechanical drawing is derived from the exact panel polygons.
    paths=['M '+' L '.join(f'{x:.5f},{y:.5f}' for x,y in ring.coords)+' Z' for ring in [material.exterior,*material.interiors]]
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1904" height="912" viewBox="0 0 {SIZE[0]} {SIZE[1]}">',
         '<rect width="100%" height="100%" fill="#101822"/>','<path d="'+' '.join(paths)+'" fill="#24404a" fill-rule="evenodd" stroke="#c4d7dd" stroke-width=".12"/>']
    colors={'Lower':'#59b4c5','Upper':'#dd9d43','Wheel':'#82c993','Encoder':'#bc9fe2'}
    for name,q in units.items():
        unitpath=' '.join('M '+' L '.join(f'{a:.4f},{b:.4f}' for a,b in ring.coords)+' Z' for ring in [q.exterior,*q.interiors])
        x,y,*_=q.bounds;svg.append(f'<path d="{unitpath}" fill-rule="evenodd" fill="{colors[name]}" fill-opacity=".18" stroke="{colors[name]}" stroke-width=".15"/>')
        svg.append(f'<text x="{x+4}" y="{y+8}" font-family="Arial" font-size="3" fill="white">{name}</text>')
    for t in tabs:
        for x,y in t['holes']:svg.append(f'<circle cx="{x}" cy="{y}" r=".3" fill="white"/>')
    svg.append('<text x="166" y="105" font-family="Arial" font-size="2.2" fill="white">238 x 114 mm / 2 layers</text></svg>')
    (OUT/'panel.svg').write_text('\n'.join(svg),encoding='utf-8')
    import resvg_py
    (OUT/'panel.png').write_bytes(resvg_py.svg_to_bytes(svg_string='\n'.join(svg)))
    for args in [('drc','--format','json','-o',OUT/'Panel-drc.json',dest),
                 ('export','gerbers','-l','F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts','--subtract-soldermask','-o',str(OUT/'gerbers')+'/',dest),
                 ('export','drill','--format','excellon','--excellon-units','mm','--excellon-separate-th','--excellon-oval-format','route','--generate-report','-o',str(OUT/'gerbers')+'/',dest)]:
        subprocess.run([str(CLI),'pcb',*map(str,args)],check=True)
    drc=json.loads((OUT/'Panel-drc.json').read_text());assert not drc['violations'] and not drc['unconnected_items'],'Panel native DRC'
    with zipfile.ZipFile(OUT/'MagMouse-panel-gerbers.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for f in sorted((OUT/'gerbers').iterdir()):archive.write(f,f.name)
    print('Panel complete',SIZE,sha(OUT/'MagMouse-panel-gerbers.zip'))

if __name__=='__main__':build()
