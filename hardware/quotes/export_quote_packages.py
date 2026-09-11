"""Export separate, traceable JLCPCB pricing inputs. Run with KiCad 10 Python.

Never edits CAD sources, substitutes components, or creates a production panel.
CSV files are machine interfaces, exported with Python's csv module.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

import pcbnew as p

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'hardware/modular'))
from schematic_io import parse, get

BOARDS = {'Main': 'hardware/modular/main/Main',
          'Wheel': 'hardware/modular/wheel/Wheel',
          'Encoder': 'hardware/encoder/Encoder'}
STATUS = 'QUOTE ONLY - NOT FOR FABRICATION OR ASSEMBLY'
# This is an explicit quote variant, not a modification of schematic DNP flags.
MANUAL = {'Main': {'U35': 'PMW3360DM-T2QU: customer-supplied/post-assembly optical sensor; catalog stock unavailable in recorded sourcing review'}}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def natural(ref):
    return tuple(int(s) if s.isdigit() else s for s in re.split(r'(\d+)', ref))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def write_csv(path, columns, rows):
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read_components(netlist):
    comps = {}
    tree = ET.parse(netlist)
    for c in tree.findall('./components/comp'):
        ref = c.get('ref')
        require(ref not in comps, 'Duplicate schematic reference ' + ref)
        props = {q.get('name') for q in c.findall('property')}
        fields = {q.get('name'): q.text or '' for q in c.findall('./fields/field')}
        lcsc = fields.get('LCSC', '')
        require(not lcsc or re.fullmatch(r'C\d+', lcsc), ref + ': invalid catalog ID')
        require(not fields.get('JLCPCB Part #') or fields['JLCPCB Part #'] == lcsc,
                ref + ': conflicting supplier IDs')
        comps[ref] = dict(value=c.findtext('value'), footprint=c.findtext('footprint'),
                          fields=fields, dnp='dnp' in props, excluded='exclude_from_bom' in props)
    return comps, tree


def classify(name, comps, fps):
    require(set(comps) == set(fps), 'Schematic/PCB reference coverage differs')
    assembly, exclusions = [], []
    require(set(MANUAL.get(name, {})) <= set(comps), 'Manual variant reference disappeared')
    for ref in sorted(comps, key=natural):
        c, f = comps[ref], fps[ref]
        require(c['value'] == f.GetValue(), ref + ': value mismatch')
        fid = f.GetFPID()
        require(c['footprint'] == str(fid.GetLibNickname()) + ':' + str(fid.GetLibItemName()), ref + ': footprint mismatch')
        require(c['dnp'] == f.IsDNP(), ref + ': DNP mismatch')
        require(c['excluded'] == f.IsExcludedFromBOM(), ref + ': BOM flag mismatch')
        reason = ('DNP in source' if c['dnp'] else
                  'Excluded from source BOM (PCB copper/test access)' if c['excluded'] else
                  MANUAL.get(name, {}).get(ref, ''))
        if reason:
            exclusions.append({'Designator': ref, 'Comment': c['value'], 'Reason': reason,
                               'MPN': c['fields'].get('MPN', ''), 'LCSC Part #': c['fields'].get('LCSC', '')})
        else:
            require(not f.IsExcludedFromPosFiles(), ref + ': assembly part excluded from positions')
            require(c['fields'].get('MPN') and c['fields'].get('LCSC'), ref + ': assembly identity missing')
            assembly.append(ref)
    return assembly, exclusions


def validate_coverage(comps, assembly, exclusions, bom, cpl):
    brefs = [r for row in bom for r in row['Designator'].split(',')]
    crefs = [row['Designator'] for row in cpl]
    excluded = [row['Designator'] for row in exclusions]
    for label, refs in [('BOM', brefs), ('CPL', crefs), ('exclusions', excluded)]:
        require(len(refs) == len(set(refs)), label + ': duplicate references')
    require(set(brefs) == set(crefs) == set(assembly), 'BOM/CPL population coverage mismatch')
    require(not set(assembly) & set(excluded), 'Assembly/exclusion overlap')
    require(set(assembly) | set(excluded) == set(comps), 'Unaccounted schematic references')
    for row in bom:
        require(int(row['Quantity']) == len(row['Designator'].split(',')), 'BOM quantity mismatch')


def make_bom(comps, assembly):
    grouped = defaultdict(list)
    for ref in assembly:
        c = comps[ref]
        grouped[(c['value'], c['footprint'], c['fields']['LCSC'], c['fields']['MPN'])].append(ref)
    return [dict(zip(['Comment', 'Footprint', 'LCSC Part #', 'MPN'], key),
                 Designator=','.join(refs), Quantity=len(refs)) for key, refs in grouped.items()]


def make_cpl(native_path, assembly, fps):
    with native_path.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    require(len(rows) == len({r['Ref'] for r in rows}), 'Duplicate native position references')
    native = {r['Ref']: r for r in rows}
    result = []
    for ref in assembly:
        require(ref in native, ref + ': no native KiCad placement')
        row, fp = native[ref], fps[ref]
        x, y, rot = map(float, (row['PosX'], row['PosY'], row['Rot']))
        require(all(math.isfinite(v) for v in (x, y, rot)), ref + ': invalid position')
        require(abs(x - p.ToMM(fp.GetPosition().x)) < 1e-5 and
                abs(y + p.ToMM(fp.GetPosition().y)) < 1e-5, ref + ': position origin mismatch')
        require(abs((rot - fp.GetOrientationDegrees() + 180) % 360 - 180) < 1e-5,
                ref + ': rotation mismatch')
        side = 'top' if fp.GetLayer() == p.F_Cu else 'bottom'
        require(row['Side'] == side, ref + ': placement side mismatch')
        result.append({'Designator': ref, 'Mid X': f'{x:.6f}mm', 'Mid Y': f'{y:.6f}mm',
                       'Rotation': f'{rot % 360:.6f}', 'Layer': side})
    return result


def via_inventory(board):
    pads = [(f.GetReference(), pad) for f in board.GetFootprints() for pad in f.Pads()
            if pad.GetAttribute() == p.PAD_ATTRIB_SMD]
    vias = sorted([v for v in board.GetTracks() if isinstance(v, p.PCB_VIA)],
                  key=lambda v: (v.GetPosition().x, v.GetPosition().y))
    rows = []
    for index, via in enumerate(vias, 1):
        pos = via.GetPosition()
        hits = []
        # Check the actual drill disk, including edge overlap, not just its centre.
        for ref, pad in pads:
            for layer in (p.F_Cu, p.B_Cu):
                if pad.IsOnLayer(layer) and pad.GetEffectiveShape(layer).Collide(pos, via.GetDrillValue() // 2):
                    hits.append(f'{ref}.{pad.GetNumber()}@{board.GetLayerName(layer)}')
        rows.append({'Via': f'V{index:04}', 'UUID': via.m_Uuid.AsString(),
                     'KiCad X mm': round(p.ToMM(pos.x), 6), 'KiCad Y mm': round(p.ToMM(pos.y), 6),
                     'Gerber/CPL X mm': round(p.ToMM(pos.x), 6), 'Gerber/CPL Y mm': round(-p.ToMM(pos.y), 6),
                     'Drill mm': round(p.ToMM(via.GetDrillValue()), 6),
                     'Diameter mm': round(p.ToMM(via.GetWidth(p.F_Cu)), 6),
                     'Net': via.GetNetname(), 'SMD pad drill overlap': ';'.join(hits)})
    return rows


def via_map(board, rows, target):
    box = board.GetBoardEdgesBoundingBox()
    x, y, w, h = [p.ToMM(n) for n in (box.GetX(), box.GetY(), box.GetWidth(), box.GetHeight())]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" viewBox="{x-4} {y-10} {w+8} {h+18}">',
             '<rect x="-1000" y="-1000" width="3000" height="3000" fill="white"/>',
             f'<text x="{x}" y="{y-5}" font-size="{min(2,w/45)}">QUOTE ONLY: red = drill intersects SMD pad; grey = other via</text>']
    outline = p.SHAPE_POLY_SET()
    require(board.GetBoardPolygonOutlines(outline, False), 'Open outline')
    for i in range(outline.OutlineCount()):
        chain = outline.Outline(i)
        points = ' '.join(f'{p.ToMM(chain.CPoint(j).x)},{p.ToMM(chain.CPoint(j).y)}' for j in range(chain.PointCount()))
        parts.append(f'<polygon points="{points}" fill="none" stroke="#263238" stroke-width=".15"/>')
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            pos, size = pad.GetPosition(), pad.GetSize()
            parts.append(f'<rect x="{p.ToMM(pos.x-size.x/2)}" y="{p.ToMM(pos.y-size.y/2)}" '
                         f'width="{p.ToMM(size.x)}" height="{p.ToMM(size.y)}" fill="#e0e6eb" '
                         f'transform="rotate({-pad.GetOrientationDegrees()} {p.ToMM(pos.x)} {p.ToMM(pos.y)})"/>')
    for row in rows:
        color = '#d32f2f' if row['SMD pad drill overlap'] else '#78909c'
        tip = html.escape(f"{row['Via']} {row['Net']} drill {row['Drill mm']} mm {row['SMD pad drill overlap']}")
        parts.append(f'<circle cx="{row["KiCad X mm"]}" cy="{row["KiCad Y mm"]}" r="{max(.18,row["Drill mm"]/2)}" fill="{color}"><title>{tip}</title></circle>')
    parts.append('</svg>')
    target.write_text('\n'.join(parts), encoding='utf-8')


def validate_drills(path, vias):
    """Cross-check actual Excellon via hits against native PCB, including origin."""
    text = path.read_text()
    require('METRIC' in text and 'absolute / metric / decimal' in text, 'Unexpected Excellon convention')
    tools, hits, via_tool, current = {}, [], False, None
    for line in text.splitlines():
        if 'TA.AperFunction' in line:
            via_tool = 'ViaDrill' in line
        tool = re.fullmatch(r'T(\d+)C([\d.]+)', line)
        if tool:
            tools[tool[1]] = (float(tool[2]), via_tool)
        select = re.fullmatch(r'T(\d+)', line)
        if select:
            current = tools[select[1]]
        hit = re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)', line)
        if hit and current and current[1]:
            hits.append((round(float(hit[1]),3), round(float(hit[2]),3), round(current[0],3)))
    # KiCad writes Excellon with 1 um resolution. Preserve native fractional
    # micrometres when matching rather than assuming Python's tie rounding.
    remaining = list(hits)
    for v in vias:
        matches = [i for i,(x,y,d) in enumerate(remaining)
                   if abs(x-v['Gerber/CPL X mm']) <= .000501 and
                   abs(y-v['Gerber/CPL Y mm']) <= .000501 and abs(d-v['Drill mm']) < .000001]
        require(len(matches) == 1, 'Excellon via count/diameter/origin mismatch')
        remaining.pop(matches[0])
    require(not remaining, 'Unexpected Excellon via hits')


def run(cli, args, log):
    result = subprocess.run([str(cli), *map(str, args)], capture_output=True, text=True)
    with log.open('a', encoding='utf-8') as f:
        f.write(json.dumps(list(map(str, args))) + '\n' + result.stdout + result.stderr + '\n')
    require(result.returncode == 0, f'KiCad failed: {args}; see {log}')


def export_board(name, stem, dest, cli):
    source = ROOT / stem
    pcb, sch = source.with_suffix('.kicad_pcb'), source.with_suffix('.kicad_sch')
    inputs = sorted(set(source.parent.glob('*.kicad_sch')) | {pcb, source.with_suffix('.kicad_pro')})
    hashes = {str(f.relative_to(ROOT)).replace('\\', '/'): sha(f) for f in inputs}
    out = dest / name
    evidence, gerbers = out / 'evidence', out / 'gerbers'
    evidence.mkdir(parents=True)
    gerbers.mkdir()
    log = evidence / 'export.log'
    run(cli, ['sch', 'export', 'netlist', '--format', 'kicadxml', '-o', evidence/'netlist.xml', sch], log)
    run(cli, ['pcb', 'drc', '--format', 'json', '--schematic-parity', '-o', evidence/'drc.json', pcb], log)
    drc = json.loads((evidence/'drc.json').read_text())
    require(not any(drc[k] for k in ('violations', 'schematic_parity', 'unconnected_items')),
            name + ': native DRC/parity/unconnected gate failed')
    board = p.LoadBoard(str(pcb))
    board.BuildConnectivity()
    require(board.GetConnectivity().GetUnconnectedCount(False) == 0, name + ': native unrouted remains')
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    require(len(fps) == len(list(board.GetFootprints())), 'Duplicate PCB references')
    comps, tree = read_components(evidence/'netlist.xml')
    assembly, exclusions = classify(name, comps, fps)
    pad_nets = defaultdict(set)
    for ref, fp in fps.items():
        for pad in fp.Pads():
            if pad.GetNumber():
                pad_nets[(ref, pad.GetNumber())].add(pad.GetNetname())
    for net in tree.findall('./nets/net'):
        for node in net.findall('node'):
            require(pad_nets[(node.get('ref'), node.get('pin'))] == {net.get('name')},
                    'PCB pin/net coverage mismatch: ' + node.get('ref') + '.' + node.get('pin'))
    run(cli, ['pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'both',
              '-o', evidence/'native-positions.csv', pcb], log)
    bom, cpl = make_bom(comps, assembly), make_cpl(evidence/'native-positions.csv', assembly, fps)
    validate_coverage(comps, assembly, exclusions, bom, cpl)
    write_csv(out/f'{name}-BOM-QUOTE.csv', ['Comment','Designator','Footprint','LCSC Part #','MPN','Quantity'], bom)
    write_csv(out/f'{name}-CPL-QUOTE.csv', ['Designator','Mid X','Mid Y','Rotation','Layer'], cpl)
    write_csv(out/'excluded-from-assembly.csv', ['Designator','Comment','Reason','MPN','LCSC Part #'], exclusions)
    with (out/f'{name}-BOM-QUOTE.csv').open(encoding='utf-8-sig',newline='') as f:
        saved_bom = list(csv.DictReader(f))
    with (out/f'{name}-CPL-QUOTE.csv').open(encoding='utf-8-sig',newline='') as f:
        saved_cpl = list(csv.DictReader(f))
    validate_coverage(comps,assembly,exclusions,saved_bom,saved_cpl)
    procurement = []
    for ref in sorted(comps, key=natural):
        c = comps[ref]
        if c['excluded'] or c['dnp']:
            continue
        procurement.append({'Designator': ref, 'MPN': c['fields'].get('MPN',''),
                            'LCSC Part #': c['fields'].get('LCSC',''), 'Units for 5 boards': 5,
                            'Quote treatment': 'JLC matching pending' if ref in assembly else 'Separately sourced / manual installation',
                            'Recorded sourcing status': c['fields'].get('Sourcing Status',''),
                            'Supplier URL': c['fields'].get('Supplier URL','')})
    write_csv(out/'procurement-review.csv', list(procurement[0]), procurement)
    vias = via_inventory(board)
    columns = ['Via','UUID','KiCad X mm','KiCad Y mm','Gerber/CPL X mm','Gerber/CPL Y mm','Drill mm','Diameter mm','Net','SMD pad drill overlap']
    write_csv(out/'all-vias.csv', columns, vias)
    vip = [v for v in vias if v['SMD pad drill overlap']]
    write_csv(out/'via-in-pad.csv', columns, vip)
    via_map(board, vias, out/'via-map.svg')
    cu = ['F.Cu','In1.Cu','In2.Cu','B.Cu'] if board.GetCopperLayerCount() == 4 else ['F.Cu','B.Cu']
    run(cli, ['pcb','export','gerbers','--layers',','.join(cu+['F.Mask','B.Mask','F.Silkscreen','B.Silkscreen','F.Paste','B.Paste','Edge.Cuts']),
              '--subtract-soldermask','-o',gerbers,pcb], log)
    run(cli, ['pcb','export','drill','--format','excellon','--drill-origin','absolute','--excellon-units','mm',
              '--excellon-separate-th','--generate-map','--map-format','svg','--generate-report',
              '--report-path',evidence/'drill-report.txt','-o',gerbers,pcb], log)
    for side in ('F','B'):
        run(cli, ['pcb','export','svg','--mode-single','--page-size-mode','2','--exclude-drawing-sheet',
                  '--layers',f'{side}.Fab,{side}.Silkscreen,Edge.Cuts','-o',out/f'assembly-{side}.svg',pcb], log)
    extensions = {'.gtl','.gbl','.gts','.gbs','.gto','.gbo','.gtp','.gbp','.gm1'}
    if len(cu) == 4:
        extensions.update({'.g1','.g2'})
    generated = list(gerbers.iterdir())
    require(extensions <= {f.suffix for f in generated}, name + ': missing Gerber layers')
    require(any(f.suffix == '.drl' for f in generated), name + ': missing drills')
    validate_drills(gerbers/f'{name}-PTH.drl', vias)
    for file in generated:
        if file.suffix in extensions:
            header = file.read_text()[:1500]
            require('%MOMM*%' in header and '%FSLAX46Y46*%' in header, 'Gerber units/precision changed')
    notes = (Path(__file__).parent/'MANUFACTURING_NOTES.md').read_text(encoding='utf-8')
    notes += f'\n## {name} snapshot inventory\n\n{len(comps)} schematic/PCB references; {len(assembly)} quoted placements; {len(exclusions)} explicit exclusions.\n'
    notes += f'{len(vias)} through vias; {len(vip)} drill disks intersect SMD pads.\n'
    notes += f'Via drill counts: {dict(Counter(str(v["Drill mm"]) for v in vias))}.\n'
    notes += '\nSee all-vias.csv, via-in-pad.csv and via-map.svg alongside this archive for exact coordinates and pad references.\n'
    (out/'MANUFACTURING_NOTES.md').write_text(notes,encoding='utf-8')
    (gerbers/'READ_ME_QUOTE_ONLY.txt').write_text(notes,encoding='utf-8')
    with zipfile.ZipFile(out/f'{name}-Gerbers-QUOTE.zip','w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(gerbers.iterdir()):
            if f.suffix != '.svg':
                z.write(f, f.name)
        for filename in ('all-vias.csv','via-in-pad.csv','via-map.svg'):
            z.write(out/filename, 'quote-notes/'+filename)
    parsed = parse(pcb.read_text(encoding='utf-8'))
    stack = get(get(parsed,'setup'),'stackup')
    stack_data = []
    if stack:
        for layer in [q for q in stack[1:] if isinstance(q,list) and q[0] == 'layer']:
            stack_data.append({'layer':layer[1], **{q[0]:q[1] for q in layer[2:] if isinstance(q,list) and len(q)>1}})
    summary = {'status':STATUS,'source_sha256':hashes,'kicad_version':drc['kicad_version'],
               'schematic_pcb_references':len(comps),'assembly_components':len(assembly),'bom_lines':len(bom),
               'excluded_references':exclusions,'assembly_sides':dict(Counter(r['Layer'] for r in cpl)),
               'native_unrouted':0,'physical_drc':0,'schematic_parity':0,
               'bom_cpl_reference_coverage':'PASS: each source reference assembled or explicitly excluded',
               'copper_layers':board.GetCopperLayerCount(),'board_thickness_mm':p.ToMM(board.GetDesignSettings().GetBoardThickness()),
               'saved_stackup':stack_data,'vias':len(vias),'vias_with_smd_drill_overlap':len(vip),
               'via_drill_counts':dict(Counter(str(v['Drill mm']) for v in vias)),
               'coordinate_convention':'Absolute KiCad origin; X right, Y up (negative KiCad Y); same Gerber/drill/CPL origin; no bottom mirroring',
               'rotation_convention':'Native KiCad rotation normalized to [0,360); supplier-specific corrections NOT applied; assembly preview review required',
               'coverage_validation_errors':[]}
    summary['excellon_via_checks'] = 'All CAD via hits matched once, diameter exact; coordinate tolerance 0.000501 mm for 1 um drill export precision'
    require(all(sha(ROOT/f) == value for f,value in hashes.items()), name + ': source changed during export')
    write_json(out/'validation.json', summary)
    write_json(out/'file-sha256.json', {str(f.relative_to(out)).replace('\\','/'):sha(f) for f in sorted(out.rglob('*')) if f.is_file()})
    print(f'{name}: {len(comps)} references, {len(assembly)} assembly, {len(exclusions)} excluded; {len(vip)}/{len(vias)} vias overlap SMD pads', flush=True)
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True,help='New directory; existing output is never overwritten')
    ap.add_argument('--kicad-cli',type=Path,default=Path(sys.executable).with_name('kicad-cli.exe'))
    args = ap.parse_args()
    require(not args.output.exists(), 'Use a new output directory; retain or explicitly remove the old snapshot')
    args.output.mkdir(parents=True)
    try:
        summaries = {name:export_board(name,stem,args.output,args.kicad_cli) for name,stem in BOARDS.items()}
        write_json(args.output/'validation.json', {'status':STATUS,'quantity_per_design':5,'destination':'Croatia 43000',
                                                  'generator_sha256':sha(__file__),
                                                  'notes_template_sha256':sha(Path(__file__).parent/'MANUFACTURING_NOTES.md'),
                                                  'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                                                  'boards':summaries})
        (args.output/'MANUFACTURING_NOTES.md').write_text((Path(__file__).parent/'MANUFACTURING_NOTES.md').read_text(encoding='utf-8'),encoding='utf-8')
        for summary in summaries.values():
            require(all(sha(ROOT/f)==value for f,value in summary['source_sha256'].items()), 'Source changed during batch')
        write_json(args.output/'file-sha256.json', {str(f.relative_to(args.output)).replace('\\','/'):sha(f)
                                                   for f in sorted(args.output.rglob('*')) if f.is_file()})
    except Exception:
        (args.output/'INCOMPLETE_DO_NOT_UPLOAD.txt').write_text('Export failed. See evidence logs; this directory is not a validated quote package.\n')
        raise


if __name__ == '__main__':
    main()
