"""Build the 19-wire wheel variant; retain the earlier routed checkpoints.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import math
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import pcbnew as p

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ROOT=HERE.parents[2]
SCRATCH=ROOT/'build/sandwich'
sys.path.insert(0,str(ROOT/'hardware/modular'))
sys.path.insert(0,str(ROOT/'build/two-layer/python'))
import schematic_io as s
from shapely.geometry import LineString, Point, box

SIGNAL_NETS=['GND','SPI_SCLK','SPI_MOSI','CS_DRV8316','DRV_MISO_LOCAL',
             'MOTOR_SPI_SCLK','MOTOR_SPI_MOSI','CS_ADC2','ADC2_MISO_LOCAL',
             'WHEEL_PWM_A','WHEEL_PWM_B','WHEEL_PWM_C','ACT_DRIVE_EN',
             'WHEEL_RUN_REQ','DRV_FAULT_LOCAL_N','+3V3','GND']
FOOTPRINT='Wire_Wheel_17_P2.54mm'
LIBID='MagMouseSandwich:'+FOOTPRINT
VALUE='Wheel 17-wire signals / 2 GND'
CLI=Path(sys.executable).with_name('kicad-cli.exe')


def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))


def connector_signature():
    return {'value':VALUE,'footprint':FOOTPRINT,
            'pads':sorted((str(i+1),net) for i,net in enumerate(SIGNAL_NETS))}


def copy_fields(old,new):
    for key,value in old.GetFieldsText().items():
        if key not in ('Reference','Value','Datasheet','Description'):
            new.SetField(key,value);new.GetField(key).SetVisible(False)


def library():
    folder=HERE/'MagMouseSandwich.pretty'
    folder.mkdir(exist_ok=True)
    lines=[f'(footprint "{FOOTPRINT}" (version 20260206) (generator "pcbnew") (layer "F.Cu")',
           '(descr "17 soldered wires: 14 signals, 3V3, two shared grounds. One unused grid position has no pad.")',
           '(attr through_hole)',
           f'(fp_text reference "REF**" (at 0 -3.67) (layer "F.SilkS") (effects (font (size .8 .8) (thickness .12))))',
           f'(fp_text value "{FOOTPRINT}" (at 0 3.67) (layer "F.Fab") (effects (font (size .8 .8) (thickness .12))))']
    for layer,width in [('F.CrtYd',.05),('F.Fab',.1)]:
        lines.append(f'(fp_rect (start -11.56 -2.67) (end 11.56 2.67) (stroke (width {width}) (type default)) (fill none) (layer "{layer}"))')
    for i in range(17):
        x,y=(i//2-4)*2.54,(i%2-.5)*2.54
        shape='rect' if i==0 else 'circle'
        lines.append(f'(pad "{i+1}" thru_hole {shape} (at {x} {y}) (size 1.8 1.8) (drill .8) (layers "*.Cu" "*.Mask"))')
    (folder/(FOOTPRINT+'.kicad_mod')).write_text('\n'.join(lines+[')'])+'\n')
    return folder


def replace_connector(board,old):
    plugin=p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP)
    new=plugin.FootprintLoad((HERE/'MagMouseSandwich.pretty').as_posix(),FOOTPRINT)
    new.SetFPID(p.LIB_ID('MagMouseSandwich',FOOTPRINT))
    copy_fields(old,new)
    new.SetReference(old.GetReference());new.SetValue(VALUE)
    new.SetSheetname(old.GetSheetname());new.SetSheetfile(old.GetSheetfile())
    new.SetPath(old.GetPath());new.SetUuid(old.m_Uuid)
    new.SetOrientationDegrees(old.GetOrientationDegrees())
    new.SetPosition(old.GetPosition())
    board.Remove(old);old.thisown=False
    board.Add(new)
    for pad in new.Pads():pad.SetNet(board.FindNet(SIGNAL_NETS[int(pad.GetNumber())-1]))
    return new


def tables(source,dest):
    for name in ('fp-lib-table','sym-lib-table'):
        text=(source/name).read_text().replace('${KIPRJMOD}/','${KIPRJMOD}/../')
        if name=='fp-lib-table':
            text=text.rstrip()[:-1]+' (lib (name "MagMouseSandwich") (type "KiCad") (uri "${KIPRJMOD}/../MagMouseSandwich.pretty") (options "") (descr "Stacked variant footprints")))\n'
        (dest/name).write_text(text)


def edit_schematic(path,ref,project):
    tree=s.parse(path.read_text(encoding='utf-8'))
    instance=next(n for n in s.allof(tree,'symbol') if s.props(n).get('Reference')==ref)
    old=s.props(instance)
    cache=s.get(tree,'lib_symbols')
    symbol=next(n for n in s.allof(cache,'symbol') if n[1]==s.get(instance,'lib_id')[1])
    positions=set(s.pin_positions(instance,symbol).values())
    # The original connector has one short wire and one global label per pin.
    ends=set()
    for wire in s.allof(tree,'wire'):
        pts=[tuple(map(float,n[1:])) for n in s.allof(s.get(wire,'pts'),'xy')]
        if any(pt in positions for pt in pts):
            ends.update(pts);tree.remove(wire)
    for label in s.allof(tree,'global_label'):
        if tuple(map(float,s.get(label,'at')[1:3])) in ends:tree.remove(label)
    assert len(ends)==60
    location=tuple(map(float,s.get(instance,'at')[1:3]))
    instance_path=s.get(s.get(s.get(instance,'instances'),'project'),'path')[1]
    uid=s.get(instance,'uuid')[1]
    tree.remove(instance);cache.remove(symbol)
    symbol=s.library_symbol(Path(sys.executable).parents[1]/'share/kicad','Connector_Generic:Conn_01x17')
    fields={key:value for key,value in old.items() if key not in ('Reference','Value')}
    fields['Footprint']=LIBID
    new=s.add_component(tree,symbol,ref,VALUE,location,
                        {str(i+1):net for i,net in enumerate(SIGNAL_NETS)},
                        project,instance_path,fields)
    s.get(new,'uuid')[1]=uid
    for text in s.allof(tree,'text'):
        if 'MAIN J8 pin N' in text[1]:
            text[1]='19-wire wheel harness: J8.N to J9.N (17 wires).\nPins 1 and 17 are shared GND; pin 16 is +3V3.\nPower J10/J11: 1 ACT_5V, 2 GND. Three shared grounds total.'
    s.write(path,tree)


def netlist(path,out):
    subprocess.run([str(CLI),'sch','export','netlist','--format','kicadxml','-o',str(out),str(path)],check=True)
    xml=ET.parse(out).getroot()
    return {(n.get('ref'),n.get('pin')):net.get('name')
            for net in xml.findall('./nets/net') for n in net.findall('node')}


def prepare():
    library();SCRATCH.mkdir(exist_ok=True)
    for name,folder,ref in [('Main','main-circuit','J8'),('Wheel','wheel','J9')]:
        source=BASE/name.lower();dest=HERE/folder;dest.mkdir(exist_ok=True)
        for f in source.iterdir():
            if f.suffix in ('.kicad_sch','.kicad_pro','.kicad_dru'):shutil.copyfile(f,dest/f.name)
        tables(source,dest)
        edit_schematic(dest/'18_Wheel_Harness.kicad_sch',ref,name)
        before=netlist(source/(name+'.kicad_sch'),SCRATCH/(name+'-old.xml'))
        after=netlist(dest/(name+'.kicad_sch'),SCRATCH/(name+'-19wire.xml'))
        assert {k:v for k,v in before.items() if k[0]!=ref}=={k:v for k,v in after.items() if k[0]!=ref}
        assert {pin:net for (r,pin),net in after.items() if r==ref}=={str(i+1):net for i,net in enumerate(SIGNAL_NETS)}
    # The active Main reference uses passive Hall buttons even after a rebuild.
    from passive_buttons import revise
    revise()
    board=p.LoadBoard(str(BASE/'wheel/Wheel.kicad_pcb'))
    old=next(f for f in board.GetFootprints() if f.GetReference()=='J9')
    replace_connector(board,old)
    # Open only the old connector's entry corridor. Preserve routing elsewhere.
    corridor=box(15.8,1,55.2,8)
    for f in board.GetFootprints():
        if f.GetReference()!='J9':
            assert all(not corridor.covers(Point(p.ToMM(pad.GetPosition()))) for pad in f.Pads())
    removed=0
    for t in list(board.GetTracks()):
        # Reroute the raw header signals as complete nets, avoiding disconnected
        # fixed stubs from the previous 30-pad fanout. Local analog, motor-phase,
        # supply and ground routing remains outside the entry corridor.
        if t.GetNetname() in set(SIGNAL_NETS)-{'GND','+3V3'}:
            board.Remove(t);t.thisown=False;removed+=1
            continue
        if isinstance(t,p.PCB_VIA):
            if corridor.covers(Point(p.ToMM(t.GetPosition()))):
                board.Remove(t);t.thisown=False;removed+=1
            continue
        line=LineString([p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())])
        if not line.intersects(corridor):continue
        remainder=line.difference(corridor)
        pieces=list(remainder.geoms) if hasattr(remainder,'geoms') else [remainder]
        for piece in pieces:
            if piece.is_empty:continue
            new=p.PCB_TRACK(board);new.SetNetCode(t.GetNetCode());new.SetLayer(t.GetLayer());new.SetWidth(t.GetWidth())
            new.SetStart(xy(*piece.coords[0]));new.SetEnd(xy(*piece.coords[-1]));board.Add(new)
        board.Remove(t);t.thisown=False;removed+=1
    board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones())
    p.SaveBoard(str(HERE/'wheel/Wheel.kicad_pcb'),board)
    assert p.ExportSpecctraDSN(board,str(SCRATCH/'Wheel-19wire.dsn'))
    dsn=SCRATCH/'Wheel-19wire.dsn'
    text=dsn.read_text()
    start=text.index('(class kicad_default');end=text.index('(class Power',start)
    text=text[:start]+text[start:end].replace(' GND ',' ')+text[end:]
    text=text.replace('(class Power','(class Ground GND (circuit (use_via "Via[0-1]_450:200_um")) (rule (width 150) (clearance 150)))\n    (class Power')
    dsn.write_text(text)
    print('Prepared 19-wire circuit; trimmed entry-corridor copper items:',removed)


def import_routes():
    board=p.LoadBoard(str(HERE/'wheel/Wheel.kicad_pcb'))
    assert p.ImportSpecctraSES(board,str(SCRATCH/'Wheel-19wire.ses'))
    # Retain schematic fields when importing a previously prepared interface.
    original=p.LoadBoard(str(BASE/'wheel/Wheel.kicad_pcb'))
    old=next(f for f in original.GetFootprints() if f.GetReference()=='J9')
    new=next(f for f in board.GetFootprints() if f.GetReference()=='J9')
    copy_fields(old,new);new.SetValue(VALUE)
    for item in board.GetTracks():
        if isinstance(item,p.PCB_VIA):
            if item.GetWidth(p.F_Cu)==p.FromMM(.45):item.SetDrill(p.FromMM(.2))
        elif item.GetWidth()<p.FromMM(.127):
            item.SetWidth(p.FromMM(.127))
    board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones())
    p.SaveBoard(str(HERE/'wheel/Wheel.kicad_pcb'),board)


def preview(connectors):
    import resvg_py
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="500" viewBox="0 0 100 50">',
         '<rect width="100" height="50" fill="#101822"/>',
         '<style>text{font-family:Arial,sans-serif;fill:#e5edf4}</style>',
         '<text x="3" y="3" font-size="2">Wheel harness: 19 wires, three shared grounds</text>']
    for ref,cx,cy,title in [('J8',22,26,'Lower / J8'),('J9',70,26,'Wheel / J9')]:
        f=connectors[ref]
        svg.append(f'<text x="{cx}" y="6" text-anchor="middle" font-size="1.6">{title}</text>')
        w,h=(4.34,37.36) if ref=='J8' else (37.36,4.34)
        svg.append(f'<rect x="{cx-w/2}" y="{cy-h/2}" width="{w}" height="{h}" fill="none" stroke="#768593" stroke-width=".15" stroke-dasharray=".8,.6"/>')
        fx,fy=p.ToMM(f.GetPosition())
        for pad in f.Pads():
            x,y=p.ToMM(pad.GetPosition());x+=cx-fx;y+=cy-fy
            color='#78cc94' if pad.GetNetname()=='GND' else '#59b4c5'
            if pad.GetShape()==p.PAD_SHAPE_RECT:
                svg.append(f'<rect x="{x-.9}" y="{y-.9}" width="1.8" height="1.8" fill="{color}"/>')
            else:svg.append(f'<circle cx="{x}" cy="{y}" r=".9" fill="{color}"/>')
            svg.append(f'<text x="{x}" y="{y+.32}" text-anchor="middle" style="fill:#101822" font-size=".95">{pad.GetNumber()}</text>')
    svg += ['<text x="48" y="35" font-size="1.5">17 signal-header wires + existing 2-wire power pair</text>',
            '<text x="48" y="39" font-size="1.5">Signal arrays: 37.36 → 22.12 mm long</text>',
            '<text x="48" y="43" font-size="1.3">Dashed outline: previous size. Green pads: GND.</text>',
            '<text x="3" y="48" font-size="1.4">Component-side views. Connect matching pin numbers; do not reverse the new pin map.</text>','</svg>']
    out=HERE/'wheel-connectors.svg';out.write_text('\n'.join(svg),encoding='utf-8')
    out.with_suffix('.png').write_bytes(resvg_py.svg_to_bytes(svg_path=str(out)))


def verify():
    path=HERE/'wheel/Wheel.kicad_pcb'
    subprocess.run([str(CLI),'pcb','drc','--format','json','--schematic-parity','--output',str(HERE/'wheel/Wheel-drc.json'),str(path)],check=True)
    report=json.loads((HERE/'wheel/Wheel-drc.json').read_text())
    print('Wheel DRC:',dict(collections.Counter(v['type'] for v in report['violations'])),
          'unconnected:',len(report['unconnected_items']),'parity:',len(report.get('schematic_parity',[])))
    assert not report['violations'] and not report['unconnected_items'] and not report.get('schematic_parity',[])
    boards={name:p.LoadBoard(str(HERE/folder/(name+'.kicad_pcb'))) for name,folder in [('Lower','lower'),('Upper','upper'),('Wheel','wheel')]}
    connectors={ref:next(f for f in boards[name].GetFootprints() if f.GetReference()==ref)
                for ref,name in [('J8','Lower'),('J9','Wheel'),('J10','Upper'),('J11','Wheel')]}
    wires=[]
    for a,b,nets in [('J8','J9',SIGNAL_NETS),('J10','J11',['ACT_5V','GND'])]:
        for ref in (a,b):
            assert {pad.GetNumber():pad.GetNetname() for pad in connectors[ref].Pads()}=={str(i+1):net for i,net in enumerate(nets)}
        wires.extend({'main':f'{a}.{i+1}','wheel':f'{b}.{i+1}','net':net} for i,net in enumerate(nets))
    assert len(wires)==19 and sum(w['net']=='GND' for w in wires)==3
    source=p.LoadBoard(str(BASE/'wheel/Wheel.kicad_pcb'))
    def inventory(board):
        return {f.GetReference():(f.GetValue(),tuple(p.ToMM(f.GetPosition())),f.GetOrientationDegrees(),
                sorted((pad.GetNumber(),pad.GetNetname(),tuple(p.ToMM(pad.GetSize())),tuple(p.ToMM(pad.GetDrillSize()))) for pad in f.Pads()))
                for f in board.GetFootprints() if f.GetReference()!='J9'}
    assert inventory(source)==inventory(boards['Wheel'])
    outline=p.SHAPE_POLY_SET()
    assert boards['Wheel'].GetBoardPolygonOutlines(outline,False)
    assert boards['Wheel'].GetCopperLayerCount()==2
    data={'wire_count':19,'ground_wire_count':3,'signal_array_pad_count':17,
          'wheel_dimensions_mm':p.ToMM(outline.BBox().GetSize()),'wheel_copper_layers':2,
          'signal_array_copper_envelope_mm':[22.12,4.34],'previous_array_copper_envelope_mm':[37.36,4.34],
          'wires':wires,'wheel_other_components_unchanged':True,
          'wheel_drc_findings':0,'wheel_unconnected':0,'wheel_schematic_parity_findings':0,
          'board_sha256':{name:hashlib.sha256((HERE/('wheel' if name=='Wheel' else name.lower())/(name+'.kicad_pcb')).read_bytes()).hexdigest() for name in boards}}
    (HERE/'wheel-interface.json').write_text(json.dumps(data,indent=2)+'\n')
    lines=['# Wheel harness — 19 wires','',
           'J8 on Lower connects to J9 on Wheel using matching pin numbers. This replaces',
           'the old 30-pad reversed-number map. J10 on Upper connects to Wheel J11.',
           'There are 14 signals, two supply wires, and three shared grounds.',
           '', 'The signal arrays have 17 holes on a 2 × 9 grid with one position omitted.',
           'Copper envelope: 22.12 × 4.34 mm (previously 37.36 × 4.34 mm).',
           'Signal pads remain 1.8 mm diameter with 0.8 mm drills.', '',
           '| Main pad | Wheel pad | Net |','| --- | --- | --- |']
    lines += [f"| {w['main']} | {w['wheel']} | {w['net']} |" for w in wires]
    lines += ['', 'Both headers are shown from the component side in the PCB files.',
              'Follow pad numbers; their rotations differ. No pin reversal is needed.',
              'Wire gauge and lengths remain dependent on the assembled stack.', '']
    (HERE/'WHEEL_WIRE_MAP.md').write_text('\n'.join(lines))
    preview(connectors)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','import','verify'])
    {'prepare':prepare,'import':import_routes,'verify':verify}[ap.parse_args().action]()
