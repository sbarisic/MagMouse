"""Generate source-derived paste, harness and bench-access review evidence.

Run after export_bench.procurement. Polygon screening is not paste-transfer,
probe-fit, connector qualification or thermal acceptance.
"""
import csv
import html
import json
from collections import defaultdict
from pathlib import Path
import pcbnew as p
from build_panel import HERE, SOURCES, OFFSETS, sha, save_json,atomic_text
from wire_interfaces import INTERFACES
from stencil_policy import POLICY, exclude_non_reflow, verify_geometry, physical_openings
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely.affinity import scale

OUT=HERE/'package'

def write_rows(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def polyset(poly):
    def ring(c):return [(p.ToMM(c.CPoint(i).x),p.ToMM(c.CPoint(i).y)) for i in range(c.PointCount())]
    return unary_union([Polygon(ring(poly.Outline(i)),[ring(poly.Hole(i,j)) for j in range(poly.HoleCount(i))])
                       for i in range(poly.OutlineCount())])

def pad_polygon(pad,layer):
    poly=p.SHAPE_POLY_SET()
    pad.TransformShapeToPolygon(poly,layer,0,p.FromMM(POLICY.polygon_error_mm),p.ERROR_INSIDE)
    return polyset(poly)

def paste_measurements(board,selected,policy=POLICY):
    aperture_rows=[];coverage=[];packages=[]
    for f in board.GetFootprints():
        if f.GetReference() not in selected:continue
        paste=physical_openings(f,policy)
        copper=[(q,pad_polygon(q,p.F_Cu)) for q in f.Pads() if q.IsOnLayer(p.F_Cu)]
        paste_union=unary_union([g for _,g,_,_ in paste])
        ratios=[]
        for q,g,numbers,primitive_count in paste:
            assert g.is_valid and g.area>0 and g.length>0
            ratio=g.area/(g.length*policy.thickness_mm);ratios.append(ratio)
            aperture_rows.append(dict(Reference=f.GetReference(),Pad=numbers,Primitive_count=primitive_count,Area_mm2=round(g.area,6),
                Perimeter_mm=round(g.length,6),Thickness_mm=policy.thickness_mm,Polygon_wkt=g.wkt,Volume_mm3=round(g.area*policy.thickness_mm,6),Area_ratio=round(ratio,4),
                X_mm=g.centroid.x,Y_mm=g.centroid.y,
                Rotation_deg=q.GetOrientationDegrees(),
                Status='REVIEW RELEASE' if ratio<policy.minimum_area_ratio else 'Geometric release screen passes'))
        for q,g in copper:
            # Report all lands; central split paste maps by polygon intersection,
            # not by blank pad numbers or largest-pad assumptions.
            overlap=g.intersection(paste_union).area
            if not overlap:continue
            coverage.append(dict(Reference=f.GetReference(),Pad=q.GetNumber(),Net=q.GetNetname(),
                Copper_area_mm2=round(g.area,6),Paste_on_land_mm2=round(overlap,6),
                Coverage_percent=round(100*overlap/g.area,2),Volume_on_land_mm3=round(overlap*policy.thickness_mm,6)))
        field=f.GetField('Datasheet')
        packages.append(dict(Reference=f.GetReference(),MPN=selected[f.GetReference()]['purchase_mpn'],
            Footprint=f.GetFPID().GetLibItemName(),Apertures=len(paste),
            Minimum_area_ratio=round(min(ratios),4) if ratios else '',
            Datasheet=field.GetText() if field else '',
            Disposition='See STENCIL_REVIEW.md; package evidence and lot/reflow limits are separate from geometric pass'))
    assert set(selected)=={r['Reference'] for r in packages},'Missing populated package in review'
    return aperture_rows,coverage,packages

def harness_rows(boards):
    pads={name:{(f.GetReference(),q.GetNumber()):q for f in b.GetFootprints() for q in f.Pads() if q.GetNumber()}
          for name,b in boards.items()}
    rows=[]
    def add(label,ab,ar,ap,bb,br,bp,length,wire):
        a=pads[ab][ar,str(ap)];z=pads[bb][br,str(bp)] if bb else None
        if z:assert a.GetNetname()==z.GetNetname(),(label,ap,bp,a.GetNetname(),z.GetNetname())
        rows.append(dict(Harness=label,From=f'{ab}/{ar}.{ap}',To=f'{bb}/{br}.{bp}' if z else f'Coil {br} lead {bp}',
            Signal=a.GetNetname(),Length_mm=length,Wire=wire,
            From_pad_X_mm=p.ToMM(a.GetPosition().x),From_pad_Y_mm=p.ToMM(a.GetPosition().y),
            To_pad_X_mm=p.ToMM(z.GetPosition().x) if z else '',To_pad_Y_mm=p.ToMM(z.GetPosition().y) if z else '',
            Check='Unpowered continuity by pad number; no adjacent-contact shorts; view coordinates are component-side'))
    for n in range(1,31):add('Soldered ribbon','Main','J8',n,'Wheel','J9',31-n,150,'30-way AWG28 ribbon; retain all ground conductors')
    for n in range(1,3):add('Wheel power','Main','J10',n,'Wheel','J11',n,150,'AWG22; directly soldered pair')
    for n in range(1,9):add('Encoder','Main','J6',n,'Encoder','J7',n,150,'AWG28; soldered eight-conductor ribbon')
    for ref,side in [('J2','L'),('J3','M'),('J4','R')]:
        for n in range(1,3):add('Button '+side,'Main',ref,n,None,side,n,200,'AWG24; directly soldered paired conductors')
    return rows


def wiring_drawing(rows):
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">',
         '<rect width="297" height="210" fill="white"/><g font-family="sans-serif" font-size="2.6">',
         '<text x="10" y="12" font-size="5">Rev-A soldered-wire map / no connectors fitted</text>',
         '<text x="10" y="20">Read numbered pads from component-side or mirrored solder-side drawings. Never infer mapping from cable colour.</text>',
         '<text x="10" y="29">150 mm AWG28 ribbon: J8.N → J9.(31−N)</text>',
         '<text x="155" y="29">Encoder, power and coil wires</text>']
    for column,selection in enumerate([[r for r in rows if r['Harness']=='Soldered ribbon'],[r for r in rows if r['Harness']!='Soldered ribbon']]):
        x=10+145*column
        for i,row in enumerate(selection):
            y=36+i*4.4;colour='#153d7a' if row['Signal']=='GND' else '#222'
            svg.append(f'<text x="{x}" y="{y}" fill="{colour}">{html.escape(row["From"])} → {html.escape(row["To"])}</text>')
            svg.append(f'<text x="{x+80}" y="{y}" fill="{colour}">{html.escape(row["Signal"])}</text>')
    svg += ['<text x="10" y="176">All 15 ribbon and 3 encoder ground conductors are mandatory. A meter alone cannot prove each parallel ground wire is present.</text>',
            '<text x="10" y="184">Power: AWG22 / 150 mm. Encoder: AWG28 / 150 mm. Coils: AWG24 / 200 mm; both leads are switched bridge outputs.</text>',
            '<text x="10" y="192">Inspect individual wires, joints and adjacent-net isolation before power. Clamp insulation; solder protrusion below 1.5 mm.</text>',
            '<text x="10" y="201">Rev-A bench prototype — pending supplier/CAM approval. No electrical function is validated by this drawing alone.</text></g></svg>']
    atomic_text(OUT/'wire-map.svg','\n'.join(svg))

def access_rows(boards):
    rows=[];thermal=[]
    targets={'Main':['U2','U4','U5','U6','U12','U13'], 'Wheel':['U21','Q5','R121','R122','R123','R124'], 'Encoder':['U27']}
    for name,b in boards.items():
        fs=list(b.GetFootprints());ground=[q for f in fs for q in f.Pads() if q.GetNetname()=='GND' and f.GetReference().startswith('TP')]
        for f in fs:
            if not f.GetReference().startswith('TP'):continue
            q=next(iter(f.Pads()));point=Point(p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y))
            side=p.F_Cu if q.IsOnLayer(p.F_Cu) else p.B_Cu
            other=[]
            for c in fs:
                if c.GetReference().startswith('TP') or c.GetReference() in INTERFACES[name] or (side==p.F_Cu)==c.IsFlipped():continue
                bounds=c.GetBoundingBox(False,False)
                obstacle=box(p.ToMM(bounds.GetX()),p.ToMM(bounds.GetY()),p.ToMM(bounds.GetRight()),p.ToMM(bounds.GetBottom()))
                if point.buffer(.5).intersects(obstacle):other.append(c.GetReference())
            nearest=min(((p.ToMM((q.GetPosition()-g.GetPosition()).EuclideanNorm()),g.GetParentFootprint().GetReference()) for g in ground),default=(None,''))
            rows.append(dict(Board=name,Reference=f.GetReference(),Signal=q.GetNetname(),Side=b.GetLayerName(side),
                X_mm=point.x,Y_mm=point.y,Ground_testpoint=nearest[1],Ground_distance_mm=round(nearest[0],3) if nearest[0] is not None else '',
                Probe_envelope_obstacles=';'.join(other),
                Access='Tilt/remove carrier for underside probe' if side==p.B_Cu else 'Top access; verify probe barrel clearance',
                Scope='0.5 mm tip-radius component-bounds screening, not 3D collision certification'))
        for f in fs:
            if f.GetReference() not in INTERFACES[name]:continue
            nearby=[q for q in f.Pads() if q.GetNetname()=='GND']+ground
            for q in f.Pads():
                distance,g=min(((p.ToMM((q.GetPosition()-g.GetPosition()).EuclideanNorm()),g) for g in nearby),key=lambda v:v[0],default=(None,None))
                rows.append(dict(Board=name,Reference=f.GetReference()+'.'+q.GetNumber(),Signal=q.GetNetname(),Side='F.Cu / B.Cu',
                    X_mm=p.ToMM(q.GetPosition().x),Y_mm=p.ToMM(q.GetPosition().y),
                    Ground_testpoint=g.GetParentFootprint().GetReference()+'.'+g.GetNumber() if g else '',
                    Ground_distance_mm=round(distance,3) if distance is not None else '',
                    Probe_envelope_obstacles='Soldered wire may occupy land; approach from underside',
                    Access='Existing plated land; no added stub or wire loop',
                    Scope='Use nearby ground spring for digital measurements; verify actual probe and wire clearance'))
        conn=b.GetConnectivity();b.BuildConnectivity()
        for f in fs:
            if f.GetReference() not in targets[name]:continue
            vias=[v for v in b.GetTracks() if isinstance(v,p.PCB_VIA) and v.GetNetname()=='GND' and
                  p.ToMM((v.GetPosition()-f.GetPosition()).EuclideanNorm())<=3]
            gp=[q for q in f.Pads() if q.GetNetname()=='GND']
            attached=all(any(i.GetClass()=='ZONE' and i.IsOnLayer(p.In1_Cu) for i in conn.GetConnectedItems(q)) for q in gp)
            thermal.append(dict(Board=name,Reference=f.GetReference(),Ground_vias_within_3mm=len(vias),
                Ground_pads=len(gp),All_ground_pads_reach_In1=attached if gp else 'N/A',
                Acceptance='Geometry inventory only; no junction temperature or current rating inferred'))
    return rows,thermal

def supports(boards):
    rows=[]
    for t in json.loads((HERE/'panel-manifest.json').read_text())['tabs']:
        name=t['board'];dx,dy=OFFSETS[name];x,y=t['center'];x-=dx;y-=dy
        # Upright fixture clips span unit Y=58..64; panel breakaway tabs are
        # separate mechanical features and need not be the carrier contact.
        if name=='Encoder':y=61
        half_width=3 if name=='Encoder' else 2.5
        nx,ny=t['normal'];tx,ty=-ny,nx
        contact=Polygon([(x+tx*a-nx*b,y+ty*a-ny*b) for a,b in [(-half_width,0),(half_width,0),(half_width,.3),(-half_width,.3)]])
        obstruct=[]
        for f in boards[name].GetFootprints():
            for q in f.Pads():
                if q.IsOnLayer(p.B_Mask) and pad_polygon(q,p.B_Cu).intersects(contact):
                    obstruct.append(f.GetReference()+'.'+q.GetNumber())
        rows.append(dict(Board=name,Support=t['index'],Unit_X_mm=x,Unit_Y_mm=y,
            Lip_depth_mm=.3,Contact_width_mm=2*half_width,Underside_exposed_pad_conflicts=';'.join(obstruct),
            Status='Clear in pad geometry; verify actual clip and both faces' if not obstruct else 'MOVE SUPPORT BEFORE CLAMPING'))
    write_rows(OUT/'support-clearances.csv',rows)
    assert all(not r['Underside_exposed_pad_conflicts'] for r in rows),'Fixture support touches an exposed pad'

def connector_views(boards):
    selected={'Main':['J1','J2','J3','J4','J6','J8','J10'],'Wheel':['J9','J11'],'Encoder':['J7']}
    for name,refs in selected.items():
        for f in boards[name].GetFootprints():
            if f.GetReference() not in refs:continue
            pads=[q for q in f.Pads() if q.GetNumber()];geoms=[pad_polygon(q,p.F_Cu) for q in pads]
            x0,y0,x1,y1=unary_union(geoms).bounds;w=x1-x0+3;h=y1-y0+4
            for bottom in [False,True]:
                side='solder-side (flipped left/right)' if bottom else 'component-side'
                svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="600" viewBox="{x0-1.5} {y0-2} {w} {h}">',
                     f'<rect x="{x0-1.5}" y="{y0-2}" width="{w}" height="{h}" fill="white"/>',
                     f'<text x="{x0}" y="{y0-1}" font-size=".35">{name}/{f.GetReference()}: {side}</text>']
                for q,g in zip(pads,geoms):
                    if bottom:g=scale(g,xfact=-1,yfact=1,origin=((x0+x1)/2,0))
                    svg.append(g.svg(scale_factor=.01,fill_color='#e66' if q.GetNumber()=='1' else '#ecd78a'))
                    x,y=tuple(p.ToMM(q.GetPosition()));x=x0+x1-x if bottom else x
                    if q.GetDrillSize().x:
                        svg.append(f'<circle cx="{x}" cy="{y}" r="{p.ToMM(q.GetDrillSize().x)/2}" fill="white" stroke="#333" stroke-width=".015"/>')
                    font='.55' if f.GetReference() in INTERFACES[name] else '.23'
                    svg.append(f'<text x="{x}" y="{y+.15}" text-anchor="middle" font-size="{font}">{html.escape(q.GetNumber())}</text>')
                svg.append('</svg>');suffix='solder-pins' if bottom else 'pins'
                atomic_text(OUT/'local-review'/f'{name}-{f.GetReference()}-{suffix}.svg','\n'.join(svg))

def closeup(board,bounds,title,path):
    x,y,w,h=bounds;clip=box(x,y,x+w,y+h)
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{round(1200*(h+3)/w)}" viewBox="{x} {y-3} {w} {h+3}">',
         f'<rect x="{x}" y="{y-3}" width="{w}" height="{h+3}" fill="white"/>']
    def shape(g,color,opacity=1):
        g=g.intersection(clip)
        if hasattr(g,'geoms'):
            for part in g.geoms:shape(part,color,opacity)
        elif g.geom_type=='Polygon' and not g.is_empty:
            svg.append(f'<g opacity="{opacity}">'+g.svg(scale_factor=.015,fill_color=color).replace('opacity="0.6"','opacity="1"')+'</g>')
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.IsOnLayer(p.In1_Cu):shape(polyset(z.GetFilledPolysList(p.In1_Cu)),'#bce3c5')
    for t in board.GetTracks():
        a=tuple(p.ToMM(t.GetStart()));c=tuple(p.ToMM(t.GetEnd()))
        if isinstance(t,p.PCB_VIA):shape(Point(a).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2),'#555');continue
        if t.GetLayer()!=p.F_Cu:continue
        color='#d62828' if t.GetNetname() in ('BUCK_SW','BRAKE_DRAIN','PHASE_A','PHASE_B','PHASE_C') else '#b77830' if t.GetNetname()=='GND' else '#2368a2'
        shape(LineString([a,c]).buffer(p.ToMM(t.GetWidth())/2),color)
    for f in board.GetFootprints():
        for q in f.Pads():
            if q.IsOnLayer(p.F_Cu):shape(pad_polygon(q,p.F_Cu),'#d8b438')
            if q.GetDrillSize().x:shape(Point(tuple(p.ToMM(q.GetPosition()))).buffer(p.ToMM(q.GetDrillSize().x)/2),'white')
        a=tuple(p.ToMM(f.GetPosition()))
        if clip.contains(Point(a)):
            svg.append(f'<text x="{a[0]}" y="{a[1]}" font-family="sans-serif" font-size=".55" fill="black">{html.escape(f.GetReference())}</text>')
    import textwrap
    lines=textwrap.wrap(title,max(20,int(w/.24)))+['Green: In1; blue: F.Cu; brown: GND']
    for i,line in enumerate(lines):svg.append(f'<text x="{x+.2}" y="{y-2.4+i*.7}" font-size=".4">{html.escape(line)}</text>')
    svg.append('</svg>')
    atomic_text(path,'\n'.join(svg))

def paste_view(board,refs,path):
    """Local stencil overlay: grey copper, red deposits, source pad coordinates."""
    footprints=[f for f in board.GetFootprints() if f.GetReference() in refs]
    all_pads=[pad_polygon(q,p.F_Cu) for f in footprints for q in f.Pads() if q.IsOnLayer(p.F_Cu)]
    x,y,x1,y1=unary_union(all_pads).bounds;x-=.4;y-=.4;x1+=.4;y1+=.4
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {x1-x} {y1-y}">',
         f'<rect x="{x}" y="{y}" width="{x1-x}" height="{y1-y}" fill="white"/>']
    for layer,color in [(p.F_Cu,'#999999'),(p.F_Paste,'#dd3333')]:
        for f in footprints:
            for q in f.Pads():
                if q.IsOnLayer(layer):svg.append(pad_polygon(q,layer).svg(scale_factor=.005,fill_color=color))
    svg.append('</svg>');atomic_text(path,'\n'.join(svg))


def generate(population):
    boards={name:p.LoadBoard(str(path)) for name,path in SOURCES.items()}
    from paste_variant import apply
    retained=[apply(b,name) for name,b in boards.items()]
    apertures=[];coverage=[];packages=[]
    for name,b in boards.items():
        selected={r['reference']:r for r in population if r['board']==name and r['method']=='TOP SMT REFLOW'}
        exclude_non_reflow(b,selected)
        verify_geometry(b,selected)
        aa,cc,pp=paste_measurements(b,selected)
        for output,items in [(apertures,aa),(coverage,cc),(packages,pp)]:output.extend(dict(Board=name,**r) for r in items)
    write_rows(OUT/'paste-shape-measurements.csv',apertures)
    write_rows(OUT/'paste-land-coverage.csv',coverage)
    write_rows(OUT/'package-review-register.csv',packages)
    mapping=harness_rows(boards);write_rows(OUT/'harness-pin-map.csv',mapping);wiring_drawing(mapping)
    harness_bom=[]
    for description,required,purchase,mapping in [
        ('30-way stranded AWG28 ribbon, 1.27 mm conductor pitch',.30,.50,'Main/J8-Wheel/J9 0.15 m; trim 8 conductors for Main/J6-Encoder/J7 0.15 m'),
        ('Stranded AWG22 insulated wire, two identifiable colours',.30,1.0,'Main/J10-Wheel/J11; two 0.15 m leads'),
        ('Stranded AWG24 insulated wire, marked paired leads',1.20,2.0,'Main/J2/J3/J4; six 0.20 m leads')]:
        harness_bom.append(dict(Description=description,Required_m=required,Suggested_purchase_m=purchase,
            Spare_m=round(purchase-required,2),Mapping=mapping,Supplier='Private-consumer source; exact wire product and price pending',
            Price_EUR='',Shipping_EUR='',Status='No crimp housings or contacts; inspect strand fit/insulation and verify continuity'))
    write_rows(OUT/'harness-purchasing.csv',harness_bom)
    access,thermal=access_rows(boards);write_rows(OUT/'probe-access.csv',access);write_rows(OUT/'thermal-return-inventory.csv',thermal)
    (OUT/'local-review').mkdir(exist_ok=True)
    supports(boards);connector_views(boards)
    views=[('Main',(57,16,15,16),'Buck and L1','buck'),('Main',(0,10,35,30),'Left and middle drivers','buttons-left'),
           ('Main',(45,28,33,35),'ADC1 and right driver','buttons-adc'),('Wheel',(16,15,33,30),'Wheel driver and brake','wheel'),
           ('Main',(28,60,26,26),'Optical footprint and ground exclusion','optical')]
    views += [('Main',(69,43,9,42),'J8 wire lands and local routing','main-wire-array'),
              ('Main',(63,38,12,10),'J10 actuator supply wire termination','main-power-wire'),
              ('Wheel',(14,0,41,13),'J9 ribbon and J11 power terminations','wheel-wire-array'),
              ('Encoder',(49,49,16,20),'Encoder wire terminations','encoder-wires')]
    for name,bounds,title,filename in views:closeup(boards[name],bounds,title,OUT/'local-review'/(filename+'.svg'))
    for name,ref in [(name,f.GetReference()) for name,b in boards.items() for f in b.GetFootprints()
                     if f.GetReference().startswith('U') and any(q.IsOnLayer(p.F_Paste) for q in f.Pads())] + [('Main','J8'),('Main','D5'),('Wheel','C90')]:
        paste_view(boards[name],{ref},OUT/'local-review'/('paste-'+name+'-'+ref+'.svg'))
    save_json(OUT/'detail-review.json',dict(source_sha256={n:sha(path) for n,path in SOURCES.items()},
        paste_polygon_error_mm=POLICY.polygon_error_mm,stencil_thickness_mm=POLICY.thickness_mm,paste_apertures=len(apertures),
        release_screen_findings=[r for r in apertures if r['Area_ratio']<POLICY.minimum_area_ratio],
        population_coverage='PASS',harness_mapping='PASS',manufacturing_ready=False,
        limits='Manufacturer examples, 3D bench fit, measured print transfer and CAM acceptance remain separate.'))

if __name__=='__main__':
    with (OUT/'population.csv').open(newline='',encoding='utf-8-sig') as f:generate(list(csv.DictReader(f)))
