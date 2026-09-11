"""Audit complete main-board connectivity, signal references and digital paths.

These are saved-copper checks, not measured impedance, timing, thermal or EMC
qualification. Run native DRC/parity and the dedicated USB/power/analog checks.
"""
import argparse
import hashlib
import heapq
import json
import math
from pathlib import Path
import sys
import pcbnew as p

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'hardware/kicad'))
from verify_high_current_layout import CopperGraph, uid

SPI3 = {'MOTOR_SPI_SCLK', 'MOTOR_SPI_MOSI', 'MOTOR_SPI_MISO', 'CS_ADC2', 'ADC2_MISO_LOCAL'}
SPI2 = {'SPI_SCLK', 'SPI_MOSI', 'SPI_MISO', 'ADC_CS', 'CS_PAW', 'CS_IMU', 'CS_DRV8316', 'CS_MA735'}
DIGITAL = SPI3 | SPI2 | {'OPT_SCLK', 'OPT_MOSI', 'OPT_MISO', 'OPT_CS_N', 'OPT_RESET_N',
                       'ENC_SCLK_LOCAL', 'ENC_MOSI_LOCAL', 'ENC_MISO_LOCAL', 'ENC_CS_LOCAL'}
PATHS = [(('U3','29'),('J8','10')), (('U3','28'),('J8','12')),
         (('J8','16'),('U25','9')), (('U25','8'),('U3','31')),
         (('U3','32'),('J8','14')), (('U3','32'),('U25','10'))]
SUPPLY_PADS = [('U3','3'), ('U10','7'), ('U10','10'), ('U25','14'), ('U32','5'), ('U32','8')]
BYPASS_PATHS = [(('C5','1'),('U3','3')), (('C6','1'),('U3','3')),
                (('C19','1'),('U10','7')), (('C20','1'),('U10','10')),
                (('C53','1'),('U25','14')), (('C72','1'),('U32','5')),
                (('C71','1'),('U32','8'))]
# Copper outlines below use 1 um polygon approximation. Keep the measured area
# in the report, but do not classify a sub-tessellation sliver as a plane split.
PRIMARY_SHADOW_AREA_TOLERANCE_MM2 = .0002


def verify(board, require_complete=True):
    tracks = list(board.GetTracks())
    entries = [(f.GetReference(),q) for f in board.GetFootprints() for q in f.Pads() if q.GetNumber()]
    objects = tracks + [q for _,q in entries]
    original = {uid(q):q.GetNetname() for q in objects}
    board.BuildConnectivity(); conn = board.GetConnectivity(); errors = []; findings = []
    if any(original[uid(q)] != q.GetNetname() for q in objects):
        errors.append('Native connectivity changed a net assignment; inspect for a short')
    remaining = conn.GetUnconnectedCount(False)
    if require_complete and remaining:
        errors.append(f'Main completion: {remaining} unrouted connections remain')
    for net in sorted({q.GetNetname() for _,q in entries} - {''}):
        nodes = [q for _,q in entries if q.GetNetname() == net]
        if len(nodes)<2: continue
        reached = {uid(q) for q in conn.GetConnectedItems(nodes[0])} | {uid(nodes[0])}
        if require_complete and any(uid(q) not in reached for q in nodes[1:]):
            errors.append(net + ': endpoint continuity failed')
    ground = p.SHAPE_POLY_SET()
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.GetLayer()==p.In1_Cu and z.GetNetname()=='GND':
            ground.BooleanAdd(z.GetFilledPolysList(p.In1_Cu))
    if ground.OutlineCount()!=1:
        errors.append('In1 must have one connected saved ground outline')
    if any(not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.In1_Cu for t in tracks):
        errors.append('A routed track occupies the In1 ground reference')
    secondary_ground = p.SHAPE_POLY_SET()
    for layer in [p.In2_Cu,p.B_Cu]:
        zones=[z for z in board.Zones() if not z.GetIsRuleArea() and z.GetLayer()==layer and z.GetNetname()=='GND']
        if not any(z.GetZoneName()=='MAIN_RETURN_'+board.GetLayerName(layer)
                   and z.GetFilledPolysList(layer).OutlineCount() for z in zones):
            errors.append(board.GetLayerName(layer)+': main return copper is missing')
        for z in zones:secondary_ground.BooleanAdd(z.GetFilledPolysList(layer))
    # A bare via attached only to In1 does not provide a return transition.
    ground_vias = [t for t in tracks if isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND'
                   and ground.Contains(t.GetPosition()) and secondary_ground.Contains(t.GetPosition())]
    metrics = {}
    for net in sorted(DIGITAL):
        copper = [t for t in tracks if t.GetNetname()==net]
        lines = [t for t in copper if not isinstance(t,p.PCB_VIA)]
        vias = [t for t in copper if isinstance(t,p.PCB_VIA)]
        shadow = p.SHAPE_POLY_SET(); primary_shadow = p.SHAPE_POLY_SET()
        for t in lines:
            poly = p.SHAPE_POLY_SET();t.TransformShapeToPolygon(poly,t.GetLayer(),0,p.FromMM(.001),p.ERROR_OUTSIDE)
            primary_shadow.BooleanAdd(poly)
            if t.GetLayer()==p.F_Cu:shadow.BooleanAdd(poly)
        shadow.BooleanSubtract(ground)
        primary_shadow.BooleanSubtract(ground)
        for v in vias + [q for _,q in entries if q.GetNetname()==net and q.IsOnLayer(p.In1_Cu)]:
            poly=p.SHAPE_POLY_SET();v.TransformShapeToPolygon(poly,p.F_Cu,p.FromMM(.4),p.FromMM(.001),p.ERROR_OUTSIDE);shadow.BooleanSubtract(poly);primary_shadow.BooleanSubtract(poly)
        missing=abs(shadow.Area())/1e12
        primary_missing=abs(primary_shadow.Area())/1e12
        distances=[min((p.ToMM((v.GetPosition()-g.GetPosition()).EuclideanNorm()) for g in ground_vias),default=math.inf) for v in vias]
        farthest=max(distances,default=0)
        reported_distance=round(farthest,3) if math.isfinite(farthest) else None
        if missing>.00001:
            findings.append({'kind':'front_reference_gap','net':net,'missing_mm2':round(missing,6)})
        if primary_missing>PRIMARY_SHADOW_AREA_TOLERANCE_MM2:
            findings.append({'kind':'primary_reference_gap','net':net,'missing_mm2':round(primary_missing,6)})
        if farthest>3:
            findings.append({'kind':'signal_transition_return','net':net,'farthest_ground_via_mm':reported_distance})
        metrics[net]={'copper_mm':round(sum(p.ToMM(t.GetLength()) for t in lines),3),'vias':len(vias),
                      'layers':sorted({board.GetLayerName(t.GetLayer()) for t in lines}),
                      'front_shadow_missing_mm2':round(missing,6), 'farthest_ground_via_mm':reported_distance}
        metrics[net]['all_layer_in1_shadow_missing_mm2']=round(primary_missing,6)
    graph=CopperGraph(board);paths=[]
    for start,end in PATHS:
        found=graph.path(uid(graph.pads[start]),uid(graph.pads[end]))
        if not found:
            if require_complete:errors.append(f'{start} -> {end}: SPI3 path missing')
            continue
        _,route=found;items=[graph.items[k] for k in route]
        length=sum(p.ToMM(t.GetLength()) for t in items if isinstance(t,p.PCB_TRACK) and not isinstance(t,p.PCB_VIA))
        via_count=sum(isinstance(t,p.PCB_VIA) for t in items)
        paths.append({'from':'.'.join(start),'to':'.'.join(end),'conductor_mm':round(length,3),'counted_vias':via_count,
                      'board_delay_screen_ns':round((length+via_count*1.6)*.008,3)})
    supply_paths=[]; bypass_paths=[]
    for source,target,output in [(('U2','6'),q,supply_paths) for q in SUPPLY_PADS] + [(a,b,bypass_paths) for a,b in BYPASS_PATHS]:
        found=graph.path(uid(graph.pads[source]),uid(graph.pads[target]))
        if not found:
            if require_complete:errors.append(f'{source} -> {target}: supply path missing')
            continue
        resistance,route=found;items=[graph.items[k] for k in route]
        length=sum(p.ToMM(t.GetLength()) for t in items if isinstance(t,p.PCB_TRACK) and not isinstance(t,p.PCB_VIA))
        output.append({'from':'.'.join(source),'to':'.'.join(target), 'conductor_mm':round(length,3),
                       'counted_vias':sum(isinstance(t,p.PCB_VIA) for t in items),
                       'screening_milliohms':round(resistance*1000,3)})
        if output is bypass_paths and length>6:
            findings.append({'kind':'bypass_supply_detour','from':'.'.join(source),'to':'.'.join(target),'conductor_mm':round(length,3)})
    stubs=[]
    for net in sorted(SPI3|SPI2):
        endpoints=[q for r,q in entries if q.GetNetname()==net and not r.startswith('TP')]
        backbone=set()
        for q in endpoints[1:]:
            found=graph.path(uid(endpoints[0]),uid(q))
            if found:backbone.update(found[1])
        for ref,q in entries:
            if not ref.startswith('TP') or q.GetNetname()!=net or not backbone:continue
            queue=[(0,uid(q))];seen=set();distance=None
            while queue:
                cost,key=heapq.heappop(queue)
                if key in seen:continue
                if key in backbone:distance=cost;break
                seen.add(key)
                for other in graph.adj[key]-seen:
                    item=graph.items[other]
                    length=0 if other in backbone else 1.6 if isinstance(item,p.PCB_VIA) else p.ToMM(item.GetLength()) if isinstance(item,p.PCB_TRACK) else 0
                    heapq.heappush(queue,(cost+length,other))
            stubs.append({'net':net,'test_point':ref,'screening_stub_mm':round(distance,3) if distance is not None else None})
            if distance is None or distance>5:
                findings.append({'kind':'test_point_stub','net':net,'test_point':ref,'screening_stub_mm':round(distance,3) if distance is not None else None})
    return {'scope':'Main connectivity, saved front reference shadows, transition return proximity and digital path/stub screening',
            'native_unconnected':remaining,'digital_nets':metrics,'spi3_paths':paths,'test_point_stubs':stubs,
            'logic_supply_paths':supply_paths,'bypass_supply_paths':bypass_paths,
            'primary_shadow_area_tolerance_mm2':PRIMARY_SHADOW_AREA_TOLERANCE_MM2,
            'review_findings':findings,'errors':errors,
            'limits':['Delay screening assumes 8 ps/mm including full 1.6 mm barrels; excludes devices, connectors, cable and firmware.',
                      'Supply resistance uses the shared 80 C trace/barrel model; excludes pads, contacts, component and ground impedance. It is not a PDN transient simulation.',
                      'All-layer In1 shadows and ground vias joined to secondary return copper are geometric screens. Inner/back traces have a more distant primary reference; secondary pours contain signal crossings. These checks do not establish impedance or EMI performance.',
                      'Cable timing, ADC noise, USB compliance and thermal response require hardware qualification.',
                      'Mechanical interfaces are provisional; panelization remains on hold.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--allow-unrouted',action='store_true')
    parser.add_argument('--require-reviewed',action='store_true',help='Fail if a reference, transition, bypass or probe-stub screening finding remains')
    args=parser.parse_args();result=verify(p.LoadBoard(str(args.board)),not args.allow_unrouted)
    result['board_sha256']=hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    raise SystemExit(bool(result['errors']) or args.require_reviewed and bool(result['review_findings']))
