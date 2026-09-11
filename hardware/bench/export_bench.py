"""Export quote-only bare panel, reviewed population variant and stencil audit."""
from collections import Counter,defaultdict
import csv
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from build_panel import HERE,ROOT,SOURCES,OFFSETS,sha,outline,xy,save_json
sys.path.insert(0,str(ROOT/'hardware/quotes'))
from export_quote_packages import read_components,write_csv,via_inventory,validate_drills
import pcbnew as p

CLI=Path(sys.executable).with_name('kicad-cli.exe')
OUT=HERE/'package'
LAYERS=('F.Cu','In1.Cu','In2.Cu','B.Cu')


def run(args):
    result=subprocess.run([str(CLI),*map(str,args)],capture_output=True,text=True)
    with (OUT/'export.log').open('a',encoding='utf-8') as f:f.write(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)


def track_key(t,dx=0,dy=0,prefix=''):
    v=isinstance(t,p.PCB_VIA)
    return (prefix+t.GetNetname(),t.GetStart().x+dx,t.GetStart().y+dy,t.GetEnd().x+dx,t.GetEnd().y+dy,
            t.GetWidth(p.F_Cu) if v else t.GetWidth(),t.GetDrillValue() if v else 0,t.GetLayer())


def fill_vertices(board,dx=0,dy=0,prefix=''):
    points=Counter()
    for z in board.Zones():
        if z.GetIsRuleArea():continue
        for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
            if not z.IsOnLayer(layer):continue
            polys=z.GetFilledPolysList(layer)
            for i in range(polys.OutlineCount()):
                chains=[polys.Outline(i)]+[polys.Hole(i,h) for h in range(polys.HoleCount(i))]
                for chain in chains:
                    for j in range(chain.PointCount()):
                        v=chain.CPoint(j);points[(prefix+z.GetNetname(),layer,v.x+dx,v.y+dy)]+=1
    return points


def verify_panel(panel,manifest):
    refs={f.GetReference():f for f in panel.GetFootprints()};tracks=Counter();filled=Counter();pad_count=0
    for name,path in SOURCES.items():
        assert sha(path)==manifest['units'][name]['sha256'],name+' stale panel source'
        b=p.LoadBoard(str(path));dx,dy=tuple(xy(*OFFSETS[name]));prefix=name+'/'
        tracks.update(track_key(t,dx,dy,prefix) for t in b.GetTracks());filled.update(fill_vertices(b,dx,dy,prefix))
        for f in b.GetFootprints():
            pf=refs[name[0]+'_'+f.GetReference()]
            assert pf.GetPosition()==f.GetPosition()+xy(*OFFSETS[name])
            assert pf.GetOrientationDegrees()==f.GetOrientationDegrees()
            def key(pad,x=0,y=0,pre=''):
                return (pad.GetNumber(),pad.GetPosition().x+x,pad.GetPosition().y+y,
                        pad.GetSize().x,pad.GetSize().y,pad.GetLayerSet().FmtHex(),pre+pad.GetNetname() if pad.GetNetCode() else '')
            assert Counter(key(a,dx,dy,prefix) for a in f.Pads())==Counter(key(a) for a in pf.Pads()),pf.GetReference()
            pad_count+=len(list(f.Pads()))
    assert tracks==Counter(track_key(t) for t in panel.GetTracks()),'Panel track/via geometry or net changed'
    assert filled==fill_vertices(panel),'Panel saved zone copper differs from translated sources'
    panel.BuildConnectivity()
    assert panel.GetConnectivity().GetUnconnectedCount(False)==0,'Panel has disconnected copper'
    poly=outline(panel)
    assert poly.is_valid
    # Every tab drill remains outside source board material; fixed geometry
    # checks do not claim that the router can mill every inside corner.
    from shapely.affinity import translate
    from shapely.geometry import Point
    polygons={n:translate(outline(p.LoadBoard(str(path))),*OFFSETS[n]) for n,path in SOURCES.items()}
    for tab in manifest['tabs']:
        for x,y in tab['holes']:
            assert all(Point(x,y).buffer(.3).distance(poly)>=.199 for poly in polygons.values())
    return dict(source_pad_count=pad_count,tracks_and_vias=sum(tracks.values()),
                filled_polygon_vertices=sum(filled.values()),native_unrouted=0,
                unit_transforms_and_net_isolation='PASS',saved_copper_translation='PASS',
                tab_drill_unit_clearance_mm=.2,manufacturing_release=False)


def procurement():
    grouped=defaultdict(list);parts={};population=[];excluded=[]
    observations=json.loads((HERE/'sourcing-observations.json').read_text())['items']
    # Public catalogue evidence is a sourcing checkpoint, not a delivered cart.
    # Explicit reviewed alternate suppliers take precedence over LCSC listings.
    for item in json.loads((HERE/'lcsc-listing-evidence.json').read_text(encoding='utf-8')):
        observations.setdefault(item['MPN'],dict(supplier='LCSC',url=item['URL'],
            stock_observed=item['stock'],moq=item['moq'],multiple=item['multiple'],
            currency='USD',tiers=item['tiers'],status='Public listing; delivery and tax not quoted'))
    for name,path in SOURCES.items():
        target=OUT/(name+'-netlist.xml');run(['sch','export','netlist','--format','kicadxml','-o',target,path.with_suffix('.kicad_sch')])
        comps,_=read_components(target)
        for ref,c in comps.items():
            if c['excluded'] or c['dnp'] or (name=='Main' and ref=='U32'):
                excluded.append(dict(board=name,reference=ref,reason='IMU omitted in bench variant' if ref=='U32' else 'Copper-only test pad or source DNP'));continue
            mpn=c['fields'].get('MPN','');assert mpn,(name,ref)
            substitutes={('Main','R25'):'CRCW0603887KFKEA',('Wheel','R113'):'CRCW060334K8FKEA'}
            purchase=substitutes.get((name,ref),mpn)
            key=(purchase,c['footprint']);grouped[key].append(name+'/'+ref);parts[key]=(mpn,c)
            population.append(dict(board=name,reference=ref,panel_reference=name[0]+'_'+ref,mpn=mpn,purchase_mpn=purchase,
                method='HAND / OPTICAL AFTER REFLOW' if ref=='U35' else 'TOP SMT REFLOW'))
    rows=[]
    for (purchase,fp),refs in sorted(grouped.items()):
        mpn,c=parts[purchase,fp];o=observations.get(purchase,{})
        required=len(refs);passive=fp.startswith(('Resistor_SMD:R_0603','Capacitor_SMD:C_0603','Capacitor_SMD:C_0805'))
        # Suggested quantity remains distinct from unverified vendor MOQ.
        suggested=required+max(2,math.ceil(required*.1)) if passive else required
        moq=o.get('moq');multiple=o.get('multiple');qty=max(moq,math.ceil(suggested/multiple)*multiple) if moq and multiple else suggested
        unit=o.get('unit_price')
        for tier in sorted(o.get('tiers',[]),key=lambda t:t['quantity']):
            if qty>=tier['quantity']:unit=tier['price']
        stock=o.get('stock_observed')
        available=stock is not None and stock>=qty
        if not available:unit=None
        status=o.get('status','MOQ, stock, price and shipping require live cart verification')
        if not available:status='UNPRICED: stock unavailable or unverified. '+status
        rows.append(dict(MPN=purchase,Original_MPN=mpn,Footprint=fp,References=';'.join(refs),Required=required,
            Suggested_purchase=qty,Spares=qty-required,MOQ=moq or '',Multiple=multiple or '',
            Supplier=o.get('supplier','LCSC candidate'),URL=o.get('url','https://www.lcsc.com/product-detail/'+c['fields'].get('LCSC','')+'.html'),
            Stock_observed=stock if stock is not None else '',
            Currency=o.get('currency',''),Unit_price=unit if unit is not None else '',
            Extended_price=round(unit*qty,4) if unit is not None else '',Status=status))
    write_csv(OUT/'one-set-purchasing.csv',list(rows[0]),rows)
    write_csv(OUT/'population.csv',list(population[0]),population)
    save_json(OUT/'excluded-population.json',excluded)
    assert len(population)==291, len(population) # 292 physical parts, less U32; includes separately fitted U35.
    return population,rows


def stencil(panel,population):
    byref={f.GetReference():f for f in panel.GetFootprints()}
    wanted={row['panel_reference'] for row in population if row['method']=='TOP SMT REFLOW'}
    removed=[]
    for ref,f in byref.items():
        if ref not in wanted:
            for pad in f.Pads():
                if pad.IsOnLayer(p.F_Paste):
                    ls=pad.GetLayerSet();ls.RemoveLayer(p.F_Paste);pad.SetLayerSet(ls);removed.append(ref)
    apertures=[]
    for ref in sorted(wanted):
        f=byref[ref]
        for pad in f.Pads():
            if not pad.IsOnLayer(p.F_Paste):continue
            margin=pad.GetSolderPasteMargin(p.F_Cu)
            w=p.ToMM(pad.GetSize().x+2*margin.x);h=p.ToMM(pad.GetSize().y+2*margin.y)
            ratio=w*h/(2*(w+h)*.1)
            apertures.append(dict(Reference=ref,Pad=pad.GetNumber(),Width_mm=w,Height_mm=h,
                Rectangular_area_ratio_at_0_10mm=round(ratio,4),Shape=int(pad.GetShape()),
                Review='CHECK RELEASE' if ratio<.66 else 'Rectangular screening pass'))
    assert 'M_U32' in removed and all(a['Reference']!='M_U32' for a in apertures)
    assert wanted=={a['Reference'] for a in apertures},'SMT part has no paste aperture'
    write_csv(OUT/'stencil-apertures.csv',list(apertures[0]),apertures)
    tmp=ROOT/'build/bench-stencil.kicad_pcb';p.SaveBoard(str(tmp),panel)
    run(['pcb','export','gerbers','-l','F.Paste','-o',OUT/'stencil',tmp])
    run(['pcb','export','svg','--mode-single','-l','F.Paste','--page-size-mode','2','--exclude-drawing-sheet','--drill-shape-opt','0','-o',OUT/'stencil/stencil.svg',tmp])
    save_json(OUT/'stencil-review.json',dict(thickness_mm=.10,populated_smt_references=len(wanted),
        aperture_count=len(apertures),deliberately_removed_paste=sorted(set(removed)),
        below_screening_ratio=[a for a in apertures if a['Review']=='CHECK RELEASE'],
        status='APERTURE REVIEW DRAFT - package-specific solder coverage and stencil vendor confirmation required',
        scope='Rectangular aperture ratio screening; not paste-transfer or hidden-joint acceptance'))


def assembly_aids(population,rows):
    """Printable support plan plus source-coordinate pin-one and hidden-pad audit."""
    selected={(r['board'],r['reference']):r for r in population}
    checklist=[]
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="220mm" height="200mm" viewBox="0 0 220 200">',
         '<rect width="220" height="200" fill="white"/>',
         '<g font-family="sans-serif" font-size="2.5" stroke-width="0.15">',
         '<text x="8" y="8">Rev-A bench stencil support plan / print 100%, no scaling</text>',
         '<text x="8" y="13">CAM group positions are pending. Align paste to real pads before printing.</text>']
    for name,path in SOURCES.items():
        board=p.LoadBoard(str(path));dx,dy=OFFSETS[name];sx,sy=dx+25,dy+25
        shape=outline(board);points=' '.join(f'{x+sx},{y+sy}' for x,y in shape.exterior.coords)
        svg.append(f'<polygon points="{points}" fill="#f5f5f5" stroke="#222"/>')
        for ring in shape.interiors:
            points=' '.join(f'{x+sx},{y+sy}' for x,y in ring.coords)
            svg.append(f'<polygon points="{points}" fill="white" stroke="#222"/>')
        x0,y0,x1,y1=shape.bounds
        svg.append(f'<text x="{x0+sx+2}" y="{y0+sy+5}">{name}</text>')
        # Foam/tape blocks must be movable and must not overlap the board.
        for x,y in [(x0+sx-4,(y0+y1)/2+sy), (x1+sx+1,(y0+y1)/2+sy)]:
            svg.append(f'<rect x="{x}" y="{y}" width="3" height="8" fill="none" stroke="#176c93" stroke-dasharray="1 1"/>')
        for f in board.GetFootprints():
            ref=f.GetReference();fp=str(f.GetFPID().GetLibItemName())
            if (name,ref) not in selected:continue
            if not (ref.startswith(('U','Q','D','J')) or 'CP_' in fp):continue
            pad=next((a for a in f.Pads() if a.GetNumber()=='1'),None)
            hidden=any(word in fp.upper() for word in ('QFN','DFN','SON','ESP32','VQFN','RGE','WQFN')) or any(a.GetNumber()=='' and a.IsOnLayer(p.F_Paste) for a in f.Pads())
            checklist.append(dict(Board=name,Reference=ref,MPN=selected[name,ref]['purchase_mpn'],Footprint=fp,
                Method=selected[name,ref]['method'],Hidden_pad_review='REQUIRED' if hidden else 'Check manufacturer drawing',
                Pin1_X_mm=p.ToMM(pad.GetPosition().x) if pad else '',Pin1_Y_mm=p.ToMM(pad.GetPosition().y) if pad else '',
                Rotation_deg=f.GetOrientationDegrees(),
                Inspection='Compare package marking/polarity to numbered pads; underside joint quality is not visually established',
                Profile_MSL_review='OPEN: record received packaging limits before assembly'))
    svg.extend(['<line x1="10" y1="183" x2="110" y2="183" stroke="black"/>',
        '<text x="10" y="180">100 mm calibration bar</text>',
        '<text x="10" y="190">Dashed blocks: removable edge stops; use matching-thickness scrap support.</text>',
        '<text x="10" y="195">Mask unused stencil groups. Depanel bare boards before paste/reflow. Main U32: DNP.</text></g></svg>'])
    (OUT/'stencil-support-jig.svg').write_text('\n'.join(svg),encoding='utf-8')
    write_csv(OUT/'pin-one-hidden-pad-checklist.csv',list(checklist[0]),checklist)
    totals=defaultdict(float)
    for row in rows:
        if row['Extended_price']!='':totals[row['Supplier']+' / '+row['Currency']]+=row['Extended_price']
    save_json(OUT/'component-price-checkpoint.json',dict(status='PARTIAL PUBLIC LISTINGS, NOT A DELIVERED CART',
        population_sets=1,priced_mpn_lines=sum(r['Extended_price']!='' for r in rows),mpn_lines=len(rows),
        supplier_currency_subtotals={k:round(v,4) for k,v in totals.items()},
        unpriced_mpn_lines=[r['MPN'] for r in rows if r['Extended_price']==''],
        external_items=json.loads((HERE/'sourcing-observations.json').read_text())['external_items'],
        omitted='U32 only; tools excluded. All unpriced required items remain required. Shipping/taxes are separate and unquoted.'))


def main():
    OUT.mkdir(exist_ok=True);(OUT/'export.log').write_text('')
    incomplete=OUT/'EXPORT_INCOMPLETE.txt'
    incomplete.write_text('Export in progress or failed. Do not use generated files.\n')
    panel=p.LoadBoard(str(HERE/'Panel.kicad_pcb'));manifest=json.loads((HERE/'panel-manifest.json').read_text())
    report=verify_panel(panel,manifest);save_json(OUT/'panel-validation.json',report)
    population,rows=procurement()
    vias=via_inventory(panel);write_csv(OUT/'all-vias.csv',list(vias[0]),vias)
    run(['pcb','export','gerbers','-l',','.join([*LAYERS,'F.Mask','B.Mask','F.SilkS','B.SilkS','Edge.Cuts']),'-o',OUT/'gerbers',HERE/'Panel.kicad_pcb'])
    run(['pcb','export','drill','--format','excellon','--excellon-separate-th','--drill-origin','absolute','--excellon-units','mm','--generate-map','--map-format','svg','-o',OUT/'gerbers',HERE/'Panel.kicad_pcb'])
    validate_drills(OUT/'gerbers/Panel-PTH.drl',vias)
    for name,path in SOURCES.items():
        (OUT/'placement').mkdir(parents=True,exist_ok=True)
        run(['pcb','export','svg','--mode-single','-l','F.Fab,Edge.Cuts','--page-size-mode','2','--exclude-drawing-sheet','--sketch-pads-on-fab-layers','-o',OUT/'placement'/(name+'.svg'),path])
    stencil(panel,population)
    assembly_aids(population,rows)
    # Keep the review notes self-contained when this folder is handed to CAM.
    notes=(HERE/'README.md').read_text(encoding='utf-8').replace('`package/','`')
    (OUT/'MANUFACTURING_NOTES.md').write_text(notes,encoding='utf-8')
    for name in ('SOURCING.md','WURTH_ENQUIRY.md','ORDER_READINESS.md','BENCH_FIXTURE.md','ASSEMBLY_AND_BRINGUP.md',
                 'COST_CHECKPOINT.md','CAD_REVIEW.md','quote-observations.json','sourcing-observations.json',
                 'bench-fixture.svg','panel-mechanical.svg','panel-manifest.json'):
        shutil.copyfile(HERE/name,OUT/name)
    (OUT/'copper-review').mkdir(exist_ok=True)
    for layer in LAYERS:
        run(['pcb','export','svg','--mode-single','-l',layer+',Edge.Cuts','--page-size-mode','2',
             '--exclude-drawing-sheet','-o',OUT/'copper-review'/(layer+'.svg'),HERE/'Panel.kicad_pcb'])
    save_json(OUT/'release-status.json',dict(ready_for_order=False,
        label='Rev-A bench prototype - QUOTE ONLY',source_boards=manifest['units'],
        open_gates='See hardware/bench/README.md; supplier, assembly, mechanical and CAM review remain open'))
    for folder,name in [('gerbers','Panel-Gerbers-QUOTE.zip'),('stencil','Stencil-QUOTE.zip')]:
        with zipfile.ZipFile(OUT/name,'w',zipfile.ZIP_DEFLATED) as z:
            for f in sorted((OUT/folder).glob('*')):
                if f.suffix!='.svg':z.write(f,f.name)
    incomplete.unlink()
    save_json(OUT/'file-sha256.json',{str(f.relative_to(OUT)):sha(f) for f in sorted(OUT.rglob('*')) if f.is_file() and f.name!='file-sha256.json'})
    print('Verified panel and exported',len(population),'population references;',len(rows),'purchase lines')


if __name__=='__main__':main()
