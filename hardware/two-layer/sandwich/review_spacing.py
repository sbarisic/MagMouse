"""Measure the spacing revision and check its fixed placement anchors."""
from pathlib import Path
import hashlib
import json
import math
import statistics
import pcbnew as p
from compact_placement import shapes, FIXED
from shapely.affinity import translate
from spaced_groups import BASELINE, TARGETS, goals

HERE=Path(__file__).resolve().parent


def main():
    partition=json.loads((HERE/'partition.json').read_text())
    report={}
    for side in ('Lower','Upper'):
        path=HERE/side.lower()/(side+'.kicad_pcb')
        board=p.LoadBoard(str(path))
        fps={f.GetReference():f for f in board.GetFootprints()}
        positions={ref:tuple(p.ToMM(f.GetPosition())) for ref,f in fps.items()}
        _,anchors=goals(side,fps,partition['component_sheets'])
        fixed=[ref for ref in fps if ref in FIXED or ref.startswith(('J','H'))
               or ref in ('U7','U8','U9','U20','U1')]
        assert all(math.dist(positions[ref],BASELINE[side][ref])<.000002 for ref in fixed)
        distances={}
        for ref,anchor in anchors.items():
            if not ref.startswith(('C','L')):continue
            old=math.dist(BASELINE[side][ref],BASELINE[side][anchor])
            new=math.dist(positions[ref],positions[anchor])
            assert new<=old+.750002,(ref,anchor,old,new)
            distances[ref]={'anchor':anchor,'before_mm':round(old,4),'after_mm':round(new,4)}
        current={ref:shapes(f)[0] for ref,f in fps.items() if not ref.startswith('TP')}
        before={ref:translate(shape,BASELINE[side][ref][0]-positions[ref][0],
                              BASELINE[side][ref][1]-positions[ref][1]) for ref,shape in current.items()}
        affected=[ref for ref in current if ref in TARGETS[side] or anchors.get(ref) in TARGETS[side]]
        def nearest(geometry):
            return [min(geometry[ref].distance(other) for r,other in geometry.items() if r!=ref) for ref in affected]
        drc=json.loads((HERE/side.lower()/(side+'-drc.json')).read_text())
        assert not drc['violations']
        report[side]={'moved_footprints':sum(math.dist(positions[ref],BASELINE[side][ref])>.001 for ref in fps),
                      'fixed_references':fixed,'fixed_placements_preserved':True,
                      'affected_footprints':len(affected),
                      'median_nearest_courtyard_gap_before_mm':round(statistics.median(nearest(before)),4),
                      'median_nearest_courtyard_gap_after_mm':round(statistics.median(nearest(current)),4),
                      'capacitor_inductor_anchor_distances':distances,
                      'placement_drc_findings':0,'unconnected_items':len(drc['unconnected_items']),
                      'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (HERE/'spacing-review.json').write_text(json.dumps(report,indent=2)+'\n')
    for side,data in report.items():
        print(side,{k:v for k,v in data.items() if k not in ('fixed_references','capacitor_inductor_anchor_distances')})


if __name__=='__main__':main()
