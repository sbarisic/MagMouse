"""Apply the reviewed 2026-11 circuit corrections using KiCad Python.

The saved schematics/boards are authoritative. This migration refuses to take
a second baseline. Temporary rollback boards in ignored build/ can be removed
after validation; the tracked before measurements and Git remain the baseline.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import argparse
import copy
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew as p
from route_main import HERE, ROOT, CLI, xy
from export_quote import BOARDS
sys.path.insert(0, str(ROOT / 'hardware/common'))
import schematic_io as s
from passive_buttons import symbol, pin_net

WORK = ROOT / 'build/circuit-fixes'
EVIDENCE = HERE / 'circuit-review'
LIB = Path(sys.executable).parents[1] / 'share/kicad'
NEXPERIA = 'https://assets.nexperia.com/documents/data-sheet/74LVC125A.pdf'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def baseline():
    EVIDENCE.mkdir(exist_ok=True)
    target = EVIDENCE / 'baseline.json'
    if target.exists():
        return json.loads(target.read_text())
    result = {}
    for name, path in BOARDS.items():
        board = p.LoadBoard(str(path))
        result[name] = {'sha256': sha(path), 'components': {
            f.GetReference(): {'value': f.GetValue(), 'footprint': str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),
                'xy': list(p.ToMM(f.GetPosition())), 'angle': f.GetOrientationDegrees(),
                'pads': sorted((q.GetNumber(), q.GetNetname()) for q in f.Pads())}
            for f in board.GetFootprints()}}
        if name != 'Encoder':
            dest = WORK / 'original' / name
            dest.mkdir(parents=True, exist_ok=True)
            for source in path.parent.glob('*.kicad_*'):
                (dest / source.name).write_bytes(source.read_bytes())
    target.write_text(json.dumps(result, indent=2) + '\n')
    return result


def properties(node, fields):
    for key, value in fields.items():
        old = next((v for v in s.allof(node, 'property') if v[1] == key), None)
        if old is not None:
            old[2] = value
        else:
            x, y = s.get(node, 'at')[1:3]
            node.append(s.parse(f'(property {json.dumps(key)} {json.dumps(value)} '
                f'(at {x} {y} 0) (hide yes) (effects (font (size 1 1))))'))


def replace(path, ref, fields):
    tree = s.parse(path.read_text(encoding='utf-8'))
    node, _ = symbol(tree, ref)
    properties(node, fields)
    s.write(path, tree)


def export(name):
    WORK.mkdir(parents=True, exist_ok=True)
    path = WORK / (name + '.xml')
    subprocess.run([str(CLI), 'sch', 'export', 'netlist', '--format', 'kicadxml',
        '-o', str(path), str(BOARDS[name].with_suffix('.kicad_sch'))], check=True)
    root = ET.parse(path).getroot()
    comps = {c.get('ref'): c for c in root.findall('./components/comp')}
    pins = {(n.get('ref'), n.get('pin')): net.get('name')
        for net in root.findall('./nets/net') for n in net.findall('node')}
    return comps, pins


def fieldset(mpn, footprint, datasheet, manufacturer, rating=''):
    return {'Footprint': footprint, 'Datasheet': datasheet, 'MPN': mpn,
        'Manufacturer': manufacturer, 'Rating': rating, 'LCSC': '', 'JLCPCB Part #': '',
        'Checked': '2026-11-05', 'Sourcing Status': 'Manufacturer specification checked; assembly stock unverified'}


def circuit():
    before = baseline()
    if (HERE / 'wheel/15_Wheel_Undervoltage.kicad_sch').exists():
        raise RuntimeError('Circuit migration already applied; use validation, not replay')
    optical = HERE / 'lower/17_Optical_Sensor.kicad_sch'
    buffer_fields = {'Value': '74LVC125APW,118', 'MPN': '74LVC125APW,118',
        'Manufacturer': 'Nexperia', 'Datasheet': NEXPERIA, 'LCSC': 'C6059',
        'JLCPCB Part #': 'C6059', 'Supplier URL': 'https://www.lcsc.com/product-detail/C6059.html',
        'Checked': '2026-11-05', 'Sourcing Status': 'Ioff and package checked; current assembly stock unverified'}
    replace(optical, 'U37', buffer_fields)
    for side,refs in [('lower',('U25','U29')),('wheel',('U24','U26'))]:
        for ref in refs:replace(HERE/side/'11_Wheel_SPI.kicad_sch',ref,buffer_fields)
    power = HERE / 'upper/05_Protected_Power.kicad_sch'
    for ref in ('R36','R37','R38','R39'):
        value = '11k' if ref == 'R39' else '10k'
        replace(power, ref, {'Value': value, 'MPN': 'RC1206FR-0711KL' if value == '11k' else 'RC1206FR-0710KL',
            'LCSC':'', 'JLCPCB Part #':'', 'Checked':'2026-11-05',
            'Sourcing Status':'1206 1% UVLO correction; assembly stock unverified'})

    driver = HERE / 'wheel/10_Wheel_Driver.kicad_sch'
    tree = s.parse(driver.read_text())
    if not any(n[1] == 'WHEEL_RUN_REQUESTED' for n in s.allof(tree, 'global_label')):
        pin_net(tree, 'U22', '3', 'WHEEL_RUN_REQUESTED')
    s.text(tree, 'U22 gate 1 produces WHEEL_RUN_REQUESTED. Sheet 15 qualifies it with local VM voltage.\nWHEEL_RUN_EN drives Q4, the three PWM gates and INLA/INLB/INLC.\nUndervoltage disables drive without preventing ACT_5V from starting.', 20, 270, 'wheel-uv-gate-note')
    s.write(driver, tree)

    rootpath = HERE / 'wheel/Wheel.kicad_sch'
    root = s.parse(rootpath.read_text())
    rootid = s.get(root, 'uuid')[1]
    sheetid = s.ident('wheel-local-undervoltage-sheet')
    sheetpath = f'/{rootid}/{sheetid}'
    sheet = s.parse(f'(kicad_sch (version 20250114) (generator "eeschema") '
        f'(uuid "{s.ident("wheel-uv-file")}") (paper "A3") '
        '(title_block (title "Wheel local undervoltage inhibit") (date "2026-11-05") (rev "0.8")) '
        '(lib_symbols) (embedded_fonts no))')
    root.append(s.parse(f'(sheet (at 160 50) (size 110 17) (stroke (width 0.254) (type default)) '
        f'(fill (color 0 0 0 0)) (uuid "{sheetid}") '
        '(property "Sheetname" "15_Wheel_Undervoltage" (at 160 48.73 0) (effects (font (size 1 1)) (justify left bottom))) '
        '(property "Sheetfile" "15_Wheel_Undervoltage.kicad_sch" (at 160 68.27 0) (effects (font (size 1 1)) (justify left top))) '
        f'(instances (project "Wheel" (path "/{rootid}" (page "7")))))'))

    resistor = s.library_symbol(LIB, 'Device:R')
    capacitor = s.library_symbol(LIB, 'Device:C')
    supervisor = s.library_symbol(LIB, 'Power_Supervisor:TPS3808DBV')
    gate = s.library_symbol(LIB, '74xGxx:74LVC1G08')
    rf = 'Resistor_SMD:R_1206_3216Metric'
    cf = 'Capacitor_SMD:C_1206_3216Metric'
    # New references start after all existing components, including manual route resistors.
    existing = {r for name in BOARDS for r in before[name]['components']}
    assert not existing.intersection({'U40','U41','R147','R148','R149','R150','C102','C103','C104'})
    specs = [
        (supervisor,'U40','TPS3808G01DBVR',(65,70),
            {'1':'WHEEL_VM_OK','2':'GND','3':'ACT_DRIVE_EN','4':None,'5':'WHEEL_VM_SENSE','6':'+3V3'},
            fieldset('TPS3808G01DBVR','Package_TO_SOT_SMD:SOT-23-6','https://www.ti.com/lit/ds/symlink/tps3808.pdf','Texas Instruments')),
        (gate,'U41','SN74LVC1G08DBVR',(170,70),
            {'1':'WHEEL_RUN_REQUESTED','2':'WHEEL_VM_OK','3':'GND','4':'WHEEL_RUN_EN','5':'+3V3'},
            fieldset('SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5','https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf','Texas Instruments')),
        (resistor,'R147','105k',(45,125),{'1':'ACT_5V','2':'WHEEL_VM_SENSE'},
            fieldset('TNPW1206105KBEEA',rf,'https://www.vishay.com/docs/28758/tnpw_e3.pdf','Vishay','0.1%, 25 ppm/K')),
        (resistor,'R148','10k',(90,125),{'1':'WHEEL_VM_SENSE','2':'GND'},
            fieldset('TNPW120610K0BEEA',rf,'https://www.vishay.com/docs/28758/tnpw_e3.pdf','Vishay','0.1%, 25 ppm/K')),
        (resistor,'R149','10k',(135,125),{'1':'+3V3','2':'WHEEL_VM_OK'},
            fieldset('RC1206FR-0710KL',rf,'https://pccomponents.com/datasheets/yageo-rc.pdf','YAGEO','1%, 0.25 W')),
        (resistor,'R150','100k',(180,125),{'1':'WHEEL_RUN_EN','2':'GND'},
            fieldset('RC1206FR-07100KL',rf,'https://pccomponents.com/datasheets/yageo-rc.pdf','YAGEO','1%, 0.25 W')),
        (capacitor,'C102','1nF/50V',(45,180),{'1':'WHEEL_VM_SENSE','2':'GND'},
            fieldset('CL31C102JBCNNNC',cf,'https://product.samsungsem.com/mlcc/CL31C102JBCNNN.do','Samsung Electro-Mechanics','C0G, 5%, 50 V')),
        (capacitor,'C103','100nF/50V',(100,180),{'1':'+3V3','2':'GND'},
            fieldset('CL31B104KBCNNNC',cf,'https://product.samsungsem.com/mlcc/CL31B104KBCNNN.do','Samsung Electro-Mechanics','X7R, 10%, 50 V')),
        (capacitor,'C104','100nF/50V',(155,180),{'1':'+3V3','2':'GND'},
            fieldset('CL31B104KBCNNNC',cf,'https://product.samsungsem.com/mlcc/CL31B104KBCNNN.do','Samsung Electro-Mechanics','X7R, 10%, 50 V')),
    ]
    for lib,ref,val,pos,nets,fields in specs:
        pos = tuple(round(v/1.27)*1.27 for v in pos)
        s.add_component(sheet,lib,ref,val,pos,nets,'Wheel',sheetpath,fields)
    s.text(sheet,'U40 senses local driver VM-to-GND; power from the existing host +3V3.\nCT is deliberately open: 12-28 ms recovery qualification. MR follows ACT_DRIVE_EN.\nU41 qualifies motor drive only; the supervisor does not gate U13 startup.\nNominal falling threshold: 0.405 V x (1 + 105k/10k) = 4.6575 V.\nThreshold/delay corners and physical validation are recorded in circuit-review.',20,215,'wheel-uv-explanation')
    s.write(rootpath,root)
    s.write(HERE/'wheel/15_Wheel_Undervoltage.kicad_sch',sheet)

    sync_boards()


def sync_boards():
    for name in ('Lower','Upper','Wheel'):
        comps,pins = export(name)
        board = p.LoadBoard(str(BOARDS[name]))
        fps = {f.GetReference(): f for f in board.GetFootprints()}
        for ref, comp in comps.items():
            if ref not in fps:
                footprint = comp.findtext('footprint')
                group, item = footprint.split(':')
                f = p.FootprintLoad(str(LIB/'footprints'/(group+'.pretty')),item)
                assert f is not None,footprint
                f.SetReference(ref)
                f.SetFPID(p.LIB_ID(group,item))
                f.SetPosition(xy(60,60))
                stamp = comp.find('tstamps').text.split()[0]
                path = comp.find('sheetpath').get('tstamps') + stamp
                f.SetPath(p.KIID_PATH(path))
                board.Add(f);fps[ref]=f
            f=fps[ref]
            f.SetValue(comp.findtext('value'))
            for prop in comp.findall('property'):
                if prop.get('name') not in ('Sheetname','Sheetfile'):
                    f.SetField(prop.get('name'),prop.get('value',''))
            f.SetField('Datasheet',comp.findtext('datasheet') or '')
            for field in f.GetFields():
                if field.GetName() not in ('Reference','Value'):
                    field.SetVisible(False)
            for pad in f.Pads():
                netname=pins.get((ref,pad.GetNumber()))
                if netname is None: continue
                net=board.FindNet(netname)
                if net is None:
                    net=p.NETINFO_ITEM(board,netname);board.Add(net)
                pad.SetNet(net)
        p.SaveBoard(str(BOARDS[name]),board)
    print('Circuit changes applied. New Wheel footprints require placement and routing.')


def place():
    import math
    import numpy as np
    from shapely.geometry import box, Point, LineString
    from shapely.ops import unary_union
    from assembly_spacing import envelope, active
    from export_quote import polygons
    placements = {}
    for name in ('Lower','Wheel'):
        path=BOARDS[name]
        checkpoint=WORK/(name+'-before-placement.kicad_pcb')
        if not checkpoint.exists():checkpoint.write_bytes(path.read_bytes())
        # Loading a detached snapshot loses its project design settings; saving
        # that board can overwrite the live project's rules with defaults.
        path.write_bytes(checkpoint.read_bytes())
        board=p.LoadBoard(str(path));fs={f.GetReference():f for f in board.GetFootprints()}
        before={r:(tuple(p.ToMM(f.GetPosition())),f.GetOrientationDegrees(),envelope(f)) for r,f in fs.items()}
        shape=p.SHAPE_POLY_SET();assert board.GetBoardPolygonOutlines(shape,False)
        material=unary_union(polygons(shape)).buffer(-.5)
        new={'U40','U41','R147','R148','R149','R150','C102','C103','C104'} if name=='Wheel' else set()
        critical = ({'C1':(51.25,23.91,0),'C3':(57.725,33.1,90),
            'C86':(46.5,49.51,0),'C83':(46.5,53.32,0),'C85':(46.5,57.13,0),'C84':(46.5,60.94,0)}
            if name=='Lower' else {'C47':(21.88,28,90),'C48':(33.11,28.8,90),
                'C49':(33.11,35,90),'C58':(27,11.2,0),'C57':(20.88,11.12,180),
                'C56':(21.215,16.08,270),
                'C46':(21.99,34.11,270),
                'U40':(58,29.5,180),'C103':(58,24.9,0),'R147':(51.9,25.1,0),
                'R148':(58,34.1,0),'C102':(52,29.5,180),'R149':(58,38.3,0),
                'U41':(43.5,57.5,0),'C104':(43.5,53.1,0),'R150':(43.5,61.9,0)})
        pending=set(new)-set(critical)
        # First reserve the critical capacitor positions, then displace only
        # passive parts that obstruct them. ICs/connectors remain fixed.
        for r,(x,y,a) in critical.items():fs[r].SetPosition(xy(x,y));fs[r].SetOrientationDegrees(a)
        for r in critical:
            env=envelope(fs[r])
            assert material.covers(env),r
            for q,f in fs.items():
                if q in critical or q in new or not active(f):continue
                if env.distance(envelope(f)) < 2.0:
                    assert q[0] in 'RCLD', (name,r,'fixed obstruction',q)
                    pending.add(q)
        occupied={r:envelope(f) for r,f in fs.items() if active(f) and r not in pending}
        anchors={'U40':(4,26),'U41':(45,53),'R147':(4,21),'R148':(4,31),
            'R149':(9,31),'R150':(50,53),'C102':(-1,26),'C103':(4,22),'C104':(45,49)}
        order=sorted(pending,key=lambda r:(r in new,r not in ('U40','U41'),r))
        for r in order:
            f=fs[r];ox,oy=anchors.get(r,before[r][0])
            xs=np.arange(ox-25,ox+25.01,.25);ys=np.arange(oy-25,oy+25.01,.25)
            xx,yy=np.meshgrid(xs,ys);xx=xx.ravel();yy=yy.ravel()
            candidates=[]
            for angle in (0,90,180,270):
                f.SetPosition(xy(0,0));f.SetOrientationDegrees(angle)
                x0,y0,x1,y1=envelope(f).bounds
                good=np.ones(len(xx),dtype=bool)
                for env in occupied.values():
                    a,b,c,d=env.bounds
                    dx=np.maximum(np.maximum(a-(xx+x1),(xx+x0)-c),0)
                    dy=np.maximum(np.maximum(b-(yy+y1),(yy+y0)-d),0)
                    good &= dx*dx+dy*dy >= 2.02**2
                score=(xx-ox)**2+(yy-oy)**2 + (0 if angle==before[r][1] else .01)
                for i in np.flatnonzero(good)[np.argsort(score[good])]:
                    if material.covers(box(xx[i]+x0,yy[i]+y0,xx[i]+x1,yy[i]+y1)):
                        candidates.append((float(score[i]),float(xx[i]),float(yy[i]),angle));break
            assert candidates,(name,r,'no legal placement')
            _,x,y,angle=min(candidates);f.SetPosition(xy(x,y));f.SetOrientationDegrees(angle)
            occupied[r]=envelope(f)
        moved={r for r,f in fs.items() if r in new or (tuple(p.ToMM(f.GetPosition())),f.GetOrientationDegrees())!=before[r][:2]}
        areas=unary_union([envelope(fs[r]).buffer(.25) for r in moved]+[before[r][2].buffer(.25) for r in moved-new])
        if name=='Wheel':
            # U22.3 was renamed; cut its old escape rather than renaming the
            # already routed, shared WHEEL_RUN_EN distribution.
            pad=next(q for q in fs['U22'].Pads() if q.GetNumber()=='3')
            areas=unary_union([areas,Point(p.ToMM(pad.GetPosition())).buffer(.35)])
        removed=0
        for t in list(board.GetTracks()):
            geom=Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2) if isinstance(t,p.PCB_VIA) else LineString([p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2)
            if areas.intersects(geom):board.Remove(t);t.thisown=False;removed+=1
        allenv={r:envelope(f) for r,f in fs.items() if active(f)}
        closest=min((a.distance(b),r,q) for r,a in allenv.items() for q,b in allenv.items() if r<q)
        assert closest[0]>=1.99999,(name,closest)
        placements[name]={'moved':{r:{'from':list(before[r][0]),'to':list(p.ToMM(fs[r].GetPosition())),
            'angle':fs[r].GetOrientationDegrees()} for r in sorted(moved)},'removed_copper_items':removed,'minimum_gap_mm':closest}
        board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones());p.SaveBoard(str(path),board)
        print(name,json.dumps(placements[name]),flush=True)
    (EVIDENCE/'placement-changes.json').write_text(json.dumps(placements,indent=2)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['circuit','sync','place'])
    args=parser.parse_args()
    {'circuit':circuit,'sync':sync_boards,'place':place}[args.action]()
