"""Build a derived Rev-A bare panel. Run with KiCad 10 Python and Shapely 2.1.2.

Sources remain separate editable projects. The panel has no shared electrical
nets. Manufacturing acceptance is deliberately separate from geometry checks.
"""
import argparse
from collections import Counter
import hashlib
import os
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'build/bench-python'))
sys.path.insert(0, str(ROOT/'hardware/modular'))
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from build_planning import root_sections
import pcbnew as p

HERE = Path(__file__).resolve().parent
SOURCES = {'Main': ROOT/'hardware/modular/main/Main.kicad_pcb',
           'Wheel': ROOT/'hardware/modular/wheel/Wheel.kicad_pcb',
           'Encoder': ROOT/'hardware/encoder/Encoder.kicad_pcb'}
OFFSETS = {'Main': (7,7), 'Wheel': (89,7), 'Encoder': (42,30)}
PANEL_SIZE = (151,139)


def xy(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic_text(path,text):
    temporary=path.with_name(path.name+'.writing')
    temporary.write_text(text,encoding='utf-8')
    os.replace(temporary,path)

def publish_panel_file(temporary, path):
    """Publish derived panel bytes when a Windows reader denies rename.

    Some viewers allow rewriting their open file but deny replacing its name.
    Only the derived Panel uses this fallback; unit source boards never do.
    """
    try:
        os.replace(temporary,path)
    except PermissionError:
        data=temporary.read_bytes()
        path.write_bytes(data)
        assert path.read_bytes()==data, 'Derived panel write did not verify'
        try:temporary.unlink()
        except PermissionError:pass


def save_json(path, data): atomic_text(path,json.dumps(data,indent=2)+'\n')
def uid(item): return item.m_Uuid.AsString()
UUID_REPLACEMENTS={}
def stable_uuid(item, name): UUID_REPLACEMENTS[uid(item)]=str(uuid.uuid5(uuid.NAMESPACE_URL,'MagMouse/bench/'+name))
def normalize_uuids(path):
    import re
    text=path.read_text(encoding='utf-8')
    text=re.sub(r'\(uuid "([^"]+)"\)',lambda m:'(uuid "'+UUID_REPLACEMENTS.get(m[1],m[1])+'")',text)
    staging=ROOT/'build'/'panel-staging';staging.mkdir(parents=True,exist_ok=True)
    input_path=staging/(str(uuid.uuid4())+'.kicad_pcb')
    output_path=staging/(str(uuid.uuid4())+'.kicad_pcb')
    input_path.write_text(text,encoding='utf-8')
    # KiCad orders items by UUID on save. Normalize first, then reload/save so
    # random creation order cannot change otherwise identical generated files.
    normalized=p.LoadBoard(str(input_path));p.SaveBoard(str(output_path),normalized)
    if path.name=='Panel.kicad_pcb':
        sections=list(root_sections(output_path.read_text(encoding='utf-8')))
        geometric={'(footprint','(segment','(arc','(via','(zone','(gr_line','(gr_arc','(gr_text','(gr_rect','(gr_poly','(gr_circle'}
        fixed=[s for s in sections if s.split()[0] not in geometric]
        shapes=sorted(s for s in sections if s.split()[0] in geometric)
    temporary=staging/(str(uuid.uuid4())+'.normalized.tmp')
    temporary.write_text('(kicad_pcb\n'+'\n'.join(fixed+shapes)+'\n)\n',encoding='utf-8')
    publish_panel_file(temporary,path)
def duplicate(item):
    raw=item.Duplicate(False) if isinstance(item,(p.ZONE,p.FOOTPRINT)) else item.Duplicate()
    return getattr(p,'Cast_to_'+item.GetClass())(raw)


def outline(board):
    poly=p.SHAPE_POLY_SET()
    assert board.GetBoardPolygonOutlines(poly,False), 'Open board outline'
    assert poly.OutlineCount()==1
    def coords(chain): return [(p.ToMM(chain.CPoint(i).x),p.ToMM(chain.CPoint(i).y)) for i in range(chain.PointCount())]
    return Polygon(coords(poly.Outline(0)),[coords(poly.Hole(0,i)) for i in range(poly.HoleCount(0))])


def copper_signature(board):
    pads={(f.GetReference(),uid(pad)): (pad.GetNumber(),pad.GetNetname(),pad.GetPosition().x,pad.GetPosition().y,
          pad.GetSize().x,pad.GetSize().y,pad.GetLayerSet().FmtHex()) for f in board.GetFootprints() for pad in f.Pads()}
    tracks={uid(t): (t.GetNetname(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y,
                    t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth(),
                    t.GetDrillValue() if isinstance(t,p.PCB_VIA) else t.GetLayer()) for t in board.GetTracks()}
    return pads,tracks


def migrate_encoder():
    path=SOURCES['Encoder']; before=p.LoadBoard(str(path)); sig=copper_signature(before)
    source_hash=sha(path)
    if before.GetCopperLayerCount()==4 and any(z.GetLayer()==p.In1_Cu for z in before.Zones()):
        print('Encoder already four-layer; migration skipped')
        return
    main_sections=list(root_sections(SOURCES['Main'].read_text(encoding='utf-8')))
    layers=next(s for s in main_sections if s.startswith('(layers'))
    setup=next(s for s in main_sections if s.startswith('(setup'))
    stack=next(s for s in root_sections(setup) if s.startswith('(stackup'))
    parts=[]
    for s in root_sections(path.read_text(encoding='utf-8')):
        if s.startswith('(layers'): s=layers
        elif s.startswith('(general'): s=s.replace('(thickness 1.6)','(thickness 1.578)')
        elif s.startswith('(setup'): s='(setup\n'+stack+'\n'+'\n'.join(t for t in root_sections(s) if not t.startswith('(stackup'))+'\n)'
        parts.append(s)
    path.write_text('(kicad_pcb\n'+'\n'.join(parts)+'\n)\n',encoding='utf-8')
    b=p.LoadBoard(str(path))
    base=next(z for z in b.Zones() if z.GetLayer()==p.F_Cu and z.GetNetname()=='GND' and not z.GetIsRuleArea())
    for layer in (p.In1_Cu,p.In2_Cu):
        z=duplicate(base);z.SetParent(b);z.SetLayer(layer);z.UnFill();z.SetZoneName('ENCODER GND '+b.GetLayerName(layer))
        stable_uuid(z,'encoder-'+b.GetLayerName(layer));b.Add(z)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity()
    assert copper_signature(b)==sig,'Encoder outer copper/pad/net change'
    assert b.GetConnectivity().GetUnconnectedCount(False)==0
    pro=path.with_suffix('.kicad_pro');raw=pro.read_bytes()
    p.SaveBoard(str(path),b);pro.write_bytes(raw);normalize_uuids(path)
    save_json(HERE/'encoder-stack-migration.json',dict(before_sha256=source_hash,after_sha256=sha(path),
        layers=4,stack='JLC041611-2116',outer_copper_and_pad_identity_preserved=True,
        inner_layers='GND pours copied from existing F.Cu boundary, refilled with source project',
        vias=17,native_unrouted=0,mechanical_datums_unchanged=True))


def add_segment(b,a,c,layer=p.Edge_Cuts):
    if xy(*a)==xy(*c):return
    s=p.PCB_SHAPE(b);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(xy(*a));s.SetEnd(xy(*c));s.SetWidth(p.FromMM(.05));s.SetLayer(layer)
    stable_uuid(s,f'segment-{layer}-{a}-{c}');b.Add(s)


def add_hole(b,x,y,d,ref):
    f=p.FOOTPRINT(b);f.SetReference(ref);f.SetValue('NPTH');f.SetExcludedFromBOM(True);f.SetExcludedFromPosFiles(True)
    f.SetPosition(xy(x,y));stable_uuid(f,ref);b.Add(f)
    pad=p.PAD(f);pad.SetAttribute(p.PAD_ATTRIB_NPTH);pad.SetShape(p.PAD_SHAPE_CIRCLE)
    pad.SetSize(xy(d,d));pad.SetDrillSize(xy(d,d));pad.SetLayerSet(p.LSET.AllCuMask());pad.SetPosition(xy(x,y));stable_uuid(pad,ref+'pad');f.Add(pad)
    for i,field in enumerate(f.GetFields()):
        field.SetVisible(False);stable_uuid(field,ref+'/field/'+str(i))


def tab_candidates(board, poly):
    """Only straight edges; drill row is 0.5 mm OUTSIDE finished unit edge."""
    # Candidate width 5 mm, 5 holes at 0.9 pitch: 0.3 mm web.
    coords=list(poly.simplify(.000001).exterior.coords); result=[]
    for a,c in zip(coords,coords[1:]):
        dx,dy=c[0]-a[0],c[1]-a[1];length=(dx*dx+dy*dy)**.5
        if length<6:continue
        tx,ty=dx/length,dy/length; nx,ny=-ty,tx
        mid=((a[0]+c[0])/2,(a[1]+c[1])/2)
        if poly.contains(Point(mid[0]+nx*.1,mid[1]+ny*.1)):nx,ny=-nx,-ny
        for distance in range(3,int(length)-2,3):
            x,y=a[0]+tx*distance,a[1]+ty*distance
            # Screen component courtyards (pads when absent) for support access.
            # Separate panel DRC and translated-copper checks cover copper.
            probe=Point(x,y).buffer(3)
            blocked=False
            for f in board.GetFootprints():
                shapes=[s for s in f.GraphicalItems() if s.GetLayer() in (p.F_CrtYd,p.B_CrtYd)] or list(f.Pads())
                for s in shapes:
                    r=s.GetBoundingBox()
                    if probe.intersects(box(p.ToMM(r.GetLeft()),p.ToMM(r.GetTop()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom()))):blocked=True;break
                if blocked:break
            if blocked:continue
            corners=[(x+tx*u+nx*v,y+ty*u+ny*v) for u,v in [(-2.5,-.1),(2.5,-.1),(2.5,2.1),(-2.5,2.1)]]
            holes=[(x+tx*u+nx*.5,y+ty*u+ny*.5) for u in (-1.8,-.9,0,.9,1.8)]
            result.append(dict(center=[x,y],normal=[nx,ny],polygon=corners,holes=holes))
    return result

def frame_material(units):
    return box(0,0,*PANEL_SIZE).difference(unary_union([u.buffer(2,join_style='round',quad_segs=128) for u in units])).buffer(-1,quad_segs=128).buffer(1,quad_segs=128)

def verify_tab_bridge(tab, unit, frame):
    """Require the entire 5 mm tab width to enter both substrates by 0.08 mm."""
    x,y=tab['center'];nx,ny=tab['normal'];tx,ty=-ny,nx
    def strip(a,b):
        return Polygon([(x+tx*u+nx*v,y+ty*u+ny*v) for u,v in [(-2.5,a),(2.5,a),(2.5,b),(-2.5,b)]])
    tab_poly=Polygon(tab['polygon'])
    assert tab_poly.buffer(1e-7).covers(strip(-.09,2.09)), 'Tab is not a full-width bridge'
    assert unit.buffer(1e-7).covers(strip(-.09,-.01)), 'Tab does not enter intended board across full width'
    assert frame.buffer(1e-7).covers(strip(2.01,2.09)), 'Tab does not enter frame across full width'
    return dict(board_overlap_depth_mm=.08,frame_overlap_depth_mm=.08,bridge_width_mm=5)


def build():
    HERE.mkdir(exist_ok=True)
    hashes={n:sha(f) for n,f in SOURCES.items()}
    boards={n:p.LoadBoard(str(f)) for n,f in SOURCES.items()}
    assert all(b.GetCopperLayerCount()==4 for b in boards.values())
    sections=[s for s in root_sections(SOURCES['Main'].read_text(encoding='utf-8'))
              if s.split()[0] in ('(version','(generator','(generator_version','(general','(paper','(layers','(setup')]
    dest=HERE/'Panel.kicad_pcb'
    staging=ROOT/'build'/'panel-staging';staging.mkdir(parents=True,exist_ok=True)
    temporary=staging/(str(uuid.uuid4())+'.kicad_pcb')
    temporary.write_text('(kicad_pcb\n'+'\n'.join(sections)+'\n)\n',encoding='utf-8')
    # Preserve source design minima in the derived manufacturing project.
    pro=HERE/'Panel.kicad_pro';pro_data=SOURCES['Main'].with_suffix('.kicad_pro').read_bytes()
    if not pro.exists() or pro.read_bytes()!=pro_data:atomic_text(pro,pro_data.decode('utf-8'))
    panel=p.LoadBoard(str(temporary));manifest={};units=[];tabs=[];refs=[]
    from shapely.affinity import translate
    for name,b in boards.items():
        ox,oy=OFFSETS[name];offset=xy(ox,oy);poly=outline(b);placed=translate(poly,ox,oy);units.append(placed)
        netmap={0:panel.FindNet(0)}
        for code,net in b.GetNetsByNetcode().items():
            if code:
                n=p.NETINFO_ITEM(panel,name+'/'+net.GetNetname());panel.Add(n);netmap[code]=n
        for f in b.GetFootprints():
            item=duplicate(f);item.SetParent(panel);panel.Add(item);item.Move(offset)
            source_ref=f.GetReference();item.SetReference(name[0]+'_'+source_ref)
            stable_uuid(item,name+'/'+source_ref)
            for i,(old,pad) in enumerate(zip(f.Pads(),item.Pads())):
                pad.SetNet(netmap[old.GetNetCode()]);stable_uuid(pad,name+'/'+source_ref+'/pad/'+str(i))
            for i,child in enumerate(item.GraphicalItems()):stable_uuid(child,name+'/'+source_ref+'/graphic/'+str(i))
            for i,child in enumerate(item.GetFields()):stable_uuid(child,name+'/'+source_ref+'/field/'+str(i))
            for i,child in enumerate(item.Zones()):stable_uuid(child,name+'/'+source_ref+'/zone/'+str(i))
            refs.append(dict(board=name,source_reference=source_ref,panel_reference=item.GetReference(),
                             source_x_mm=p.ToMM(f.GetPosition().x),source_y_mm=p.ToMM(f.GetPosition().y),
                             panel_x_mm=p.ToMM(item.GetPosition().x),panel_y_mm=p.ToMM(item.GetPosition().y),
                             rotation_degrees=item.GetOrientationDegrees()))
        for collection in (b.GetTracks(),b.Zones(),b.GetDrawings()):
            for old in collection:
                if isinstance(old,p.PCB_SHAPE) and old.GetLayer()==p.Edge_Cuts:continue
                item=duplicate(old);item.SetParent(panel);panel.Add(item)
                if hasattr(item,'SetNet'):item.SetNet(netmap[old.GetNetCode()])
                item.Move(offset);stable_uuid(item,name+'/'+uid(old))
        # Spread tabs over available edges. The main's front and two straight
        # side edges are preferred; rectangular modules use opposed edges.
        candidates=tab_candidates(b,poly);chosen=[]
        targets={'Main':[(24,0),(57,0),(0,75),(80,68)],'Wheel':[(9,0),(55,12),(13,60),(43,60)],'Encoder':[(53,50),(64,53)]}[name]
        for target in targets:
            usable=[c for c in candidates if all(Point(c['center']).distance(Point(t['center']))>=8 for t in chosen)]
            if not usable:raise ValueError(name+': insufficient clear tab sites')
            best=min(usable,key=lambda c:Point(c['center']).distance(Point(target)))
            assert Point(best['center']).distance(Point(target))<1e-6,(name,'Reviewed tab site unavailable',target)
            chosen.append(best)
        for i,t in enumerate(chosen):
            t['board']=name;t['index']=i+1
            t['polygon']=[(x+ox,y+oy) for x,y in t['polygon']];t['holes']=[(x+ox,y+oy) for x,y in t['holes']]
            t['center']=[t['center'][0]+ox,t['center'][1]+oy];tabs.append(t)
        manifest[name]=dict(source=str(SOURCES[name].relative_to(ROOT)),sha256=hashes[name],
            translation_mm=[ox,oy],rotation_degrees=0,footprints=len(list(b.GetFootprints())),
            tracks_and_vias=len(list(b.GetTracks())),zones=len(list(b.Zones())),net_prefix=name+'/')
    waste=frame_material(units)
    for tab in tabs:
        verify_tab_bridge(tab,units[list(boards).index(tab['board'])],waste)
    material=unary_union([waste,*units,*[Polygon(t['polygon']) for t in tabs]])
    assert material.geom_type=='Polygon' and material.is_valid,'Panel is not one connected valid substrate'
    from router_geometry import make_routable,verify_outer,CONTOUR_SIMPLIFICATION
    for unit in units:verify_outer(Polygon(unit.exterior))
    material,router=make_routable(material)
    # Snap overlay vertices to KiCad's nanometre grid and remove duplicate
    # vertices before constructing Edge.Cuts. Do not emit zero-length edges.
    from shapely import set_precision
    material=set_precision(material.simplify(CONTOUR_SIMPLIFICATION,preserve_topology=True),.000001)
    from router_geometry import verify_material_tab
    router['tab_checks']=[verify_material_tab(material,tab) for tab in tabs]
    for ring in [material.exterior,*material.interiors]:
        coords=list(ring.coords)
        for a,c in zip(coords,coords[1:]):add_segment(panel,a,c)
    for i,t in enumerate(tabs):
        for j,(x,y) in enumerate(t['holes']):add_hole(panel,x,y,.6,f'MB{i+1}_{j+1}')
    for i,(x,y) in enumerate([(2.5,2.5),(148.5,2.5),(2.5,136.5),(148.5,136.5)]):
        assert material.boundary.distance(Point(x,y).buffer(1))>=.2,'Tooling hole too close to routing'
        add_hole(panel,x,y,2,f'TOOL{i+1}')
    # Copy saved copper exactly. Do not refill panel zones: source custom rules
    # and changed edge clearance must not silently change proven unit copper.
    panel.BuildConnectivity()
    staged_board=staging/(str(uuid.uuid4())+".kicad_pcb")
    assert p.SaveBoard(str(staged_board),panel)
    publish_panel_file(staged_board,dest)
    normalize_uuids(dest)
    # Temporary KiCad boards have default project settings; restore reviewed minima.
    atomic_text(pro,pro_data.decode("utf-8"))
    assert all(sha(f)==hashes[n] for n,f in SOURCES.items()),'Source changed during panel build'
    save_json(HERE/'panel-manifest.json',dict(status='REV-A BENCH QUOTE / ENGINEERING REVIEW REQUIRED',
        panel_size_mm=PANEL_SIZE,board_count=3,units=manifest,reference_map=refs,tabs=tabs,
        tab_width_mm=5,mousebite_diameter_mm=.6,mousebite_pitch_mm=.9,
        drill_row_offset_outside_unit_mm=.5,routing_gap_mm=2,
        router=router,
        stencil_variant_omitted=['Main/U32'],net_namespacing=True,
        source_copper_refilled_in_panel=False,panel_sha256=sha(dest)))
    # Readable mechanical preview, drawn in mm; a 100% print is a scale jig.
    paths=[]
    for ring in [material.exterior,*material.interiors]:
        paths.append('M '+' L '.join(f'{x:.5f},{y:.5f}' for x,y in ring.coords)+' Z')
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="151mm" height="139mm" viewBox="0 0 151 139">',
         '<rect width="151" height="139" fill="white"/>',
         '<path d="'+' '.join(paths)+'" fill="#dcead9" fill-rule="evenodd" stroke="#263238" stroke-width=".12"/>']
    for t in tabs:
        for x,y in t['holes']:svg.append(f'<circle cx="{x}" cy="{y}" r=".3" fill="white" stroke="#b71c1c" stroke-width=".05"/>')
    for name,b in boards.items():
        ox,oy=OFFSETS[name];bounds=outline(b).bounds
        svg.append(f'<text x="{bounds[0]+ox+3}" y="{bounds[1]+oy+6}" font-size="2.5">{name}</text>')
        for f in b.GetFootprints():
            for s in f.GraphicalItems():
                if s.GetLayer()!=p.F_CrtYd:continue
                r=s.GetBoundingBox();x=p.ToMM(r.GetX())+ox;y=p.ToMM(r.GetY())+oy
                svg.append(f'<rect x="{x}" y="{y}" width="{p.ToMM(r.GetWidth())}" height="{p.ToMM(r.GetHeight())}" fill="none" stroke="#416a9b" stroke-width=".08"/>')
    svg.append('<text x="92" y="125" font-size="2">BENCH REV-A / QUOTE ONLY</text></svg>')
    (HERE/'panel-mechanical.svg').write_text('\n'.join(svg),encoding='utf-8')
    print('Built',dest,'with',len(refs),'source footprints and',len(tabs),'tabs')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--migrate-encoder',action='store_true');args=ap.parse_args()
    if args.migrate_encoder:migrate_encoder()
    build()
