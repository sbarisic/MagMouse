"""Independent acceptance of integrated encoder / underside-test-pad removal.
Run with KiCad Python after routing and panel export.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json, hashlib, math, subprocess
from integrated_encoder import HERE,ROOT,CLI,p,BOARDS,REMOVED
from circuit_review_rules import additions,expected_net,VALUE_CHANGES
from assembly_spacing import envelope,active
from standard_vias import intersections
from validate_circuit_fixes import geometry,measurements
from netlist import export
from review_trace_loops import review as trace_loops
from validate_routing_cleanup import check_usb_geometry
from hall_relocation import POSITIONS

def main():
    baseline=json.loads((HERE/'encoder-baseline.json').read_text())
    out=ROOT/'build/sandwich/integrated-encoder';out.mkdir(parents=True,exist_ok=True)
    report={'motor':'TSL GB1806 with integrated AS5048A','boards':{},'hardware_validated':False}
    allpins={};top=[]
    for name,path in BOARDS.items():
        b=p.LoadBoard(str(path));b.BuildConnectivity();fs={f.GetReference():f for f in b.GetFootprints()}
        old=baseline[name];new=additions(name) if name=='Lower' else {}
        assert set(fs)==(set(old['components'])-REMOVED[name])|set(new)
        comps,pins=export(path.with_suffix('.kicad_sch'),out/(name+'.xml'));allpins[name]=pins
        assert not (REMOVED[name]&set(comps))
        for ref,f in fs.items():
            pads={q.GetNumber():q.GetNetname() for q in f.Pads() if q.GetNumber()}
            assert not (ref.startswith('TP') and f.IsFlipped()),(name,ref)
            if ref.startswith('TP'):top.append(name+'.'+ref)
            if ref in new:
                value,footprint,expected=new[ref]
                assert str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())==footprint
            else:
                before=old['components'][ref]
                value=VALUE_CHANGES.get(name,{}).get(ref,before['value'])
                expected={pin:expected_net(name,ref,pin,net) for pin,net in before['pads'].items() if pin}
                if ref in POSITIONS.get(name,{}):
                    x,y,angle=POSITIONS[name][ref]
                    assert math.dist(p.ToMM(f.GetPosition()),(x,y))<.000002
                    assert f.GetOrientationDegrees()==angle
                elif ref not in ('C55','C64'):
                    assert math.dist(p.ToMM(f.GetPosition()),before['xy'])<.000002
                    assert f.GetOrientationDegrees()==before['angle']
            assert f.GetValue()==value,(name,ref,'value')
            assert pads==expected,(name,ref,pads,expected)
            schematic={pin:net for (r,pin),net in pins.items() if r==ref}
            assert {k:v for k,v in pads.items() if v}==schematic,(name,ref,'parity')
        assert json.loads(json.dumps(geometry(b)))==old['geometry'],name+' geometry'
        project=json.loads(path.with_suffix('.kicad_pro').read_text())
        assert project['board']['design_settings']==old['design_settings'],name+' DRC rules changed'
        env={r:envelope(f) for r,f in fs.items() if active(f)}
        gap=min((a.distance(c),r,q) for r,a in env.items() for q,c in env.items() if r<q)
        assert gap[0]>=1.99999,(name,gap)
        assert not intersections(b)
        assert all(t.GetDrillValue()>=p.FromMM(.3) for t in b.GetTracks() if isinstance(t,p.PCB_VIA))
        assert not [r for r in trace_loops(b) if r['net']!='GND'],name+' signal track loops'
        for kind,args in [('erc',['sch','erc','--format','json']),('drc',['pcb','drc','--schematic-parity','--format','json'])]:
            dest=out/(name+'-'+kind+'.json')
            subprocess.run([str(CLI),*args,'-o',str(dest),str(path.with_suffix('.kicad_sch') if kind=='erc' else path)],check=True,stdout=subprocess.DEVNULL)
            d=json.loads(dest.read_text())
            issues=[v for sheet in d['sheets'] for v in sheet['violations']] if kind=='erc' else d['violations']+d['unconnected_items']+d.get('schematic_parity',[])
            assert not issues,(name,kind,issues[:2])
        report['boards'][name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'removed_bottom_test_pads':sorted(REMOVED[name]),'remaining_bottom_test_pads':0,
            'minimum_component_gap_mm':gap[0],'erc':0,'drc':0,'unconnected':0,'schematic_parity':0,
            'rules_unchanged':True,'geometry_unchanged':True,'via_hole_smd_overlaps':0,
            'non_ground_planar_trace_findings':0}
        if name=='Lower':
            # The later authorized cleanup changes USB fanouts and local jogs.
            # Keep the wide pair and transition vias fixed and measure the full
            # revised trace width against actual opposite-side ground copper.
            report['usb_return']=check_usb_geometry(b)
            caps=measurements(b,[('U42','1','C55','1'),('U42','5','C64','1'),('U29','14','C105','1')])
            assert all(c['pad_center_distance_mm']<=5 and c['whole_segment_sum_mm']<=5
                       and c['vias']==0 for c in caps),caps
            report['local_decoupling']=caps
    assert sorted(top)==['Lower.TP38','Lower.TP39','Wheel.TP34','Wheel.TP35','Wheel.TP36','Wheel.TP37']
    assert not (HERE.parent/'encoder').exists() or not list((HERE.parent/'encoder').glob('*.kicad_*'))
    panel=json.loads((HERE/'panel/panel-manifest.json').read_text())
    assert panel['designs']==3 and set(panel['units'])==set(BOARDS)
    assert all(panel['units'][name]['sha256']==report['boards'][name]['sha256'] for name in BOARDS)
    assert panel['exact_translated_pads_tracks_drills_and_zone_copper']
    for a,ar,b,br in [('Lower','J101','Upper','J102'),('Lower','J103','Upper','J104'),('Lower','J8','Wheel','J9'),('Upper','J10','Wheel','J11')]:
        assert {pin:net for (ref,pin),net in allpins[a].items() if ref==ar}=={pin:net for (ref,pin),net in allpins[b].items() if ref==br}
    assert {pin:net for (ref,pin),net in allpins['Lower'].items() if ref=='J6'}=={
        '1':'ENC_5V','2':'GND','3':'ENC_SCLK_LOCAL','4':'GND','5':'ENC_MOSI_LOCAL','6':'ENC_CS_LOCAL','7':'GND','8':'ENC_MISO_LOCAL'}
    report.update(top_test_pads=sorted(top),panel_designs=3,standalone_encoder_removed=True,
        encoder_branch_budget_mA=25,encoder_supply='PWR_5V -> U33/RGB_5V -> U28/ENC_5V; U42/ENC_3V3 for U29',
        limits='CAD and datasheet review only; module supply, shutdown, signal integrity, angle timing and mechanical fit require bench validation.')
    (HERE/'encoder-review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('usb_return','local_decoupling')},indent=2))

if __name__=='__main__':main()
