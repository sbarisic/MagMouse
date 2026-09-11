"""Read-only via cost screening, using KiCad 10's actual copper shapes.

This is not DRC acceptance. It deliberately does not alter production CAD.
"""
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path

import pcbnew as p

from export_quote_packages import BOARDS, ROOT, via_inventory, write_json


def audit(name, stem, expected):
    path = ROOT / (stem + '.kicad_pcb')
    for source, expected_hash in expected.items():
        assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest() == expected_hash, source + ': quote snapshot differs'
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == expected[stem + '.kicad_pcb'], 'Quote snapshot differs from current CAD'
    board = p.LoadBoard(str(path))
    project = json.loads((ROOT/(stem+'.kicad_pro')).read_text())
    if any(v.GetDrillValue() < p.FromMM(.3) for v in board.GetTracks() if isinstance(v, p.PCB_VIA)):
        assert project['board']['design_settings']['rules']['min_via_annular_width'] <= .125
    rows = via_inventory(board)
    vias = {v.m_Uuid.AsString(): v for v in board.GetTracks() if isinstance(v, p.PCB_VIA)}
    copper = list(board.GetTracks()) + [pad for f in board.GetFootprints() for pad in f.Pads()]
    layers = [l for l in board.GetEnabledLayers().Seq() if p.IsCopperLayer(l)]
    # Index native bounding boxes in a spatial grid. Include each proposed
    # 0.55 mm via's radius plus the 0.15 mm screening clearance.
    grid = defaultdict(list)
    cell = p.FromMM(2)
    for item in copper:
        box = item.GetBoundingBox()
        for x in range(math.floor(box.GetLeft()/cell), math.floor(box.GetRight()/cell)+1):
            for y in range(math.floor(box.GetTop()/cell), math.floor(box.GetBottom()/cell)+1):
                grid[x, y].append(item)
    screened = []
    for row in rows:
        if row['Drill mm'] >= .3:
            continue
        via = vias[row['UUID']]
        pos = via.GetPosition()
        radius = p.FromMM(.425)  # 0.55 diameter / 2 + 0.15 clearance
        nearby = {}
        for x in range(math.floor((pos.x-radius)/cell), math.floor((pos.x+radius)/cell)+1):
            for y in range(math.floor((pos.y-radius)/cell), math.floor((pos.y+radius)/cell)+1):
                for item in grid[x, y]:
                    nearby[item.m_Uuid.AsString()] = item
        old_hits, new_hits = set(), set()
        old_radius = via.GetWidth(p.F_Cu)//2 + p.FromMM(.15)
        for uid, item in nearby.items():
            if item.GetNetCode() == via.GetNetCode():
                continue
            for layer in layers:
                if item.IsOnLayer(layer) and via.IsOnLayer(layer):
                    shape = item.GetEffectiveShape(layer)
                    if shape.Collide(pos, radius):
                        new_hits.add(uid)
                    if shape.Collide(pos, old_radius):
                        old_hits.add(uid)
        screened.append(dict(uuid=row['UUID'], net=row['Net'], x_mm=row['KiCad X mm'],
                              y_mm=row['KiCad Y mm'], current_diameter_mm=row['Diameter mm'],
                              current_drill_mm=row['Drill mm'],
                              old_clearance_screen_hits=len(old_hits),
                              proposed_clearance_screen_hits=len(new_hits),
                              newly_encroached_items=sorted(new_hits-old_hits)))
    overlaps = [r for r in rows if r['SMD pad drill overlap']]
    refs = Counter(hit.split('.')[0] for r in overlaps for hit in r['SMD pad drill overlap'].split(';'))
    assembly_refs = {f.GetReference() for f in board.GetFootprints()
                     if not f.IsExcludedFromBOM() and not f.IsDNP()}
    assembly_overlaps = [r for r in overlaps if any(hit.split('.')[0] in assembly_refs
                         for hit in r['SMD pad drill overlap'].split(';'))]
    result = dict(source_sha256=digest, vias=len(rows), smd_drill_overlap_vias=len(overlaps),
                  populated_component_smd_overlap_vias=len(assembly_overlaps),
                  only_dnp_or_bom_excluded_pad_overlap_vias=len(overlaps)-len(assembly_overlaps),
                  overlap_pad_hits_by_reference=dict(refs.most_common()),
                  via_sizes=dict(Counter(f"{r['Diameter mm']}/{r['Drill mm']}" for r in rows)),
                  requires_drill_enlargement=len(screened),
                  proposed_vias_with_new_copper_encroachment=sum(bool(r['newly_encroached_items']) for r in screened),
                  proposed_vias_without_screened_copper_obstacle=sum(r['proposed_clearance_screen_hits']==0 for r in screened),
                  proposed_vias_with_any_screened_copper_obstacle=sum(r['proposed_clearance_screen_hits']>0 for r in screened),
                  enlargement_screen=screened)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    return result


if __name__ == '__main__':
    snapshot = json.loads((ROOT/'hardware/quotes/2026-09-11/validation.json').read_text())
    result = dict(status='READ-ONLY COST SCREEN - NOT MANUFACTURING ACCEPTANCE',
                  proposal='0.55 mm diameter / 0.30 mm drill for every via with drill below 0.30 mm; preserves 0.125 mm annular ring',
                  clearance_screen_mm=.15,
                  limitations=['Only different-net tracks, vias and pads are screened.',
                               'Same-net drill spacing, holes, board edges, zones, keepouts and netclass rules require native DRC.',
                               'Plane refill, USB/analog return paths, power resistance and thermals require revalidation.',
                               'No source CAD or manufacturing archive is changed.'])
    result['boards'] = {n: audit(n, s, snapshot['boards'][n]['source_sha256']) for n, s in BOARDS.items()}
    output = ROOT/'hardware/quotes/cost-reduction-2026-09-11/fabrication-audit.json'
    write_json(output, result)
    print(json.dumps({n: {k:v for k,v in b.items() if k != 'enlargement_screen'} for n,b in result['boards'].items()}, indent=2))
