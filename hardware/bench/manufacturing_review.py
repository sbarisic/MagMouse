"""Prepare the bare-board CAM handoff without submitting an order."""
from collections import Counter
import csv
import json
import math
import re
import zipfile
from pathlib import Path
import pcbnew as p
from build_panel import HERE, SOURCES, outline, sha, save_json, atomic_text

ORDER = dict(panel_quantity=5,designs_per_panel=3,panel_size_mm=[151,139],
    panelization='Panel by customer; routed tabs and mouse bites; no V-score',
    pcb_assembly=False,allow_x_outs=False,confirm_production_files=True,
    layers=4,nominal_thickness_mm=1.6,stack='JLC041611-2116',
    material='FR4 TG155',outer_copper_oz=1,inner_copper_oz=1,
    finish='ENIG 1 microinch',solder_mask='Green',silkscreen='White',
    paid_impedance_control=False,stack_substitution_allowed=False,
    via_treatment='All actual vias epoxy filled and copper capped; all component/NPTH holes open',
    stencil_quantity=1,stencil_sheet_mm=[220,200],stencil_thickness_mm=.10,
    stencil='Unframed stainless, top only, supplied three groups; no automatic aperture resizing',
    destination='Croatia 43000',status='DRAFT - not submitted; no purchase authorized')
COPPER_FILES={'Panel-F_Cu.gtl':'Copper,L1,Top','Panel-In1_Cu.g1':'Copper,L2,Inr',
              'Panel-In2_Cu.g2':'Copper,L3,Inr','Panel-B_Cu.gbl':'Copper,L4,Bot'}


def normalize_job(path):
    """Correct order metadata only; never alter Gerber artwork or CAD sources."""
    data=json.loads(path.read_text())
    data['GeneralSpecs']['Size']={'X':151,'Y':139}
    data['GeneralSpecs']['ImpedanceControlled']=False
    # Retain the source model's 1.578 mm and all material-stack fields.
    # Nominal 1.6 mm is the order selection; see the exact stack drawing.
    # Inferred zero same-net clearances are not fabrication permissions.
    data.pop('DesignRules',None)
    save_json(path,data)


def validate_job(data):
    assert data['GeneralSpecs']['Size']=={'X':151,'Y':139},'Incorrect panel envelope'
    assert data['GeneralSpecs']['ImpedanceControlled'] is False,'Paid impedance metadata contradicts economy order'
    assert data['GeneralSpecs']['LayerNumber']==4,'Layer count changed'
    assert data['GeneralSpecs']['Finish']=='ENIG','Finish changed'
    stack=[(r['Name'],r['Thickness']) for r in data['MaterialStackup'] if r['Type'] in ('Copper','Dielectric')]
    assert stack==[('F.Cu',.035),('F.Cu/In1.Cu',.109),('In1.Cu',.03),('In1.Cu/In2.Cu',1.23),
                   ('In2.Cu',.03),('In2.Cu/B.Cu',.109),('B.Cu',.035)],'Unreviewed stack substitution'
    copper={r['Path']:r['FileFunction'] for r in data['FilesAttributes'] if r['FileFunction'].startswith('Copper')}
    if copper:assert copper==COPPER_FILES,'Incorrect copper file-layer mapping'


def inspect(board,manifest,vias):
    from verify_wire_interfaces import verify_fill
    verify_fill(board,vias)
    poly=outline(board)
    assert tuple(round(v,4) for v in poly.bounds)==(0,0,151,139)
    assert manifest['board_count']==3 and len(manifest['tabs'])==10
    assert manifest['tab_width_mm']>=5 and manifest['routing_gap_mm']>=2
    assert .5<=manifest['mousebite_diameter_mm']<=.8
    web=manifest['mousebite_pitch_mm']-manifest['mousebite_diameter_mm']
    assert .2-1e-6<=web<=.3+1e-6
    vs=[t for t in board.GetTracks() if isinstance(t,p.PCB_VIA)]
    assert all(.15<=p.ToMM(v.GetDrillValue())<=.5 for v in vs)
    assert all(p.ToMM(v.GetWidth(p.F_Cu)-v.GetDrillValue())>=.1-1e-6 for v in vs)
    holes=[(f,q) for f in board.GetFootprints() for q in f.Pads() if q.GetDrillSize().x]
    plated=[(f,q) for f,q in holes if q.GetAttribute()==p.PAD_ATTRIB_PTH]
    annuli=[min(p.ToMM(q.GetSize().x-q.GetDrillSize().x),p.ToMM(q.GetSize().y-q.GetDrillSize().y))/2 for f,q in plated]
    assert min(annuli)>=.15-1e-6
    widths=[p.ToMM(t.GetWidth()) for t in board.GetTracks() if not isinstance(t,p.PCB_VIA)]
    assert min(widths)>=.09
    rows=[]
    for f,q in holes:
        rows.append(dict(Reference=f.GetReference(),Pad=q.GetNumber(),X_mm=p.ToMM(q.GetPosition().x),
            KiCad_Y_mm=p.ToMM(q.GetPosition().y),Excellon_Y_mm=-p.ToMM(q.GetPosition().y),
            Hole_X_mm=p.ToMM(q.GetDrillSize().x),Hole_Y_mm=p.ToMM(q.GetDrillSize().y),
            Rotation_degrees=q.GetOrientationDegrees(),
            Treatment='PLATED - LEAVE OPEN' if q.GetAttribute()==p.PAD_ATTRIB_PTH else 'NPTH - LEAVE OPEN'))
    return dict(local_manufacturing_screen='PASS',panel_size_mm=[151,139],designs=3,
        tabs=10,tab_width_mm=5,mousebite_diameter_mm=.6,mousebite_web_mm=round(web,4),
        vias_to_fill=len(vs),via_drill_counts={str(k):v for k,v in sorted(Counter(p.ToMM(v.GetDrillValue()) for v in vs).items())},
        component_holes_to_leave_open=len(plated),npth_to_leave_open=len(holes)-len(plated),
        minimum_component_annular_ring_mm=round(min(annuli),4),minimum_track_width_mm=min(widths),
        full_clearance_drc='See evidence/acceptance.json; source hashes checked',
        cam_approval=False,remaining='JLC confirmation of fixed stack, supplied routing and via treatment; no supplier response received'),rows


def verify_open_drills(holes,folder):
    """Check every open round hole and USB anchor slot in emitted Excellon."""
    for plated,filename in [(True,'Panel-PTH.drl'),(False,'Panel-NPTH.drl')]:
        tools={};current=None;via=False;hits=[]
        for line in (folder/filename).read_text().splitlines():
            if 'TA.AperFunction' in line:via='ViaDrill' in line
            match=re.fullmatch(r'T(\d+)C([\d.]+)',line)
            if match:tools[match[1]]=(float(match[2]),via)
            match=re.fullmatch(r'T(\d+)',line)
            if match:current=tools[match[1]]
            match=re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)(?:G85X(-?[\d.]+)Y(-?[\d.]+))?',line)
            if match and current and not current[1]:
                a=tuple(float(match[i]) for i in (1,2))
                z=tuple(float(match[i]) for i in (3,4)) if match[3] else a
                hits.append((*sorted((a,z)),current[0]))
        for row in holes:
            if row['Treatment'].startswith('PLATED')!=plated:continue
            x,y=row['X_mm'],row['KiCad_Y_mm'];w,h=row['Hole_X_mm'],row['Hole_Y_mm']
            length=abs(w-h)/2;angle=math.radians(-row['Rotation_degrees'])
            dx,dy=(length,0) if w>=h else (0,length)
            dx,dy=dx*math.cos(angle)-dy*math.sin(angle),dx*math.sin(angle)+dy*math.cos(angle)
            a,z=sorted(((x-dx,-(y-dy)),(x+dx,-(y+dy))))
            matched=next((i for i,(aa,zz,d) in enumerate(hits) if abs(d-min(w,h))<1e-6
                and all(abs(v-u)<=.000501 for v,u in zip((*a,*z),(*aa,*zz)))),None)
            assert matched is not None,(row['Reference'],row['Pad'],'missing or changed open drill/slot')
            hits.pop(matched)
        assert not hits,('unexpected open drills',filename)


def generate(out):
    panel=p.LoadBoard(str(HERE/'Panel.kicad_pcb'))
    manifest=json.loads((HERE/'panel-manifest.json').read_text())
    acceptance=json.loads((out/'evidence/acceptance.json').read_text())
    assert acceptance['cad_checks']=='PASS'
    assert {n:sha(path) for n,path in SOURCES.items()}==acceptance['source_sha256'],'Stale electrical acceptance'
    assert sha(HERE/'Panel.kicad_pcb')==acceptance['panel_sha256'],'Stale panel acceptance'
    with (out/'all-vias.csv').open(encoding='utf-8-sig',newline='') as f:vias=list(csv.DictReader(f))
    for path in [out/'gerbers/Panel-job.gbrjob',out/'stencil/bench-stencil-job.gbrjob']:
        normalize_job(path);validate_job(json.loads(path.read_text()))
    for filename,function in COPPER_FILES.items():
        text=(out/'gerbers'/filename).read_text()
        assert '%TF.FileFunction,'+function+'*%' in text,(filename,'Incorrect Gerber copper layer header')
    result,holes=inspect(panel,manifest,vias)
    verify_open_drills(holes,out/'gerbers')
    result['open_component_npth_and_slot_excellon_check']='PASS'
    result['source_sha256']=acceptance['source_sha256'];result['panel_sha256']=acceptance['panel_sha256']
    with (out/'do-not-fill-holes.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(holes[0]));writer.writeheader();writer.writerows(holes)
    save_json(out/'manufacturing-review.json',result);save_json(out/'order-settings.json',ORDER)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="190mm" height="165mm" viewBox="-5 -12 190 165">',
         '<rect x="-5" y="-12" width="190" height="165" fill="white"/>',
         '<g font-family="sans-serif" font-size="2.5"><text x="0" y="-7">Rev-A hole treatment / component-side view / coordinates in mm</text>',
         f'<text x="0" y="147">Blue: fill/cap {result["vias_to_fill"]} vias. Red: {result["component_holes_to_leave_open"]} plated holes OPEN. Grey: {result["npth_to_leave_open"]} NPTH OPEN.</text>',
         '<text x="0" y="152">Gerber/Excellon Y is negative of drawing Y. CSV coordinates and tool attributes are authoritative.</text></g>',
         outline(panel).svg(scale_factor=.04,fill_color='#eeeeee')]
    for row in vias:
        svg.append(f'<circle cx="{row["KiCad X mm"]}" cy="{row["KiCad Y mm"]}" r=".32" fill="#1761ac"/>')
    for row in holes:
        x,y=row['X_mm'],row['KiCad_Y_mm'];colour='#cf222e' if row['Treatment'].startswith('PLATED') else '#666'
        svg.append(f'<ellipse cx="{x}" cy="{y}" rx="{row["Hole_X_mm"]/2}" ry="{row["Hole_Y_mm"]/2}" transform="rotate({-row["Rotation_degrees"]} {x} {y})" fill="white" stroke="{colour}" stroke-width=".16"/>')
    svg.append('</svg>');atomic_text(out/'via-treatment.svg','\n'.join(svg))
    job=json.loads((out/'gerbers/Panel-job.gbrjob').read_text())
    lines=['# Exact stack and file-layer mapping','',
        'Order: nominal 1.6 mm, four layers, JLC041611-2116, 1 oz outer/inner, ENIG.',
        'The CAD model uses the following thicknesses; total including both masks is 1.578 mm.',
        'Keep the 0.109 mm outer dielectrics. No stack substitution is authorized.',
        'The source model uses 0.030 mm inner copper for the selected nominal 1 oz construction;',
        'JLC must confirm the construction against this table. Do not silently change it to 0.5 oz.',
        '', '| Layer/material | Thickness (mm) |','|---|---:|']
    for r in job['MaterialStackup']:
        if 'Thickness' in r:lines.append(f'| {r["Name"]} | {r["Thickness"]} |')
    lines+=['','| File | Function |','|---|---|']
    for r in job['FilesAttributes']:lines.append(f'| {r["Path"]} | {r["FileFunction"]} |')
    lines+=['','USB design target: 90 ohm differential, width 0.1466 mm, gap 0.1501 mm, F.Cu over In1 GND.',
        'Paid impedance control/testing: NO. Exported job metadata reflects this economy selection.',
        'Gerber profile centerlines define 151 x 139 mm. The 0.05 mm drawing stroke does not enlarge the board.',
        'Gerber/drill coordinates: X right, negative Y downward; drawings use positive Y downward.']
    atomic_text(out/'STACK_AND_LAYERS.md','\n'.join(lines)+'\n')
    return result


def bundle(out):
    names=['Panel-Gerbers-QUOTE.zip','Stencil-QUOTE.zip','MANUFACTURING_REVIEW.md',
        'order-settings.json','STACK_AND_LAYERS.md','manufacturing-review.json',
        'panel-mechanical.svg','panel-manifest.json','via-treatment.svg',
        'all-vias.csv','do-not-fill-holes.csv','STENCIL_REVIEW.md','stencil-review.json',
        'stencil-support-jig.svg','stencil/stencil.svg','paste-shape-measurements.csv',
        'paste-land-coverage.csv','supplier-drafts/JLC_CAM_REVIEW.md']
    hashes={name:sha(out/name) for name in names}
    with zipfile.ZipFile(out/'CAM-review-attachments.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in names:z.write(out/name,name)
        z.writestr('attachment-sha256.json',json.dumps(hashes,indent=2)+'\n')
