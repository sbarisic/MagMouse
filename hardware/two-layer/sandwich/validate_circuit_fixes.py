# SPDX-License-Identifier: GPL-3.0-or-later
"""Independent circuit/net/geometry checks and bounded behavioral screening.

Run with KiCad Python. Behavioral checks are not transistor-level simulation,
firmware execution, compliance evidence or measured hardware acceptance.
"""
import itertools
import hashlib
import json
import math
import sys

from circuit_fixes import BOARDS, WORK, EVIDENCE, export, sha, p
from circuit_review_rules import VALUE_CHANGES, PIN_CHANGES, NEW_COMPONENTS
from assembly_spacing import envelope, active
from standard_vias import intersections
from copper_graph import CopperGraph, uid
from usb_return import check_usb
from export_quote import polygons
from shapely.ops import unary_union

PAIRS = {
    'Lower': [('U2','2','C1','1'),('U35','5','C86','1')],
    'Wheel': [('U21','6','C47','2'),('U21','7','C47','1'),
              ('U21','25','C48','1'),('U23','8','C58','1')],
}


def geometry(board):
    outline=p.SHAPE_POLY_SET();assert board.GetBoardPolygonOutlines(outline,False)
    keepouts=[]
    for z in list(board.Zones())+[z for f in board.GetFootprints() for z in f.Zones()]:
        if z.GetIsRuleArea():
            keepouts.append((z.GetZoneName(),str(z.GetLayerSet().FmtHex()),
                unary_union(polygons(z.Outline())).wkt,z.GetDoNotAllowTracks(),
                z.GetDoNotAllowVias(),z.GetDoNotAllowZoneFills()))
    return {'material_wkt':unary_union(polygons(outline)).wkt,
            'rule_areas':sorted(keepouts),'thickness_iu':board.GetDesignSettings().GetBoardThickness()}


def usb_copper(board):
    return sorted((t.GetNetname(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y,
                   t.GetLayer(),t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth(),
                   t.GetDrillValue() if isinstance(t,p.PCB_VIA) else 0)
                  for t in board.GetTracks() if t.GetNetname() in ('USB_DM','USB_DP'))


def encoder_signal_copper_digest(board):
    """Freeze Encoder signal routing while permitting the reviewed ground setback."""
    items = sorted((t.GetNetname(), t.GetStart().x, t.GetStart().y,
                    t.GetEnd().x, t.GetEnd().y, t.GetLayer(),
                    t.GetWidth(p.F_Cu) if isinstance(t, p.PCB_VIA) else t.GetWidth(),
                    t.GetDrillValue() if isinstance(t, p.PCB_VIA) else 0)
                   for t in board.GetTracks() if t.GetNetname() != 'GND')
    digest = hashlib.sha256(json.dumps(items).encode()).hexdigest()
    # Measured before and after the authorized 0.5 mm edge-clearance revision.
    assert digest == 'de035c1b5d7cd708c01971b3326cd20525d6d834d2b87c43800bc7d3523220a0'
    return digest


def measurements(board, pairs):
    graph= CopperGraph(board)
    resistance_cost=dict(graph.cost)
    for key,item in graph.items.items():
        graph.cost[key]=p.ToMM(item.GetLength()) if isinstance(item,p.PCB_TRACK) and not isinstance(item,p.PCB_VIA) else 0
    result=[]
    for r,pin,c,cp in pairs:
        a,b=graph.pads[r,pin],graph.pads[c,cp]
        route=graph.path(uid(a),uid(b))
        assert route is not None,(r,pin,c,cp,'no track/pad path')
        result.append({'connection':f'{r}.{pin} to {c}.{cp}',
            'pad_center_distance_mm':math.dist(p.ToMM(a.GetPosition()),p.ToMM(b.GetPosition())),
            'whole_segment_sum_mm':route[0],
            'vias':sum(isinstance(graph.items[k],p.PCB_VIA) for k in route[1]),
            'layers':sorted({graph.items[k].GetLayerName() for k in route[1] if isinstance(graph.items[k],p.PCB_TRACK) and not isinstance(graph.items[k],p.PCB_VIA)}),
            'contact_graph_resistance_mohm':1000*sum(resistance_cost[k] for k in route[1]),
            'route_objects':[{'start_mm':list(p.ToMM(graph.items[k].GetStart())),
                              'end_mm':list(p.ToMM(graph.items[k].GetEnd())),
                              'layer':graph.items[k].GetLayerName(),
                              'width_mm':p.ToMM(graph.items[k].GetWidth(p.F_Cu)) if isinstance(graph.items[k],p.PCB_VIA) else p.ToMM(graph.items[k].GetWidth())}
                             for k in route[1] if isinstance(graph.items[k],p.PCB_TRACK)],
            'length_model':'Sum of selected contact-graph objects; excludes travel within pads and overlapping copper. Not an exact centreline length.'})
    return result


def corners():
    # Independent errors, 25 C initial tolerance, full -40..125 C component range.
    # Extra long-term resistor drift is a qualification item, not silently zeroed.
    rows=[]
    for temp in (-40,25,85,125):
        e=.001+25e-6*abs(temp-25)
        fall=[];rise=[]
        for top,bottom,threshold,leak,hys in itertools.product((-1,1),(-1,1),(-.02,.02),(-25e-9,25e-9),(0,.03)):
            rt=105000*(1+top*e);rb=10000*(1+bottom*e)
            falling=.405*(1+threshold)*(1+rt/rb)+leak*rt
            # Conservative hysteresis maximum scaled by the high reference corner.
            rising=falling+.405*(1+threshold)*hys*(1+rt/rb)
            fall.append(falling);rise.append(rising)
        rows.append({'temperature_C':temp,'fall_min_V':min(fall),'fall_max_V':max(fall),
                     'release_min_V':min(rise),'release_max_V':max(rise)})
    assert min(r['fall_min_V'] for r in rows)>4.5
    assert max(r['release_max_V'] for r in rows)<5.0
    uv=[v*(1+30000*(1+t*.01)/(11000*(1+b*.01)))+leak*30000*(1+t*.01)
        for v,t,b,leak in itertools.product((1.183,1.223),(-1,1),(-1,1),(-.1e-6,.1e-6))]
    return {'supervisor_nominal_falling_V':.405*11.5,'supervisor_corners':rows,
        'supervisor_delay_ms':[12,20,28], 'sense_filter_tau_us':(105000*10000/115000)*1e-9*1e6,
        'efuse_nominal_rising_V':1.2*(1+30/11),'efuse_rising_range_excluding_D3_V':[min(uv),max(uv)],
        'D3_25C_max_reverse_leakage_uA':2,
        'D3_25C_max_startup_threshold_reduction_V':2e-6*30300,
        'D3_limit':'Reverse leakage injects current into EN and lowers its threshold. The 2 uA limit is specified at 25 C; no full-temperature maximum is assumed. Local drive qualification is independent.',
        'efuse_nominal_falling_V':1.09*(1+30/11)}


def behavior():
    # Check all steady interlock combinations, independent of the implementation script.
    combinations=0
    for source,request,sensors,reset_ok,heartbeat,run,vm_ok in itertools.product((False,True),repeat=7):
        arm=source and request and sensors and reset_ok
        act=arm and heartbeat
        wheel=(act and run) and vm_ok
        assert wheel==all((source,request,sensors,reset_ok,heartbeat,run,vm_ok))
        combinations+=1
    # Time-domain functional abstraction with RC sense filtering and explicit
    # supervisor propagation-delay sweeps. No claim of a vendor transistor model.
    dt=10e-6;tau=105000*10000/115000*1e-9
    scenarios={
        'startup':lambda t:(min(5.05,t/.025*5.05),True,True),
        'slow_droop':lambda t:(5.05 if t<.05 else max(4.2,5.05-(t-.05)*50),True,True),
        'abrupt_droop_recovery':lambda t:(4.0 if .05<=t<.075 else 5.05,True,True),
        'repeated_crossings':lambda t:((4.5 if int((t-.05)/.002)%2==0 else 4.85) if .05<=t<.09 else 5.05,True,True),
        'reset':lambda t:(5.05,not (.05<=t<.075),True),
        'missing_heartbeat':lambda t:(5.05,t<.06,True),
        'run_request_removed':lambda t:(5.05,True,t<.05),
        'recovery_without_heartbeat':lambda t:(4.0 if .05<=t<.075 else 5.05,t<.06,True),
        'recovery_without_run':lambda t:(4.0 if .05<=t<.075 else 5.05,True,t<.055),
        'startup_without_permission':lambda t:(min(5.05,t/.025*5.05),False,True),
    }
    results=[]
    for name,func in scenarios.items():
        for delay,propagation in itertools.product((.012,.020,.028),(20e-6,100e-6)):
            sensed=0;good=False;high_time=0;low_time=0;edges=[];last=False
            for step in range(12000):
                t=step*dt;vm,act,run=func(t)
                sensed+=(vm-sensed)*(1-math.exp(-dt/tau))
                if not act:good=False;high_time=0;low_time=0
                elif sensed<4.6575:
                    low_time+=dt;high_time=0
                    if low_time>=propagation:good=False
                else:
                    low_time=0
                    if sensed>4.6575*(1+.015):high_time+=dt
                    else:high_time=0
                    if not good and high_time>=delay:good=True
                enabled=act and run and good
                assert not enabled or (act and run)
                if enabled!=last:edges.append({'time_ms':round(t*1000,3),'enabled':enabled});last=enabled
            if name=='startup_without_permission':assert not edges and not last,name
            else:assert edges and edges[0]['enabled'],name
            if name in ('slow_droop','missing_heartbeat','run_request_removed'):assert not last,name
            if name in ('recovery_without_heartbeat','recovery_without_run'):assert not last,name
            if name in ('abrupt_droop_recovery','reset','repeated_crossings'):
                assert last and sum(not e['enabled'] for e in edges)>=1,name
                assert sum(e['enabled'] for e in edges)==2,(name,'chattering/recovery')
            results.append({'scenario':name,'release_delay_ms':delay*1000,
                'assumed_assertion_delay_us':propagation*1e6,'edges':edges})
    # Power-off buffer contract and independent chip selects: not firmware execution.
    bus_cases=0
    for optic_power,opt_cs,imu_cs,adc_cs in itertools.product((False,True),repeat=4):
        optical_drives=optic_power and not opt_cs
        if not optic_power:assert not optical_drives
        # CS signals are independent active-low controls, not a decoder.
        # Multiple selects are deliberately classified as a forbidden software
        # state; powered-off optical isolation must still hold in that state.
        imu_drives=not imu_cs;adc_drives=not adc_cs
        selected=sum((not opt_cs,imu_drives,adc_drives))
        if selected<=1:assert sum((optical_drives,imu_drives,adc_drives))<=1
        bus_cases+=1
    return {'interlock_combinations':combinations,'buffer_contract_cases':bus_cases,
        'heartbeat_model':'Permission expires at 60 ms, representing a last edge at 50 ms plus an assumed 10 ms monostable timeout. Actual timeout corners require bench measurement.',
        'transient_cases':results,'model_limit':'Functional abstraction. Delays and board voltages require bench confirmation; no firmware or full IC simulation.'}


def main():
    baseline=json.loads((EVIDENCE/'baseline.json').read_text())
    prior=json.loads((EVIDENCE/'before-layout.json').read_text())
    report={'boards':{},'capacitors':{},'corners':corners(),'behavior':behavior()}
    allpins={}
    for name,path in BOARDS.items():
        comps,pins=export(name);allpins[name]=pins
        b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()}
        assert json.loads(json.dumps(geometry(b)))==prior[name]['geometry'],(name,'outline, aperture or keepout changed')
        if name=='Lower':
            report['lower_usb']=check_usb(b)
        old=baseline[name]['components'];new=NEW_COMPONENTS if name=='Wheel' else {}
        assert set(fs)==set(old)|set(new)
        for ref,f in fs.items():
            actual={q.GetNumber():q.GetNetname() for q in f.Pads() if q.GetNumber()}
            schematic={pin:net for (r,pin),net in pins.items() if r==ref}
            # BAT54's unused physical land 2 has no symbol terminal. Preserve
            # only such explicitly empty baseline lands; never omit a live net.
            empty_lands={pin:'' for pin,net in old.get(ref,{}).get('pads',[]) if pin and not net}
            assert actual=={**empty_lands,**schematic},(name,ref,actual,schematic)
            fp=str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())
            if ref in new:
                val,expected_fp,expected=new[ref]
                assert f.GetValue()==val and fp==expected_fp and actual==expected,ref
            else:
                assert f.GetValue()==VALUE_CHANGES[name].get(ref,old[ref]['value']),ref
                assert fp==old[ref]['footprint'],ref
                expected={pin:PIN_CHANGES.get(name,{}).get((ref,pin),net) for pin,net in old[ref]['pads'] if pin}
                assert actual==expected,(name,ref)
            if ref.startswith(('J','H')) or ref=='U35':
                assert list(p.ToMM(f.GetPosition()))==old[ref]['xy'],ref
                assert f.GetOrientationDegrees()==old[ref]['angle'],ref
        env=[(r,envelope(f)) for r,f in fs.items() if active(f)]
        gap=min((a.distance(c),r,s) for r,a in env for s,c in env if r<s)
        assert gap[0]>=1.99999,(name,gap)
        assert b.GetCopperLayerCount()==2
        assert not intersections(b),name
        assert all(t.GetDrillValue()==p.FromMM(.3) for t in b.GetTracks() if isinstance(t,p.PCB_VIA))
        if name=='Encoder':
            encoder_signal_copper_digest(b)
            for ref, f in fs.items():
                assert list(p.ToMM(f.GetPosition())) == old[ref]['xy']
                assert f.GetOrientationDegrees() == old[ref]['angle']
        if name in PAIRS:
            after=measurements(b,PAIRS[name])
            before=prior[name]['capacitors']
            assert all(q['pad_center_distance_mm']<=5 for q in after)
            if name=='Wheel':assert all(q['vias']==0 for q in after[:2])
            report['capacitors'][name]={'before':before,'after':after}
        report['boards'][name]={'sha256':sha(path),'checked_pins':len(pins),'minimum_component_gap_mm':gap[0],
            'via_in_pad':0,'copper_layers':2,'geometry_and_keepouts_unchanged':True,
            'encoder_unchanged':name=='Encoder' and sha(path)==baseline[name]['sha256'],
            'encoder_signal_routing_unchanged':name=='Encoder'}
    harness=[]
    for a,ar,b,br in [('Lower','J101','Upper','J102'),('Lower','J103','Upper','J104'),
                     ('Lower','J8','Wheel','J9'),('Upper','J10','Wheel','J11'),('Lower','J6','Encoder','J7')]:
        ap={pin:net for (ref,pin),net in allpins[a].items() if ref==ar}
        bp={pin:net for (ref,pin),net in allpins[b].items() if ref==br}
        assert ap==bp
        harness.append({'ends':[a+'.'+ar,b+'.'+br],'pins':len(ap),'match':True})
    report['harness']=harness
    (EVIDENCE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('behavior',)},indent=2))


if __name__=='__main__':main()
