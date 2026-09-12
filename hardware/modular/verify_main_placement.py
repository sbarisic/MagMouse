"""Verify the split main PCB inventory, outline and placement reservations.

Use KiCad Python and a fresh native DRC/parity report. Mechanical fit and
electrical routing are separate acceptance steps.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as p


def review(board_path,netlist_path,drc_path):
    board=p.LoadBoard(str(board_path));tree=ET.parse(netlist_path);errors=[]
    expected={(n.get('ref'),n.get('pin')):net.get('name') for net in tree.findall('./nets/net') for n in net.findall('node')}
    components={c.get('ref'):c for c in tree.findall('./components/comp')}
    fps={f.GetReference():f for f in board.GetFootprints()}
    pads={(r,q.GetNumber()):q for r,f in fps.items() for q in f.Pads() if q.GetNumber()}
    def check(ok,msg):
        if not ok:errors.append(msg)
    check(set(fps)==set(components),'Reference inventory differs from split main schematic')
    for key,net in expected.items():check(key in pads and pads[key].GetNetname()==net,f'{key}: wrong or missing net {net}')
    outline=p.SHAPE_POLY_SET();check(board.GetBoardPolygonOutlines(outline,False),'Main outline is not closed')
    edges=board.GetBoardEdgesBoundingBox()
    check(abs(p.ToMM(edges.GetWidth())-80)<.2 and abs(p.ToMM(edges.GetHeight())-125)<.2,'Main outline must be 125 x 80 mm')
    front=[]
    for d in board.GetDrawings():
        if d.GetLayer()==p.Edge_Cuts:
            for q in [d.GetStart(),d.GetEnd()]:
                if abs(p.ToMM(q.y))<.001:front.append(p.ToMM(q.x))
    check(front and abs(max(front)-min(front)-44)<.001,'Front edge must be 44 mm wide')
    check(board.GetCopperLayerCount()==4,'Main stack must have four copper layers')
    checked_courtyards=0
    for ref,c in components.items():
        if ref not in fps:continue
        f=fps[ref]
        check(f.GetValue()==c.findtext('value'),ref+': value differs from schematic')
        check(f.GetFPID().GetLibItemName()==c.findtext('footprint').split(':')[1],ref+': footprint differs from schematic')
        check(ref.startswith('TP') or f.GetLayer()==p.F_Cu,ref+': assembly part is not on front')
        # The USB shell may overhang the front by up to 0.5 mm; its copper pads
        # remain subject to native copper-edge DRC. Other courtyards stay inside.
        for item in f.GraphicalItems():
            if item.GetLayer() not in [p.F_CrtYd,p.B_CrtYd]:continue
            if ref=='U3':continue  # Its courtyard includes the antenna's 15 mm free-space region.
            a,c=item.GetStart(),item.GetEnd()
            steps=max(1,math.ceil(math.hypot(a.x-c.x,a.y-c.y)/p.FromMM(.25)))
            for i in range(steps+1):
                q=p.VECTOR2I(round(a.x+(c.x-a.x)*i/steps),round(a.y+(c.y-a.y)*i/steps))
                if ref=='J1' and -p.FromMM(.5)<=q.y<=0:continue
                if not outline.Contains(q):errors.append(ref+': courtyard outside shaped outline');break
        checked_courtyards+=1
        if ref=='U3':
            # The RF keepout may extend off-board, but the actual module body
            # must fit. Its F.Fab shapes describe that body independently.
            for item in f.GraphicalItems():
                if item.GetLayer()!=p.F_Fab or not isinstance(item,p.PCB_SHAPE):continue
                box=item.GetBoundingBox()
                for x,y in [(box.GetLeft(),box.GetTop()),(box.GetRight(),box.GetTop()),(box.GetRight(),box.GetBottom()),(box.GetLeft(),box.GetBottom())]:
                    check(outline.Contains(p.VECTOR2I(x,y)),'U3: physical module body outside shaped outline')
    def position(ref):
        f=fps[ref];q=f.GetPosition();return [round(p.ToMM(q.x),5),round(p.ToMM(q.y),5),f.GetOrientationDegrees()]
    check(position('J1')==[40,4,180],'USB datum changed')
    check(position('U35')==[40.5,72.5,-90],'Optical datum changed')
    check(position('J8')==[73.5,63.5,-90],'Main solder-array position/orientation changed; review wire access')
    check(position('J10')==[71,42,180],'Main power-wire position changed; review cable clearance')
    hall_spans={ref:round(math.dist(position(ref)[:2],position('U10')[:2]),3) for ref in ['U7','U8','U9']}
    check(max(hall_spans.values())<40,'ADC1 is more than 40 mm from a provisional Hall sensor')
    names={z.GetZoneName() for z in board.Zones() if z.GetIsRuleArea()}
    for name in ['PMW3360 APERTURE RESERVE - SAMPLE FIT PENDING','WHEEL MECHANICS PROVISIONAL','J8 SOLDERED WIRE ACCESS - CLAMP ON FIXTURE']:
        check(name in names,'Missing mechanical reservation: '+name)
    drc=json.loads(drc_path.read_text())
    check(not drc['violations'],'Physical DRC has unresolved violations')
    check(not drc['schematic_parity'],'Schematic parity has unresolved issues')
    board.BuildConnectivity()
    return {'status':'Main placement/routing snapshot; mechanical fit pending; panelization on hold',
            'board_sha256':hashlib.sha256(board_path.read_bytes()).hexdigest(),
            'netlist_sha256':hashlib.sha256(netlist_path.read_bytes()).hexdigest(),
            'footprints':len(fps),'checked_netlist_pins':len(expected),'checked_courtyards':checked_courtyards,
            'back_test_points':sum(f.GetLayer()==p.B_Cu for f in fps.values()),
            'antenna_clearance':'U3 extended RF courtyard may overhang the PCB; module body checked inside; enclosure RF clearance remains open',
            'native_unconnected':board.GetConnectivity().GetUnconnectedCount(False),
            'drc_unconnected_entries':len(drc['unconnected_items']),
            'physical_drc_violations':len(drc['violations']),'schematic_parity_issues':len(drc['schematic_parity']),
            'interface_positions_mm_degrees':{r:position(r) for r in ['J1','J2','J3','J4','J6','J8','J10','U35']},
            'hall_to_adc1_center_span_mm':hall_spans,
            'errors':errors}


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__)
    for name in ['board','netlist','drc','output']:a.add_argument('--'+name,type=Path,required=True)
    args=a.parse_args();result=review(args.board,args.netlist,args.drc)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    raise SystemExit(bool(result['errors']))
