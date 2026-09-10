"""Check the independent wheel PCB's netlist, outline and initial placement.

Use KiCad Python and a fresh native DRC/parity report. Airwire distances are
placement measures, not routed length or electrical acceptance.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as p


def review(board_path,netlist_path,drc_path):
    b=p.LoadBoard(str(board_path));tree=ET.parse(netlist_path)
    comps={c.get('ref'):c for c in tree.findall('./components/comp')}
    expected={(node.get('ref'),node.get('pin')):n.get('name')
              for n in tree.findall('./nets/net') for node in n.findall('node')}
    fps={f.GetReference():f for f in b.GetFootprints()}
    pads={(f.GetReference(),pad.GetNumber()):pad for f in b.GetFootprints() for pad in f.Pads() if pad.GetNumber()}
    errors=[]
    def check(ok,msg):
        if not ok:errors.append(msg)
    check(set(fps)==set(comps),'PCB/netlist reference inventory differs')
    for key,net in expected.items():
        check(key in pads and pads[key].GetNetname()==net,f'{key}: missing/wrong net {net}')
    for ref,c in comps.items():
        if ref not in fps:continue
        f=fps[ref]
        check(f.GetFPID().GetLibItemName()==c.findtext('footprint').split(':')[1],f'{ref}: footprint differs')
        check(f.GetValue()==c.findtext('value'),f'{ref}: value differs')
        check(f.GetLayer()==p.F_Cu,f'{ref}: unexpected back-side assembly')
        for item in f.GraphicalItems():
            if item.GetLayer()!=p.F_CrtYd:continue
            box=item.GetBoundingBox()
            check(box.GetLeft()>=0 and box.GetTop()>=0 and box.GetRight()<=p.FromMM(55)
                  and box.GetBottom()<=p.FromMM(60),f'{ref}: courtyard outside outline')
    box=b.GetBoardEdgesBoundingBox()
    check(abs(p.ToMM(box.GetWidth())-55)<.2 and abs(p.ToMM(box.GetHeight())-60)<.2,'Wheel outline is not 55 x 60 mm')
    polygon=p.SHAPE_POLY_SET()
    check(b.GetBoardPolygonOutlines(polygon,False),'Wheel outline is not closed')
    check(b.GetCopperLayerCount()==4,'Wheel stack is not four layers')
    check(b.IsLayerEnabled(p.In1_Cu),'In1 ground-reference layer unavailable')
    def pos(ref,pin):
        v=pads[ref,str(pin)].GetPosition();return p.ToMM(v.x),p.ToMM(v.y)
    def distance(a,c):return math.dist(pos(*a),pos(*c))
    # With J9 mouth pointing up, pad 1 lies to the right and pad 30 left.
    check(fps['J9'].GetOrientationDegrees()%360==180,'J9 rotation violates facing-header cable contract')
    check(pos('J9',1)[0]>pos('J9',30)[0],'J9 contact order contradicts cable drawing')
    metrics={}
    for phase,driver_pin,adc_pin,r,c in [('A',40,15,'R102','C59'),('B',39,16,'R103','C60'),('C',38,1,'R104','C61')]:
        approach=distance(('U21',driver_pin),(r,1))+distance((r,2),('U23',adc_pin))
        cap=distance(('U23',adc_pin),(c,1))
        check(approach<12,f'{phase}: current-sense placement span exceeds 12 mm')
        check(cap<4,f'{c}: ADC filter capacitor more than 4 mm from input')
        check(pos('U23',adc_pin)[1]<pos('U21',driver_pin)[1],'ADC input is on phase-exit side of driver')
        metrics[phase]={'driver_to_filter_to_adc_airwire_mm':approach,'adc_to_filter_cap_airwire_mm':cap}
    gate=distance(('U30',1),('R119',1))+distance(('R119',2),('Q5',1))
    check(gate<12,'Brake comparator/resistor/MOSFET placement span exceeds 12 mm')
    check(pos('J5',2)[1]>pos('U21',16)[1],'Phase connector is not beyond driver phase side')
    drc=json.loads(drc_path.read_text())
    check(not drc['violations'],'Native physical DRC has unresolved violations')
    check(not drc['schematic_parity'],'Native schematic parity has unresolved issues')
    routed=bool(list(b.GetTracks()))
    return {'status':'Routed; mechanical and electrical qualification pending' if routed and not drc['unconnected_items'] else 'Partial routing; not for fabrication',
            'board_sha256':hashlib.sha256(board_path.read_bytes()).hexdigest(),
            'netlist_sha256':hashlib.sha256(netlist_path.read_bytes()).hexdigest(),
            'footprints':len(fps),'checked_netlist_pins':len(expected),'copper_layers':b.GetCopperLayerCount(),
            'tracks_and_vias':len(list(b.GetTracks())),'zones':len(list(b.Zones())),
            'physical_drc_violations':len(drc['violations']),'schematic_parity_issues':len(drc['schematic_parity']),
            'unconnected_items':len(drc['unconnected_items']),
            'current_sense_placement':metrics,'brake_gate_airwire_via_series_resistor_mm':gate,
            'reference_plane_status':'See wheel-routing-review.json for saved copper checks' if routed else 'In1 reserved; no saved fill',
            'open_items':['Bench qualification of power, brake, ADC noise and SPI timing',
                          'Thermal, signal-integrity and enclosure review',
                          'Mounting/support, motor wires, cable mating tolerances and enclosure fit',
                          'Final silkscreen, test access, panel tooling and manufacturing exports'],
            'errors':errors}


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--board',type=Path,required=True);a.add_argument('--netlist',type=Path,required=True)
    a.add_argument('--drc',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    args=a.parse_args();result=review(args.board,args.netlist,args.drc)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    raise SystemExit(int(bool(result['errors'])))
