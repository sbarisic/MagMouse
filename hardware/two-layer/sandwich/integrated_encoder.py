"""One-time AS5048A migration and independent acceptance checks. KiCad Python.

Saved schematics and boards are authoritative; the migration refuses replay.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import argparse, copy, hashlib, json, shutil, subprocess, sys
from pathlib import Path
import pcbnew as p
from route_main import HERE, ROOT, CLI, xy
sys.path.insert(0, str(ROOT/'hardware/common'))
sys.path.insert(0, str(ROOT/'build/two-layer/python'))
import schematic_io as s
from passive_buttons import symbol, disconnect, pin_net
from circuit_fixes import properties
from netlist import export

WORK=ROOT/'build/sandwich/integrated-encoder'
LIB=CLI.parent.parent/'share/kicad'
BOARDS={n:HERE/n.lower()/(n+'.kicad_pcb') for n in ('Lower','Upper','Wheel')}
REMOVED={'Lower':{f'TP{i}' for i in (*range(1,2),*range(4,11),*range(16,34),*range(40,44))},
         'Upper':{f'TP{i}' for i in (2,3,*range(11,16))},'Wheel':set()}
CHANGED={('U28','1'):'RGB_5V',('U28','6'):'ENC_5V',('C63','1'):'RGB_5V',
         ('R125','2'):'ENC_5V',('J6','1'):'ENC_5V',('C55','1'):'ENC_5V'}
NEW_PINS={'1':'ENC_5V','2':'GND','3':'ENC_5V','4':'unconnected-(U42-NC-Pad4)','5':'ENC_3V3'}
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def metadata():
    """Sync field text without the KiCad 10 SWIG GetField ownership ambiguity."""
    for name,path in BOARDS.items():
        comps,_=export(path.with_suffix('.kicad_sch'),WORK/(name+'.xml'))
        tree=s.parse(path.read_text(encoding='utf-8'))
        for footprint in s.allof(tree,'footprint'):
            ref=s.props(footprint).get('Reference')
            if ref not in comps:continue
            comp=comps[ref]
            values={q.get('name'):q.get('value','') for q in comp.findall('property')
                    if q.get('name') not in ('Sheetname','Sheetfile')}
            values['Datasheet']=comp.findtext('datasheet') or ''
            properties(footprint,values)
        s.write(path,tree)
        board=p.LoadBoard(str(path));p.SaveBoard(str(path),board)

def schematic():
    assert len(REMOVED['Lower'])==30 and len(REMOVED['Upper'])==7
    assert not (WORK/'baseline.json').exists(), 'Migration already started; do not replay'
    WORK.mkdir(parents=True,exist_ok=True)
    baseline={}
    for name,path in BOARDS.items():
        dest=WORK/'original'/name
        shutil.copytree(path.parent,dest)
        b=p.LoadBoard(str(path))
        actual={f.GetReference() for f in b.GetFootprints() if f.IsFlipped() and f.GetReference().startswith('TP')}
        assert actual==REMOVED[name]
        baseline[name]={'sha256':sha(path),'components':{f.GetReference():{
            'value':f.GetValue(),'xy':list(p.ToMM(f.GetPosition())),
            'angle':f.GetOrientationDegrees(),'pads':{q.GetNumber():q.GetNetname() for q in f.Pads()}}
            for f in b.GetFootprints()}}
    shutil.copytree(HERE/'main-circuit',WORK/'original/Main')
    (WORK/'baseline.json').write_text(json.dumps(baseline,indent=2)+'\n')
    # Resolve the installed symbol's inheritance, preserving its actual pinout.
    library=s.parse((LIB/'symbols/Regulator_Linear.kicad_sym').read_text(encoding='utf-8'))
    symbols={n[1]:n for n in s.allof(library,'symbol')}
    child=symbols['TLV75533PDBV']; parent=copy.deepcopy(symbols[s.get(child,'extends')[1]])
    old=parent[1]; parent[1]='Regulator_Linear:TLV75533PDBV'
    for sub in s.allof(parent,'symbol'): sub[1]=sub[1].replace(old,'TLV75533PDBV')
    for prop in s.allof(child,'property'):
        target=next((a for a in s.allof(parent,'property') if a[1]==prop[1]),None)
        if target is not None: parent.remove(target)
        parent.append(copy.deepcopy(prop))
    for folder,project in [('lower','Lower'),('upper','Upper'),('main-circuit','Main')]:
        root=s.parse((HERE/folder/(project+'.kicad_sch')).read_text(encoding='utf-8'))
        removed=REMOVED.get(project,REMOVED['Lower']|REMOVED['Upper'])
        for path in (HERE/folder).glob('*.kicad_sch'):
            raw=path.read_text(encoding='utf-8'); tree=s.parse(raw.replace('CS_MA735','CS_ENCODER'))
            modified=raw!=raw.replace('CS_MA735','CS_ENCODER')
            refs={s.props(n).get('Reference') for n in s.allof(tree,'symbol')}
            for ref in refs & removed:
                node,positions=symbol(tree,ref)
                for pos in positions.values(): disconnect(tree,pos)
                tree.remove(node); modified=True
            for (ref,pin),net in CHANGED.items():
                if ref in refs: pin_net(tree,ref,pin,net); modified=True
            if 'U3' in refs:
                for pin in ('39','40'):pin_net(tree,'U3',pin,None)
                modified=True
            for ref in ('C55','C64'):
                if ref in refs:
                    node,_=symbol(tree,ref)
                    properties(node,{'Value':'1uF/50V','MPN':'CL31B105KBHNNNE','Manufacturer':'Samsung Electro-Mechanics',
                        'Datasheet':'https://product.samsungsem.com/mlcc/CL31B105KBHNNN.do',
                        'LCSC':'','JLCPCB Part #':'','Checked':'2026-11-22',
                        'Sourcing Status':'1 uF 50 V X7R 1206; assembly stock unverified'})
                    modified=True
            if 'J6' in refs:
                node,_=symbol(tree,'J6');properties(node,{'Value':'GB1806 AS5048A encoder wires'})
            if path.stem=='12_Wheel_Feedback':
                sheet=next(n for n in s.allof(root,'sheet') if s.props(n).get('Sheetfile')==path.name)
                instance_path='/'+s.get(root,'uuid')[1]+'/'+s.get(sheet,'uuid')[1]
                s.add_component(tree,parent,'U42','TLV75533PDBVR',(180.34,180.34),
                    {**NEW_PINS,'4':None},project,instance_path,{
                    'Footprint':'Package_TO_SOT_SMD:SOT-23-5','MPN':'TLV75533PDBVR',
                    'Manufacturer':'Texas Instruments','Datasheet':'https://www.ti.com/lit/ds/symlink/tlv755p.pdf',
                    'LCSC':'','JLCPCB Part #':'','Checked':'2026-11-22',
                    'Sourcing Status':'Manufacturer specification checked; assembly stock unverified'})
                cap, _ = symbol(tree,'C64')
                caplib=next(n for n in s.allof(s.get(tree,'lib_symbols'),'symbol') if n[1]==s.get(cap,'lib_id')[1])
                s.add_component(tree,caplib,'C105','100nF/50V',(220.98,180.34),
                    {'1':'ENC_3V3','2':'GND'},project,instance_path,{
                    'Footprint':'Capacitor_SMD:C_1206_3216Metric','MPN':'CC1206KRX7R9BB104',
                    'Manufacturer':'YAGEO','Datasheet':'https://www.yageogroup.com/download/specsheet/CC1206KRX7R9BB104',
                    'LCSC':'','JLCPCB Part #':''})
                for note in s.allof(tree,'text'):
                    if any(w in note[1] for w in ('MA735','encoder','Encoder','ENC_3V3')):
                        note[1]='GB1806 integrated AS5048A: J6.1=ENC_5V; 2/4/7=GND; 3=CLK; 5=MOSI; 6=CSn; 8=MISO.\nU28 switches regulated RGB_5V from U33 with HALL_EN. U42 supplies only the local 3.3 V SPI buffer.\nC55/C64: 1 uF LDO input/output. Motor encoder PWM is unused. No standalone encoder PCB.'
                modified=True
            if modified:s.write(path,tree)
    partition=json.loads((HERE/'partition.json').read_text())
    for key in ('component_ownership','component_sheets'):
        if key in partition:
            for ref in REMOVED['Lower']|REMOVED['Upper']:partition[key].pop(ref,None)
    partition['component_ownership']['U42']='Lower'
    partition['component_sheets']['U42']='12_Wheel_Feedback'
    partition['component_ownership']['C105']='Lower'
    partition['component_sheets']['C105']='12_Wheel_Feedback'
    (HERE/'partition.json').write_text(json.dumps(partition,indent=2)+'\n')
    print('Schematics migrated',flush=True)

def pcb():
    from assembly_spacing import envelope,active
    from shapely.geometry import Point,LineString,box
    from shapely.ops import unary_union
    from board_geometry import polygons
    import numpy as np
    for name,path in BOARDS.items():
        if name=='Wheel':continue
        b=p.LoadBoard(str(path)); assert not any(f.GetReference()=='U42' for f in b.GetFootprints())
        comps,pins=export(path.with_suffix('.kicad_sch'),WORK/(name+'.xml'))
        # Rename the entire net, retaining every existing route and pad.
        net=b.FindNet('CS_MA735')
        if net:net.SetNetname('CS_ENCODER')
        fs={f.GetReference():f for f in b.GetFootprints()}
        for ref in REMOVED[name]:
            f=fs.pop(ref);b.Remove(f);f.thisown=False
        changed_regions=[]
        for ref,comp in comps.items():
            if ref not in fs:
                group,item=comp.findtext('footprint').split(':')
                f=p.FootprintLoad(str(LIB/'footprints'/(group+'.pretty')),item)
                f.SetReference(ref);f.SetFPID(p.LIB_ID(group,item));b.Add(f);fs[ref]=f
                f.SetPath(p.KIID_PATH(comp.find('sheetpath').get('tstamps')+comp.findtext('tstamps').split()[0]))
                f.Reference().SetVisible(False);f.Value().SetVisible(False)
            f=fs[ref];f.SetValue(comp.findtext('value'))
            for prop in comp.findall('property'):
                key=prop.get('name')
                if key in ('Sheetname','Sheetfile'):continue
                field=next((a for a in f.GetFields() if a.GetName()==key),None)
                if field is None:
                    field=p.PCB_FIELD(f,p.FIELD_T_USER,key);f.Add(field)
                field.SetText(prop.get('value',''))
            for field in f.GetFields():
                if field.GetName() not in ('Reference','Value'):field.SetVisible(False)
            for pad in f.Pads():
                netname=pins.get((ref,pad.GetNumber()))
                if not netname:continue
                if ref not in ('U42','C105') and netname!=pad.GetNetname():
                    changed_regions.append(Point(p.ToMM(pad.GetPosition())).buffer(.65))
                net=b.FindNet(netname)
                if net is None:net=p.NETINFO_ITEM(b,netname);b.Add(net)
                pad.SetNet(net)
        if name=='Lower':
            for t in list(b.GetTracks()):
                if t.GetNetname() in ('UART_TX','UART_RX'):
                    b.Remove(t);t.thisown=False
            moving={'U42','C55','C64','C105'}
            changed_regions += [envelope(fs[r]).buffer(.2) for r in ('C55','C64')]
            # Jointly checked cluster: both LDO capacitors within 5 mm pin distance;
            # C105 preserves the former U29 bypass location.
            for ref,(x,y,angle) in {'U42':(9,31.5,180),'C55':(9.5,37,270),
                    'C64':(5,36.5,270),'C105':(17.625,26.8,90)}.items():
                fs[ref].SetPosition(xy(x,y));fs[ref].SetOrientationDegrees(angle)
                changed_regions.append(envelope(fs[ref]).buffer(.2))
            env={r:envelope(f) for r,f in fs.items() if active(f)}
            assert min(a.distance(c) for r,a in env.items() for q,c in env.items() if r<q)>=1.99999
            area=unary_union(changed_regions)
            for t in list(b.GetTracks()):
                geom=(Point(p.ToMM(t.GetPosition())).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2)
                    if isinstance(t,p.PCB_VIA) else LineString([p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2))
                if area.intersects(geom):
                    assert t.GetNetname() not in ('USB_DP','USB_DM','MCU_USB_DP','MCU_USB_DM'), 'USB protected'
                    b.Remove(t);t.thisown=False
        b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
        project=json.loads(path.with_suffix('.kicad_pro').read_text().replace('CS_MA735','CS_ENCODER'))
        path.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
        print(name,'PCB migrated',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['schematic','pcb','metadata']);a=parser.parse_args()
    {'schematic':schematic,'pcb':pcb,'metadata':metadata}[a.action]()
