"""Build unrouted sandwich placement studies and an exact proposed wire map.

Run with KiCad 10 Python. Reads Main's current schematic/netlist and original
compact placement; writes only this study directory and ignored build/sandwich.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import collections
import hashlib
import html
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import pcbnew as p

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(BASE))
from prepare import signature
from compact_placement import place, ANTENNA, ANTENNA_BODY, ANTENNA_CLEARANCE_MM
from wheel_interface import library as wheel_library, replace_connector, connector_signature
from passive_buttons import REMOVED, expected_inventory, update_pads

UPPER_SHEETS = {'03_Buttons', '04_Sensing', '05_Protected_Power',
                '06_Actuator_Interlock', '07_Power_Monitor', '08_Actuator_Rail'}
OVERRIDES = {'D1': 'Lower', 'TP1': 'Lower', 'TP10': 'Lower', 'J10': 'Upper'}
SIGNALS = [
    ('SPI_SCLK', 'Lower to Upper'), ('SPI_MOSI', 'Lower to Upper'),
    ('SPI_MISO', 'Upper to Lower; shared bus'), ('ADC_CS', 'Lower to Upper'),
    ('ACT_REQ', 'Lower to Upper'), ('ACT_HEARTBEAT', 'Lower to Upper'),
    ('SENS_REQ', 'Lower to Upper'), ('CC_OUT1', 'Lower to Upper'),
    ('CC_OUT2', 'Lower to Upper'), ('VBUS_PRESENT_N', 'Upper to Lower'),
    ('HALL_EN', 'Upper to Lower'), ('ACT_DRIVE_EN', 'Upper to Lower / Wheel'),
    ('MCU_EN', 'Shared reset: Lower pull-up; Upper fault sinks'),
]
RAILS = [('VBUS_USB', 'Lower to Upper'), ('PWR_5V', 'Upper to Lower'),
         ('+3V3', 'Lower to Upper')]
SIGNAL_PINS = [('GND', 'Shared signal return')] + SIGNALS
POWER_PINS = [('GND', 'Shared power return')] + RAILS + [('GND', 'Shared power return')]
MOUNTS = ((18, 6), (52, 6), (7, 76), (63, 76))


def wire_position(index, power=False):
    return (25+5.08*index, 11) if power else (6+2.54*(index%2), 42+2.54*(index//2))


def resize_edge(edge):
    for endpoint in ('Start','End'):
        x,y=p.ToMM(getattr(edge,'Get'+endpoint)())
        getattr(edge,'Set'+endpoint)(xy(x*.875,y*.8))


def edge_signature(board):
    return sorted((int(d.GetShape()), d.GetStart().x, d.GetStart().y,
                   d.GetEnd().x, d.GetEnd().y, d.GetWidth())
                  for d in board.GetDrawings() if d.GetLayer()==p.Edge_Cuts)


def outline_points(board):
    edges = {tuple(p.ToMM(d.GetStart())): tuple(p.ToMM(d.GetEnd()))
             for d in board.GetDrawings() if d.GetLayer()==p.Edge_Cuts}
    start = min(edges)
    points, point = [], start
    while point not in points:
        points.append(point)
        point = edges[point]
    assert point==start and len(points)==len(edges), 'Outline must be a single closed loop'
    return points


def xy(x, y):
    return p.VECTOR2I(p.FromMM(x), p.FromMM(y))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resize_antenna_reserve(footprint):
    """Reduce the inherited 15 mm zone and its matching courtyard to 5 mm."""
    assert footprint.GetOrientationDegrees()==180
    zones=list(footprint.Zones())
    assert len(zones)==1 and zones[0].GetZoneName()=='Antenna'
    zone=zones[0]
    bounds=zone.GetBoundingBox()
    assert tuple(p.ToMM(bounds.GetSize()))==(45.4,19.5)
    x0,y0=p.ToMM(bounds.GetPosition())
    x1,y1=x0+45.4,y0+19.5
    reduction=15.0-ANTENNA_CLEARANCE_MM
    # Keep the boundary beside the module body fixed; reduce the three free sides.
    def adjusted(point):
        x,y=p.ToMM(point)
        if abs(x-x0)<1e-6: x+=reduction
        elif abs(x-x1)<1e-6: x-=reduction
        if abs(y-y1)<1e-6: y-=reduction
        return xy(x,y)
    for graphic in footprint.GraphicalItems():
        if graphic.GetLayer()==p.F_CrtYd:
            graphic.SetStart(adjusted(graphic.GetStart()))
            graphic.SetEnd(adjusted(graphic.GetEnd()))
        elif graphic.GetLayer()==p.F_SilkS and isinstance(graphic,p.PCB_SHAPE) and graphic.GetShape()==p.SHAPE_T_SEGMENT:
            # The inherited silk extends beyond the antenna body. Bring its rear
            # strokes inside the curved board edge while retaining the pin marker.
            silk_end=p.ToMM(footprint.GetPosition().y)+9.5
            for endpoint in ('Start','End'):
                x,y=p.ToMM(getattr(graphic,'Get'+endpoint)())
                getattr(graphic,'Set'+endpoint)(xy(x,min(y,silk_end)))
    zone.Outline().RemoveAllContours()
    zone.Outline().NewOutline()
    for x,y in ((x0+reduction,y0),(x1-reduction,y0),
                (x1-reduction,y1-reduction),(x0+reduction,y1-reduction)):
        zone.Outline().Append(p.FromMM(x),p.FromMM(y))


def label(board, text, x, y, size=1):
    item = p.PCB_TEXT(board)
    item.SetText(text)
    item.SetPosition(xy(x, y))
    item.SetTextSize(xy(size, size))
    item.SetTextThickness(p.FromMM(.15))
    item.SetLayer(p.Dwgs_User)
    board.Add(item)


def wire_array(board, ref, rows, power=False):
    footprint = p.FOOTPRINT(board)
    footprint.SetReference(ref)
    footprint.SetValue('STUDY 5-wire power' if power else 'STUDY 14-wire signals')
    footprint.SetAttributes(p.FP_THROUGH_HOLE)
    footprint.SetPosition(xy(0, 0))
    footprint.Reference().SetVisible(False)
    footprint.Value().SetVisible(False)
    for i, net in enumerate(rows):
        pad = p.PAD(footprint)
        pad.SetNumber(str(i+1))
        pad.SetAttribute(p.PAD_ATTRIB_PTH)
        pad.SetShape(p.PAD_SHAPE_CIRCLE)
        pad.SetSize(xy(2.4, 2.4) if power else xy(1.8, 1.8))
        pad.SetDrillSize(xy(1.2, 1.2) if power else xy(.8, .8))
        pad.SetLayerSet(p.PAD.PTHMask())
        pad.SetPosition(xy(*wire_position(i,power)))
        pad.SetNetCode(board.FindNet(net).GetNetCode())
        footprint.Add(pad)
    board.Add(footprint)


def mounting(board, start):
    for i, (x, y) in enumerate(MOUNTS):
        footprint = p.FOOTPRINT(board)
        footprint.SetReference(f'H{start+i}')
        footprint.SetValue('STUDY M2 clearance / 5mm support envelope')
        footprint.SetPosition(xy(x, y))
        footprint.Reference().SetVisible(False)
        footprint.Value().SetVisible(False)
        pad = p.PAD(footprint)
        pad.SetAttribute(p.PAD_ATTRIB_NPTH)
        pad.SetShape(p.PAD_SHAPE_CIRCLE)
        pad.SetSize(xy(2.2, 2.2))
        pad.SetDrillSize(xy(2.2, 2.2))
        pad.SetLayerSet(p.PAD.PTHMask())
        pad.SetPosition(xy(x, y))
        footprint.Add(pad)
        circle = p.PCB_SHAPE(footprint)
        circle.SetShape(p.SHAPE_T_CIRCLE)
        circle.SetCenter(xy(x, y))
        circle.SetEnd(xy(x+2.5, y))
        circle.SetWidth(p.FromMM(.05))
        circle.SetLayer(p.F_CrtYd)
        footprint.Add(circle)
        board.Add(footprint)


def preview(boards, ownership, sheets, out):
    # An engineering placement drawing, with real pad outlines from KiCad.
    sys.path.insert(0, str(ROOT/'build/two-layer/python'))
    from finish_copper import polygons
    colors = {'Upper': '#dd9d43', 'Lower': '#59b4c5'}
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="840" viewBox="0 0 200 150">',
           '<rect width="200" height="150" fill="#101822"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#e5edf4} .small{font-size:1.4px}</style>',
           '<text x="8" y="7" font-size="3.8">MagMouse stacked Main — placement study</text>',
           f'<text x="8" y="12" font-size="2.2">Unrouted • {len(ownership)} components • passive plastic buttons with Hall sensing</text>']
    for j, (name, board) in enumerate(boards.items()):
        tx, ty = 10+j*100, 23
        svg += [f'<text x="{tx}" y="19" font-size="3">{name}: tapered 70 × 100 mm</text>',
                f'<g transform="translate({tx},{ty})">']
        outline = ' '.join(f'{x},{y}' for x,y in outline_points(board))
        svg.append(f'<polygon points="{outline}" fill="#1d2d3a" stroke="#dce9ef" stroke-width=".3"/>')
        ax0,ay0,ax1,ay1=ANTENNA
        svg += [f'<clipPath id="outline-{name}"><polygon points="{outline}"/></clipPath>',
                f'<g clip-path="url(#outline-{name})">',
                f'<rect x="{ax0}" y="{ay0}" width="{ax1-ax0}" height="{ay1-ay0}" fill="#402c3c" stroke="#da88b8" stroke-dasharray="1,1" stroke-width=".2"/>',
                f'<text x="{(ax0+ax1)/2}" y="{ay0+2}" text-anchor="middle" font-size="1.3">ANTENNA / {ANTENNA_CLEARANCE_MM:g} mm CLEARANCE</text>', '</g>']
        if name == 'Lower':
            svg += ['<rect x="31.2" y="43.68" width="8.6" height="17.26" fill="#183e49" stroke="#67d5ef" stroke-width=".2"/>']
        for f in board.GetFootprints():
            ref = f.GetReference()
            if ref=='U3':
                # Show the module's physical perimeter, including its antenna end.
                bx0,by0,bx1,by1=ANTENNA_BODY
                svg.append(f'<rect x="{bx0}" y="{by0-15.5}" width="{bx1-bx0}" height="{by1-by0+15.5}" fill="none" stroke="#59b4c5" stroke-width=".2"/>')
            for pad in f.Pads():
                if not pad.IsOnLayer(p.F_Cu):
                    continue
                shape = p.SHAPE_POLY_SET()
                pad.TransformShapeToPolygon(shape, p.F_Cu, 0, p.FromMM(.01), p.ERROR_INSIDE)
                for poly in polygons(shape):
                    coords = ' '.join(f'{x:.4f},{y:.4f}' for x,y in poly.exterior.coords)
                    svg.append(f'<polygon points="{coords}" fill="{colors[name]}"/>')
            x,y = p.ToMM(f.GetPosition())
            if ref.startswith('H'):
                svg.append(f'<circle cx="{x}" cy="{y}" r="2.5" fill="none" stroke="#e9c66e" stroke-width=".25"/>')
            elif ref in ownership:
                svg.append(f'<text class="small" x="{x+.7}" y="{y-.7}">{html.escape(ref)}</text>')
        svg += ['<text x="4" y="39" font-size="1.5">Signals + GND</text>',
                '<text x="26" y="14" font-size="1.5">Power + 2 GND</text>', '</g>']
    svg += ['<text x="10" y="133" font-size="2.4">Both boards: 70 × 100 mm • full-size components • matching tapered outlines</text>',
            '<text x="10" y="139" font-size="2.4">19 inter-board wires: 13 signals + 3 power rails + 3 shared grounds</text>',
            '<text x="10" y="145" font-size="2.1">Unrouted placement study. Stack height and assembled fit remain to be established.</text>', '</svg>']
    out.write_text('\n'.join(svg), encoding='utf-8')
    import resvg_py
    out.with_suffix('.png').write_bytes(resvg_py.svg_to_bytes(svg_path=str(out)))


def wire_document(wires):
    lines = ['# Proposed sandwich wire map', '',
        'This is the exact endpoint map for the unrouted placement study. Wire gauge,',
        'cut lengths and assembled stack height are not yet selected.', '',
        'Both boards use the same top-view XY orientation; do not mirror the upper',
        'board. Connect like-numbered pads. Upper pads can be soldered from underneath.',
        'There are three shared GND wires: one in the signal array and two in the power array.', '',
        '| Lower pad | Upper pad | Net | Role / direction |',
        '| --- | --- | --- | --- |']
    lines += [f"| {w['lower']} | {w['upper']} | {w['net']} | {w['direction']} |" for w in wires]
    lines += ['', '## Pad coordinates', '',
        '- Signal arrays J101/J102: 14 pins in two columns. Odd pins at x = 6.00 mm,',
        '  even pins at x = 8.54 mm. Rows start at y = 42.00 mm with 2.54 mm pitch.',
        '  Row 1 is pins 1/2; row 7 is pins 13/14 at y = 57.24 mm. Only pin 1 is GND.',
        '- Power arrays J103/J104: five pins at y = 11.00 mm and x = 25.00, 30.08,',
        '  35.16, 40.24 and 45.32 mm. Pins 1 and 5 are shared power grounds.',
        '- Signal pads: 1.8 mm copper diameter / 0.8 mm finished-hole design value.',
        '  Power pads: 2.4 mm copper diameter / 1.2 mm finished-hole design value.',
        '  These are candidate geometries; verify actual wire fit and fabrication tolerances.',
        '', 'Raw VBUS goes up to the protection circuitry; protected PWR_5V returns to',
        'the lower regulator; regulated +3V3 goes back up. ACT_5V stays on Upper and',
        'feeds the existing Wheel power connector J10 from there.', '',
        'Every original endpoint of every boundary net is listed in partition.json.',
        'USB data/CC, Hall outputs and ADC analog inputs',
        'do not cross this new interface.', '']
    (HERE/'WIRE_MAP.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    wheel_library()
    scratch = ROOT/'build/sandwich'
    scratch.mkdir(parents=True, exist_ok=True)
    cli = Path(sys.executable).with_name('kicad-cli.exe')
    source = ROOT/'hardware/modular/main/Main.kicad_pcb'
    current = BASE/'main/Main.kicad_pcb'
    netlist = scratch/'Main.xml'
    subprocess.run([str(cli), 'sch', 'export', 'netlist', '--format', 'kicadxml',
                    '-o', str(netlist), str(HERE/'main-circuit/Main.kicad_sch')], check=True)
    xml = ET.parse(netlist).getroot()
    comps = {c.get('ref'): c for c in xml.findall('./components/comp')}
    sheets = {ref:c.find('sheetpath').get('names').strip('/') for ref,c in comps.items()}
    owners = {ref:OVERRIDES.get(ref, 'Upper' if sheet in UPPER_SHEETS else 'Lower')
              for ref,sheet in sheets.items()}
    original_board = p.LoadBoard(str(source))
    for edge in original_board.GetDrawings():
        if edge.GetLayer()==p.Edge_Cuts:
            resize_edge(edge)
    target_edges = edge_signature(original_board)
    original = signature(original_board)
    assert original == signature(p.LoadBoard(str(current)))
    netmap={(node.get('ref'),node.get('pin')):net.get('name')
            for net in xml.findall('./nets/net') for node in net.findall('node')}
    original=expected_inventory(original,netmap)
    original['J8']=connector_signature()
    assert set(original) == set(owners)
    boundary = {}
    for net in xml.findall('./nets/net'):
        endpoints = {side:[] for side in ('Lower','Upper')}
        for node in net.findall('node'):
            ref,pin = node.get('ref'),node.get('pin')
            assert (pin,net.get('name')) in original[ref]['pads'], (ref,pin,net.get('name'))
            endpoints[owners[ref]].append(f'{ref}.{pin}')
        if all(endpoints.values()):
            boundary[net.get('name')] = endpoints
    assert set(boundary) == {'GND'} | {n for n,d in SIGNALS+RAILS}
    wires = []
    for kind, entries, lowref, upref in [('signal', SIGNAL_PINS, 'J101','J102'),
                                       ('power', POWER_PINS, 'J103','J104')]:
        for i,(net,direction) in enumerate(entries):
            wires.append({'kind':kind, 'net':net, 'lower':f'{lowref}.{i+1}',
                          'upper':f'{upref}.{i+1}', 'direction':direction})
    boards, placement, positions = {}, {}, {}
    for name in ('Lower','Upper'):
        folder = HERE/name.lower()
        folder.mkdir(parents=True,exist_ok=True)
        board = p.LoadBoard(str(source))
        for track in list(board.GetTracks()):
            board.Remove(track); track.thisown=False
        for zone in list(board.Zones()):
            # Retain optical opening only on Lower. U3's footprint owns its antenna keepout.
            if name=='Lower' and zone.GetIsRuleArea() and 'PMW3360 APERTURE' in zone.GetZoneName():
                zone.Move(xy(-5,-20))
                continue
            board.Remove(zone); zone.thisown=False
        for item in list(board.GetDrawings()):
            if item.GetLayer()==p.Edge_Cuts:
                resize_edge(item)
                continue
            board.Remove(item); item.thisown=False
        for f in list(board.GetFootprints()):
            ref=f.GetReference()
            if ref not in owners or owners[ref]!=name:
                board.Remove(f); f.thisown=False
            elif ref=='J8':
                replace_connector(board,f)
            elif ref=='U3':
                resize_antenna_reserve(f)
                # Keep the stock library intact and make the intentional RF edit
                # reproducible without suppressing library-mismatch DRC checks.
                f.SetFPID(p.LIB_ID('MagMouseSandwich', 'ESP32-S2-MINI-1'))
                library=HERE/'MagMouseSandwich.pretty'
                library.mkdir(exist_ok=True)
                library_footprint=p.FOOTPRINT(f)
                library_footprint.SetOrientationDegrees(0)
                library_footprint.SetPosition(xy(0,0))
                library_footprint.SetReference('REF**')
                p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(
                    library.as_posix(),library_footprint)
        update_pads(board,netmap)
        board.SetCopperLayerCount(2)
        layers=board.GetEnabledLayers()
        layers.RemoveLayer(p.In1_Cu);layers.RemoveLayer(p.In2_Cu)
        board.SetEnabledLayers(layers)
        board.GetDesignSettings().m_HasStackup=False
        if name=='Upper':
            # Project the lower module's antenna reserve onto both copper faces.
            # Same outline requires substrate above the antenna; RF still needs validation.
            zone=p.ZONE(board)
            zone.SetIsRuleArea(True)
            zone.SetZoneName('LOWER ESP32 ANTENNA - PROJECTED STACK RESERVE')
            zone.SetLayerSet(p.LSET.ExternalCuMask())
            zone.SetDoNotAllowTracks(True)
            zone.SetDoNotAllowVias(True)
            zone.SetDoNotAllowPads(True)
            zone.SetDoNotAllowZoneFills(True)
            zone.SetDoNotAllowFootprints(True)
            zone.Outline().NewOutline()
            x0,y0,x1,y1=ANTENNA
            for x,y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1)):
                zone.Outline().Append(p.FromMM(x),p.FromMM(y))
            board.Add(zone)
        wire_array(board,'J101' if name=='Lower' else 'J102',[n for n,d in SIGNAL_PINS])
        wire_array(board,'J103' if name=='Lower' else 'J104',[n for n,d in POWER_PINS],power=True)
        mounting(board,101 if name=='Lower' else 105)
        positions[name]=place(board,name,sheets,owners,outline_points(board))
        label(board,f'{name.upper()} / 70x100 / UNROUTED',35,8,.8)
        label(board,'SIGNALS + GND',7.2,39,.6)
        label(board,'POWER + 2 GND',35,14,.6)
        remaining={ref:data for ref,data in signature(board).items() if ref in owners}
        assert remaining=={ref:original[ref] for ref in owners if owners[ref]==name}
        path=folder/(name+'.kicad_pcb')
        p.SaveBoard(str(path),board)
        # Save a matching project for design rules; no split schematic exists yet.
        shutil.copyfile(BASE/'main/Main.kicad_pro',folder/(name+'.kicad_pro'))
        for table in ('fp-lib-table','sym-lib-table'):
            text=(BASE/'main'/table).read_text().replace('${KIPRJMOD}/','${KIPRJMOD}/../')
            if table=='fp-lib-table':
                text=text.rstrip()[:-1]+' (lib (name "MagMouseSandwich") (type "KiCad") (uri "${KIPRJMOD}/../MagMouseSandwich.pretty") (options "") (descr "Sandwich antenna clearance: 5 mm")))\n'
            (folder/table).write_text(text)
        drc=folder/(name+'-drc.json')
        subprocess.run([str(cli),'pcb','drc','--format','json','--output',str(drc),str(path)],check=True)
        result=json.loads(drc.read_text())
        placement[name]={'width_mm':70,'height_mm':100,'front_edge_width_mm':38.5,
            'outline_matches_scaled_original':edge_signature(board)==target_edges,
            'original_footprints':len(remaining),'added_footprints':6,
            'unconnected_items':len(result['unconnected_items']),
            'drc_findings':dict(collections.Counter(v['type'] for v in result['violations'])),
            'board_sha256':sha(path)}
        boards[name]=p.LoadBoard(str(path))
        assert boards[name].GetCopperLayerCount()==2
        assert edge_signature(boards[name])==target_edges
        assert not list(boards[name].GetTracks())
        antenna_zones=([z for f in boards[name].GetFootprints() if f.GetReference()=='U3'
                        for z in f.Zones()] if name=='Lower' else
                       [z for z in boards[name].Zones() if 'ANTENNA' in z.GetZoneName()])
        assert len(antenna_zones)==1
        box=antenna_zones[0].GetBoundingBox()
        assert tuple(p.ToMM(box.GetPosition()))==ANTENNA[:2]
        assert tuple(p.ToMM(box.GetSize()))==(round(ANTENNA[2]-ANTENNA[0],6),
                                             round(ANTENNA[3]-ANTENNA[1],6))
        assert not result['violations'], f'{name}: resolve placement findings before accepting study'
        sys.path.insert(0,str(ROOT/'build/two-layer/python'))
        from shapely.geometry import Polygon, Point, box as shape_box
        outline=Polygon(outline_points(boards[name]))
        assert outline.is_valid
        antenna_body=shape_box(*ANTENNA_BODY)
        assert outline.covers(antenna_body), 'Physical antenna must remain inside the taper'
        antenna_edge_gap=outline.boundary.distance(antenna_body)
        assert .3 <= antenna_edge_gap <= .5, 'Antenna must sit immediately beside the rear edge'
        placement[name]['antenna_body_to_outline_mm']=round(antenna_edge_gap,4)
        margins=[]
        for f in boards[name].GetFootprints():
            if f.GetReference() in ('J101','J102','J103','J104'):
                for pad in f.Pads():
                    center=Point(p.ToMM(pad.GetPosition()))
                    radius=p.ToMM(pad.GetSize().x)/2
                    assert outline.covers(center.buffer(radius+.3))
                    margins.append(outline.boundary.distance(center)-radius)
        for x,y in MOUNTS:
            assert outline.covers(Point(x,y).buffer(2.5+.3)), (name,x,y)
        placement[name]['minimum_new_wire_pad_to_outline_mm']=round(min(margins),4)
        placement[name]['mount_support_envelopes_inside_outline']=True
        placement[name]['outline_area_mm2']=round(outline.area,4)
    # Check the delivered PCB pads, not just the planned net names.
    padmaps={name:{f'{f.GetReference()}.{pad.GetNumber()}':pad
                  for f in b.GetFootprints() for pad in f.Pads()}
             for name,b in boards.items()}
    for wire in wires:
        a=padmaps['Lower'][wire['lower']];b=padmaps['Upper'][wire['upper']]
        assert a.GetNetname()==b.GetNetname()==wire['net']
        assert a.GetPosition()==b.GetPosition()
    assert len({w['lower'] for w in wires})==len(wires)==19
    assert len({w['upper'] for w in wires})==19
    assert sum(w['net']=='GND' for w in wires)==3
    for name,board in boards.items():
        saved={ref:data for ref,data in signature(board).items() if ref in owners}
        assert saved=={ref:original[ref] for ref in owners if owners[ref]==name}
    report={'status':'Unrouted placement study; proposed harness, no split schematics or release approval',
        'source_placement_sha256':sha(source),'current_main_sha256':sha(current),
        'netlist_sha256':sha(netlist),'component_ownership':owners,'component_sheets':sheets,
        'boundary_nets':boundary,'wires':wires,'ground_wire_count':3,'placement':placement,
        'removed_button_actuator_components':sorted(REMOVED),
        'antenna_clearance_mm':ANTENNA_CLEARANCE_MM,'antenna_reserve_bounds_mm':ANTENNA,
        'validation':{'all_208_retained_components_present_once':True,
            'component_and_pad_net_identity_except_revised_J8_and_passive_button_pins':True,
            'all_boundary_nets_have_wire_assignments':True,
            'all_19_saved_pad_pairs_match_net_and_xy':True,
            'both_boards_two_layers_and_unrouted':True,
            'both_outlines_match_70x100_taper':True,
            'split_schematic_parity_checked':False}}
    (HERE/'partition.json').write_text(json.dumps(report,indent=2)+'\n')
    (HERE/'placement-positions.json').write_text(json.dumps(positions,indent=2)+'\n')
    preview(boards,owners,sheets,HERE/'placement.svg')
    wire_document(wires)
    print(json.dumps({'boundary_nets':len(boundary),'wires':len(wires),'placement':placement},indent=2))


if __name__=='__main__':
    main()
