# SPDX-License-Identifier: GPL-3.0-or-later
"""Record routing measurements against the pre-rebuild boards in build/."""
import collections, hashlib, json, math
from pathlib import Path
import rebuild_routes as r
from review_power_ground import inspect
from validate_circuit_fixes import geometry, usb_copper
from circuit_review_rules import REMOVED_COMPONENTS, additions
from circuit_routes import shapes
from usb_return import check_usb
from hall_relocation import POSITIONS


def measure(name,path):
    b=r.p.LoadBoard(str(path));data=inspect(name,path)
    tracks=[t for t in b.GetTracks() if not isinstance(t,r.p.PCB_VIA)]
    material=r.board_interior(b,0)
    outside=[r.uid(t) for t in b.GetTracks() if any(not material.buffer(.001).covers(s) for s in shapes(t).values())]
    assert not outside,(name,outside)
    widths=collections.defaultdict(float);off_axis=0
    for t in tracks:
        w=r.p.ToMM(t.GetWidth());length=r.p.ToMM(t.GetLength());widths[str(round(w,4))]+=length
        a,z=r.p.ToMM(t.GetStart()),r.p.ToMM(t.GetEnd());dx,dy=abs(z[0]-a[0]),abs(z[1]-a[1])
        if length>.1 and min(dx,dy,abs(dx-dy))>.002:off_axis+=1
    data.update(track_length_mm=round(sum(widths.values()),2),via_count=sum(isinstance(t,r.p.PCB_VIA) for t in b.GetTracks()),
                width_length_mm={k:round(v,3) for k,v in sorted(widths.items())},non_octilinear_segments_over_0_1mm=off_axis,copper_items_outside_board=0)
    return data


def main():
    out={};dest=r.HERE/'routing-review/routing-rebuild.json'
    previous=json.loads(dest.read_text()) if dest.exists() else {}
    for name in ['Lower','Upper','Wheel']:
        old=r.WORK/name/(name+'.kicad_pcb');new=r.BOARDS[name]
        after=r.p.LoadBoard(str(new))
        def placement(b):return {f.GetReference():(tuple(r.p.ToMM(f.GetPosition())),f.GetOrientationDegrees()) for f in b.GetFootprints()}
        if old.exists():
            before=r.p.LoadBoard(str(old));baseline={'geometry':geometry(before),'placement_mm':placement(before),'usb_copper':usb_copper(before) if name=='Lower' else []};before_data=measure(name,old)
        else:baseline=previous[name]['baseline'];before_data=previous[name]['before']
        assert json.dumps(baseline['geometry'],sort_keys=True)==json.dumps(geometry(after),sort_keys=True)
        aa,zz=baseline['placement_mm'],placement(after)
        aa={k:v for k,v in aa.items() if k not in REMOVED_COMPONENTS[name]}
        assert set(aa)|set(additions(name))==set(zz)
        expected=dict(aa)
        for ref in additions(name):expected[ref]=zz[ref]
        if name=='Lower':
            moves=json.loads((r.HERE/'routing-review/lower-usb.json').read_text())['changed_placements']
            moves={ref:move for ref,move in moves.items() if ref not in REMOVED_COMPONENTS[name]}
            for ref,move in moves.items():
                assert math.dist(aa[ref][0],move['before'][0])<=.000002 and aa[ref][1]==move['before'][1],ref
                expected[ref]=move['after']
            check_usb(after)
        if name=='Lower':
            for ref in ('C55','C64'):expected[ref]=zz[ref]
        for ref,(x,y,angle) in POSITIONS.get(name,{}).items():expected[ref]=((x,y),angle)
        assert all(math.dist(expected[k][0],zz[k][0])<=.000002 and expected[k][1]==zz[k][1] for k in expected)
        out[name]={'baseline':baseline,'before':before_data,'after':measure(name,new),'placement_and_geometry_unchanged':name=='Wheel','placement_serialization_tolerance_mm':.000002}
        if name in POSITIONS:out[name]['hall_placement_changes']=POSITIONS[name]
        if name=='Lower':out[name]['placement_changes']=moves
    out['model_limits']='Native-contact resistance screen at 80 C, 35 um copper, 20 um via plating; not measured ampacity, SI, EMI or thermal acceptance.'
    dest.write_text(json.dumps(out,indent=2)+'\n')
    for n in ['Lower','Upper','Wheel']:
        print(n,[(k,out[n][k]['track_length_mm'],out[n][k]['via_count']) for k in ['before','after']])


if __name__=='__main__':main()
