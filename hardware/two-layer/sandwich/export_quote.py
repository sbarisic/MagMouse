"""Validate all four boards and export a reproducible supplier-quote package.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import collections,csv,hashlib,json,subprocess,sys,zipfile,xml.etree.ElementTree as ET
import pcbnew as p
from route_main import HERE,ROOT,CLI
from split_main import export
sys.path.insert(0,str(ROOT/'build/two-layer/python'))
sys.path.insert(0,str(HERE.parent))
from finish_copper import polygons
from shapely.geometry import Point

BOARDS={'Lower':HERE/'lower/Lower.kicad_pcb','Upper':HERE/'upper/Upper.kicad_pcb',
        'Wheel':HERE/'wheel/Wheel.kicad_pcb','Encoder':HERE.parent/'encoder/Encoder.kicad_pcb'}
OUT=HERE/'quote-package'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(*args):subprocess.run([str(CLI),*map(str,args)],check=True)
def write_csv(path,fields,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
def main():
    OUT.mkdir(exist_ok=True);review=HERE/'routing-review';review.mkdir(exist_ok=True)
    reference,reference_pins=export(HERE/'main-circuit/Main.kicad_sch',review/'Main-reference.xml')
    ownership=json.loads((HERE/'partition.json').read_text())['component_ownership']
    report={};combined=[];allpins={};inventory=[]
    for name,path in BOARDS.items():
        before=sha(path);folder=OUT/name;folder.mkdir(exist_ok=True)
        sch=path.with_suffix('.kicad_sch')
        run('sch','erc','--format','json','-o',review/(name+'-erc.json'),sch)
        erc=json.loads((review/(name+'-erc.json')).read_text());assert not [v for sheet in erc['sheets'] for v in sheet['violations']],name+' ERC'
        run('pcb','drc','--format','json','--schematic-parity','-o',review/(name+'-drc.json'),path)
        drc=json.loads((review/(name+'-drc.json')).read_text());assert not drc['violations'] and not drc['unconnected_items'] and not drc.get('schematic_parity'),name+' DRC'
        comps,pins=export(sch,review/(name+'.xml'));allpins[name]=pins
        if name in ('Lower','Upper'):
            owned={r for r,o in ownership.items() if o==name}
            assert owned<=set(comps)
            for ref in owned:
                assert comps[ref].findtext('value')==reference[ref].findtext('value')
                assert {k:v for k,v in pins.items() if k[0]==ref}=={k:v for k,v in reference_pins.items() if k[0]==ref},ref
        board=p.LoadBoard(str(path));assert board.GetCopperLayerCount()==2
        outline=p.SHAPE_POLY_SET();assert board.GetBoardPolygonOutlines(outline,False)
        dimensions=tuple(p.ToMM(outline.BBox().GetSize()))
        assert dimensions==({'Lower':(70.,100.),'Upper':(70.,100.),'Wheel':(70.,67.),'Encoder':(14.,18.)}[name])
        run('pcb','export','gerbers','-l','F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts','--subtract-soldermask','-o',str(folder/'gerbers')+'/',path)
        run('pcb','export','drill','--format','excellon','--excellon-units','mm','--excellon-separate-th','--excellon-oval-format','route','--generate-report','-o',str(folder/'gerbers')+'/',path)
        groups=collections.defaultdict(list);positions=[];manual=[]
        for f in sorted(board.GetFootprints(),key=lambda f:f.GetReference()):
            ref=f.GetReference();fields=f.GetFieldsText();mpn=fields.get('MPN','')
            if f.IsDNP() or f.IsExcludedFromBOM():continue
            if not mpn:
                manual.append({'Reference':ref,'Value':f.GetValue(),'Footprint':str(f.GetFPID().GetLibItemName()),'Reason':'Wire pad, test access, or component without a purchasing MPN; review manually'})
                continue
            lcsc=fields.get('LCSC','');manufacturer=fields.get('Manufacturer','');footprint=str(f.GetFPID().GetLibItemName())
            key=(f.GetValue(),footprint,lcsc,manufacturer,mpn);groups[key].append(ref)
            inventory.append({'Board':name,'Reference':ref,'Value':f.GetValue(),'MPN':mpn,'LCSC':lcsc,'Footprint':footprint})
            if not f.IsExcludedFromPosFiles():
                x,y=p.ToMM(f.GetPosition());positions.append({'Designator':ref,'Mid X':f'{x:.6f}mm','Mid Y':f'{-y:.6f}mm','Layer':'bottom' if f.IsFlipped() else 'top','Rotation':f'{f.GetOrientationDegrees()%360:.4f}'})
        bom=[]
        for (value,footprint,lcsc,manufacturer,mpn),refs in groups.items():
            row={'Comment':value,'Designator':','.join(refs),'Footprint':footprint,'LCSC Part #':lcsc,'Manufacturer':manufacturer,'MPN':mpn,'Quantity':len(refs)};bom.append(row)
            combined.append({'Board':name,**row})
        bomfields=['Comment','Designator','Footprint','LCSC Part #','Manufacturer','MPN','Quantity']
        write_csv(folder/(name+'-BOM.csv'),bomfields,bom)
        write_csv(folder/(name+'-CPL.csv'),['Designator','Mid X','Mid Y','Layer','Rotation'],positions)
        write_csv(folder/(name+'-manual-items.csv'),['Reference','Value','Footprint','Reason'],manual)
        with zipfile.ZipFile(OUT/(name+'-gerbers.zip'),'w',zipfile.ZIP_DEFLATED) as archive:
            for f in sorted((folder/'gerbers').iterdir()):archive.write(f,f.name)
        for side,layers in [('front','F.Cu,F.Silkscreen,Edge.Cuts'),('back','B.Cu,B.Silkscreen,Edge.Cuts')]:
            run('pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-l',layers,'-o',review/(name+'-'+side+'.svg'),path)
            svg=review/(name+'-'+side+'.svg')
            svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
        assert sha(path)==before,'Exporter changed PCB'
        tracks=collections.defaultdict(lambda:collections.Counter())
        for t in board.GetTracks():
            if not isinstance(t,p.PCB_VIA):tracks[t.GetNetname()][str(round(p.ToMM(t.GetWidth()),4))]+=p.ToMM(t.GetLength())
        (review/(name+'-track-widths.json')).write_text(json.dumps({n:{w:round(v,3) for w,v in widths.items()} for n,widths in sorted(tracks.items())},indent=2)+'\n')
        via_in_pad=[]
        vias=[t for t in board.GetTracks() if isinstance(t,p.PCB_VIA)]
        for f in board.GetFootprints():
            for pad in f.Pads():
                if pad.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
                shape=p.SHAPE_POLY_SET();pad.TransformShapeToPolygon(shape,pad.GetLayer(),0,p.FromMM(.001),p.ERROR_OUTSIDE)
                shapes=polygons(shape)
                for v in vias:
                    point=Point(p.ToMM(v.GetPosition()))
                    if any(poly.intersects(point.buffer(p.ToMM(v.GetDrill())/2)) for poly in shapes):
                        via_in_pad.append({'reference':f.GetReference(),'pad':pad.GetNumber(),'via_xy_mm':list(p.ToMM(v.GetPosition())),'drill_mm':p.ToMM(v.GetDrill())})
        (folder/(name+'-via-in-pad.json')).write_text(json.dumps(via_in_pad,indent=2)+'\n')
        assert not via_in_pad,name+' still has a via hole in an SMD land'
        assert all(v.GetDrillValue()>=p.FromMM(.3) for v in vias),name+' has a sub-0.30 mm via'
        report[name]={'source':str(path.relative_to(ROOT)),'sha256':before,'dimensions_mm':dimensions,'copper_layers':2,
            'erc_findings':0,'drc_findings':0,'unconnected_items':0,'schematic_parity_findings':0,'ignored_checks':drc['ignored_checks'],
            'fitted_bom_components':sum(r['Quantity'] for r in bom),'unique_bom_lines':len(bom),'placement_entries':len(positions),
            'via_hole_pad_intersections':len(via_in_pad),
            'vias':sum(isinstance(t,p.PCB_VIA) for t in board.GetTracks()),
            'smallest_drill_mm':min(p.ToMM(t.GetDrill()) for t in board.GetTracks() if isinstance(t,p.PCB_VIA)),
            'minimum_track_mm':min(p.ToMM(t.GetWidth()) for t in board.GetTracks() if not isinstance(t,p.PCB_VIA))}
        rules=json.loads(path.with_suffix('.kicad_pro').read_text())['board']['design_settings']['rules']
        report[name]['fabrication_rules']={k:rules[k] for k in ('min_through_hole_diameter','min_via_diameter','min_via_annular_width','min_hole_clearance','min_hole_to_hole','min_clearance')}
    for wire in json.loads((HERE/'partition.json').read_text())['wires']:
        for side in ('Lower','Upper'):
            ref,pin=wire[side.lower()].split('.');assert allpins[side][ref,pin]==wire['net']
    write_csv(OUT/'combined-BOM.csv',['Board',*bomfields],combined)
    write_csv(OUT/'component-inventory.csv',['Board','Reference','Value','MPN','LCSC','Footprint'],inventory)
    (review/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    files={f.relative_to(OUT).as_posix():sha(f) for f in OUT.rglob('*') if f.is_file() and f.name not in ('SHA256SUMS.json','MagMouse-quote-package.zip')}
    (OUT/'SHA256SUMS.json').write_text(json.dumps(files,indent=2)+'\n')
    with zipfile.ZipFile(HERE/'MagMouse-quote-package.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for f in sorted(OUT.rglob('*')):
            if f.is_file():archive.write(f,f.relative_to(OUT).as_posix())
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
