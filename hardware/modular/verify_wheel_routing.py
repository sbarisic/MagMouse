"""Check saved wheel power/analog copper with KiCad Python.

These are geometric regression checks, not measured noise, ampacity, thermal,
regeneration or control-loop acceptance. Run native DRC/parity separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pcbnew as p

SENSE={f'WHEEL_SO{x}' for x in 'ABC'}|{f'WHEEL_I_{x}' for x in 'ABC'}
PHASE={f'WHEEL_PHASE_{x}' for x in 'ABC'}
BRAKE={'BRAKE_REF','BRAKE_SENSE','BRAKE_DIV_TOP','BRAKE_FB_1','BRAKE_FB_2','BRAKE_OUT','BRAKE_GATE','BRAKE_DRAIN'}
LOCAL={'WHEEL_CPL','WHEEL_CPH','WHEEL_CP','WHEEL_BUCK_SW','WHEEL_BUCK_OUT','DRV_AVDD','ADC2_DECAP','ACT_5V'}
GROUND_REFS={'U21','U23','U30','U31','Q5','J11','C90','D6','C41','C42','C43','C44','C45','C48','C49','C50','C56','C57','C58','C59','C60','C61','C65','C66','C67','C68','C69','R114','R120'}


def uid(item):return item.m_Uuid.AsString()


def verify(board):
    original={uid(i):i.GetNetname() for i in list(board.GetTracks())+[q for f in board.GetFootprints() for q in f.Pads()]}
    board.BuildConnectivity();conn=board.GetConnectivity();errors=[];metrics={}
    for i in list(board.GetTracks())+[q for f in board.GetFootprints() for q in f.Pads()]:
        if original[uid(i)]!=i.GetNetname():errors.append('Connectivity changed a copper/pad net assignment; inspect for a short')
    pads=[(f.GetReference(),q) for f in board.GetFootprints() for q in f.Pads() if q.GetNumber()]
    tracks=list(board.GetTracks());ground=p.SHAPE_POLY_SET();ground_ids=set()
    remaining=conn.GetUnconnectedCount(False)
    if remaining:errors.append(f'Wheel completion: {remaining} native unconnected items remain')
    complete_nets=0
    for net in sorted({q.GetNetname() for _,q in pads}):
        nodes=[q for _,q in pads if q.GetNetname()==net]
        if not net or len(nodes)<2:continue
        complete_nets+=1
        reached={uid(i) for i in conn.GetConnectedItems(nodes[0])}|{uid(nodes[0])}
        if any(uid(q) not in reached for q in nodes[1:]):errors.append(net+': whole-board endpoint continuity failed')
    for z in board.Zones():
        if z.GetLayer()==p.In1_Cu and z.GetNetname()=='GND' and not z.GetIsRuleArea():
            ground.BooleanAdd(z.GetFilledPolysList(p.In1_Cu));ground_ids.add(uid(z))
    if ground.OutlineCount()!=1:errors.append('In1 must have one connected saved ground outline')
    if any(t.GetLayer()==p.In1_Cu for t in tracks if not isinstance(t,p.PCB_VIA)):
        errors.append('A track occupies the In1 ground reference')
    for net in sorted(SENSE|PHASE|BRAKE|LOCAL):
        nodes=[(r,q) for r,q in pads if q.GetNetname()==net]
        if len(nodes)<2:errors.append(net+': missing endpoints');continue
        reached={uid(i) for i in conn.GetConnectedItems(nodes[0][1])}|{uid(nodes[0][1])}
        for r,q in nodes[1:]:
            if uid(q) not in reached:errors.append(f'{net}: disconnected {r}.{q.GetNumber()}')
        copper=[t for t in tracks if t.GetNetname()==net]
        vias=[t for t in copper if isinstance(t,p.PCB_VIA)]
        lines=[t for t in copper if not isinstance(t,p.PCB_VIA)]
        length=sum(p.ToMM(t.GetLength()) for t in lines)
        if net in SENSE|PHASE|{'ADC2_DECAP','BRAKE_GATE','BRAKE_OUT','BRAKE_REF','BRAKE_SENSE'}:
            if vias or any(t.GetLayer()!=p.F_Cu for t in lines):errors.append(net+': must stay front-only without signal vias')
        limit=8 if net in SENSE else 30 if net in PHASE else 6 if net=='BRAKE_GATE' else 16 if net=='BRAKE_OUT' else 20 if net=='BRAKE_REF' else 14 if net=='BRAKE_SENSE' else None
        if limit and length>limit:errors.append(f'{net}: {length:.3f} mm copper exceeds {limit} mm regression limit')
        if net in PHASE:
            if any(p.ToMM(t.GetWidth())<.249 for t in lines):errors.append(net+': phase launch below 0.25 mm')
            if any(p.ToMM(t.GetWidth())<.849 and p.ToMM(t.GetLength())>1.3 for t in lines):errors.append(net+': narrow phase launch longer than 1.3 mm')
            if any(min(p.ToMM(t.GetStart().y),p.ToMM(t.GetEnd().y))<31.39 for t in lines):errors.append(net+': phase copper escaped toward the sensing island')
        missing=None
        if net in SENSE|{'ADC2_DECAP','BRAKE_REF','BRAKE_SENSE','DRV_AVDD'}:
            shadow=p.SHAPE_POLY_SET()
            for t in lines:
                if t.GetLayer()!=p.F_Cu:continue
                poly=p.SHAPE_POLY_SET();t.TransformShapeToPolygon(poly,p.F_Cu,0,p.FromMM(.001),p.ERROR_OUTSIDE);shadow.BooleanAdd(poly)
            shadow.BooleanSubtract(ground)
            # Only this signal's own through-via transitions are exempted.
            for v in vias:
                poly=p.SHAPE_POLY_SET();v.TransformShapeToPolygon(poly,p.F_Cu,p.FromMM(.4),p.FromMM(.001),p.ERROR_OUTSIDE);shadow.BooleanSubtract(poly)
            missing=abs(shadow.Area())/1e12
            if missing>.00001:errors.append(f'{net}: {missing:.6f} mm2 lacks In1 ground shadow')
        metrics[net]={'pads':len(nodes),'copper_mm':round(length,3),'vias':len(vias),'layers':sorted({board.GetLayerName(t.GetLayer()) for t in lines}),'missing_front_ground_shadow_mm2':round(missing,6) if missing is not None else None}
    checked_ground=0
    for ref,q in pads:
        if ref in GROUND_REFS and q.GetNetname()=='GND':
            checked_ground+=1
            if not {uid(i) for i in conn.GetConnectedItems(q)}&ground_ids:errors.append(f'{ref}.{q.GetNumber()}: ground does not reach In1')
    # Geometric projection is deliberately conservative: even opposite-layer
    # phase copper must remain 0.5 mm away from every current-sense conductor.
    separation={}
    aggressors=[t for t in tracks if t.GetNetname() in PHASE|{'BRAKE_DRAIN','WHEEL_BUCK_SW','WHEEL_CPH','WHEEL_CPL'}]
    for net in sorted(SENSE):
        closest=1e9;against=None
        for a in [t for t in tracks if t.GetNetname()==net]:
            for c in aggressors:
                aw=a.GetWidth(p.F_Cu) if isinstance(a,p.PCB_VIA) else a.GetWidth()
                cw=c.GetWidth(p.F_Cu) if isinstance(c,p.PCB_VIA) else c.GetWidth()
                gap=p.ToMM(p.SEG(a.GetStart(),a.GetEnd()).Distance(p.SEG(c.GetStart(),c.GetEnd())))-(p.ToMM(aw)+p.ToMM(cw))/2
                if gap<closest:closest=gap;against=c.GetNetname()
        separation[net]={'minimum_projected_gap_mm':round(closest,3),'aggressor':against}
        if closest<.5:errors.append(f'{net}: switching copper projection within 0.5 mm ({against})')
    thermal=[t for t in tracks if isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND' and 26.7<=p.ToMM(t.GetPosition().x)<=28.3 and 27.2<=p.ToMM(t.GetPosition().y)<=28.8]
    if len(thermal)<9:errors.append('DRV8316 thermal pad has fewer than nine ground vias')
    digital={}
    for net in ['MOTOR_SPI_SCLK','MOTOR_SPI_MOSI','CS_ADC2','ADC2_SCLK_LOCAL','ADC2_MOSI_LOCAL','ADC2_CS_LOCAL','ADC2_MISO_LOCAL','SPI_SCLK','SPI_MOSI','CS_DRV8316','DRV_SCLK_LOCAL','DRV_MOSI_LOCAL','DRV_CS_LOCAL','DRV_MISO_LOCAL']:
        copper=[t for t in tracks if t.GetNetname()==net]
        digital[net]={'copper_mm':round(sum(p.ToMM(t.GetLength()) for t in copper if not isinstance(t,p.PCB_VIA)),3),
                      'vias':sum(isinstance(t,p.PCB_VIA) for t in copper),
                      'layers':sorted({board.GetLayerName(t.GetLayer()) for t in copper if not isinstance(t,p.PCB_VIA)})}
    return {'scope':'Wheel whole-board continuity plus power, brake, phases, ADC2 and saved analog return geometry',
            'nets':metrics,'current_sense_separation':separation,'checked_ground_pads':checked_ground,
            'checked_connected_nets':complete_nets,'spi_copper_inventory':digital,
            'in1_ground_outlines':ground.OutlineCount(),'drv8316_thermal_vias':len(thermal),
            'tracks_and_vias':len(tracks),'native_unconnected':conn.GetUnconnectedCount(False),
            'limits':['SPI length/via inventory is not sampling-time or signal-integrity acceptance','No measured ADC noise, thermal, ampacity or brake reaction acceptance','Filled and capped vias required at exposed pads and signal/ground vias in component pads; smallest signal via 0.45/0.20 mm','Mechanical interfaces remain provisional; panelization is on hold'],
            'errors':errors}


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--board',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    args=a.parse_args();result=verify(p.LoadBoard(str(args.board)))
    result['board_sha256']=hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    raise SystemExit(bool(result['errors']))
