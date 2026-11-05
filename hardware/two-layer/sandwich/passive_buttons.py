"""Remove button actuation from the active stacked variant; retain Hall sensing.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import copy
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
import pcbnew as p

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'hardware/common'))
import schematic_io as s

DRIVER_REFS={'U4','U5','U6','J2','J3','J4',
             *[f'R{i}' for i in (8,9,10,11,12,14,15,16,17,18,20,21,22,23,24)],
             *[f'C{i}' for i in range(7,16)]}
REMOVED=DRIVER_REFS|{'U17','C30',*[f'R{i}' for i in range(50,56)]}
REWIRED={'U3':{str(i) for i in range(8,14)},'U10':{'2','3','4'},'U18':{'1','2','3','4','5','6'}}


def export_netlist(output):
    cli=Path(sys.executable).with_name('kicad-cli.exe')
    subprocess.run([str(cli),'sch','export','netlist','--format','kicadxml','-o',str(output),
                    str(HERE/'main-circuit/Main.kicad_sch')],check=True)
    xml=ET.parse(output).getroot()
    refs={c.get('ref') for c in xml.findall('./components/comp')}
    mapping={(n.get('ref'),n.get('pin')):net.get('name')
             for net in xml.findall('./nets/net') for n in net.findall('node')}
    return refs,mapping


def symbol(tree,ref):
    instance=next(n for n in s.allof(tree,'symbol') if s.props(n).get('Reference')==ref)
    lib=next(n for n in s.allof(s.get(tree,'lib_symbols'),'symbol') if n[1]==s.get(instance,'lib_id')[1])
    return instance,s.pin_positions(instance,lib)


def disconnect(tree,position):
    ends=set()
    for wire in list(s.allof(tree,'wire')):
        pts={tuple(map(float,n[1:])) for n in s.allof(s.get(wire,'pts'),'xy')}
        if position in pts:ends.update(pts);tree.remove(wire)
    for label in list(s.allof(tree,'global_label')):
        if tuple(map(float,s.get(label,'at')[1:3])) in ends:tree.remove(label)
    for nc in list(s.allof(tree,'no_connect')):
        if tuple(map(float,s.get(nc,'at')[1:3]))==position:tree.remove(nc)


def pin_net(tree,ref,pin,net):
    _,positions=symbol(tree,ref);x,y=positions[pin]
    disconnect(tree,(x,y))
    if net is None:
        tree.append(s.parse(f'(no_connect (at {x} {y}) (uuid "{s.ident("passive-"+ref+pin)}"))'))
    else:
        # A label directly at the symbol pin avoids a dangling old sense stub.
        tree.append(s.parse(f'(global_label "{net}" (shape bidirectional) (at {x} {y} 0) '
                            f'(effects (font (size 1 1)) (justify left)) (uuid "{s.ident("passive-"+ref+pin)}"))'))


def revise():
    scratch=ROOT/'build/sandwich';scratch.mkdir(exist_ok=True)
    before_refs,before=export_netlist(scratch/'Main-before-passive.xml')
    if not (before_refs&REMOVED):
        print('Passive Hall buttons already applied');return
    assert before_refs&REMOVED==REMOVED
    for filename in ('03_Buttons','06_Actuator_Interlock','02_MCU','04_Sensing','08_Actuator_Rail'):
        path=HERE/'main-circuit'/(filename+'.kicad_sch')
        backup=scratch/'before-passive-buttons'/path.name
        backup.parent.mkdir(exist_ok=True)
        if not backup.exists():backup.write_bytes(path.read_bytes())
        tree=s.parse(path.read_text(encoding='utf-8'))
        if filename=='03_Buttons':
            tree[:]=[n for n in tree if not isinstance(n,list) or n[0] not in ('symbol','wire','global_label','no_connect','text')]
            s.get(tree,'lib_symbols')[:]=[s.Atom('lib_symbols')]
            s.get(s.get(tree,'title_block'),'title')[1]='MagMouse - passive plastic buttons'
            s.text(tree,'Plastic click mechanism and passive return.\nOne sensing magnet per button; Hall sensors U7/U8/U9 remain on sheet 04.\nNo button coils, actuator magnets, driver ICs or coil wiring.',20,30,'passive-button-sheet')
        elif filename=='06_Actuator_Interlock':
            for ref in sorted(REMOVED-DRIVER_REFS):
                instance,positions=symbol(tree,ref)
                for pos in positions.values():disconnect(tree,pos)
                tree.remove(instance)
            for pin in ('1','2','4','5'):pin_net(tree,'U18',pin,'GND')
            for pin in ('3','6'):pin_net(tree,'U18',pin,None)
            for text in s.allof(tree,'text'):
                if '~10 ms' in text[1]:
                    text[1]='Wheel drive permit: source qualification, ACT_REQ, HALL_EN and heartbeat.\nU18 gate 3 retains HALL_EN = SENS_REQ AND MCU_EN.\nUnused U18 inputs are grounded; unused outputs are unconnected.\nButton actuation and its command gates have been removed.'
        elif filename=='02_MCU':
            for pin in REWIRED['U3']:pin_net(tree,'U3',pin,None)
            for note in s.allof(tree,'text'):
                if 'GPIO allocation:' in note[1]:
                    note[1]=note[1].replace('38 assigned + GPIO46 boot-low spare','32 assigned + GPIO4..9 unused + GPIO46 boot-low spare').replace('MCPWM1: six independent button commands','MCPWM1: unallocated')
            s.text(tree,'Passive-button revision: GPIO4..9 are unused (module pads 8..13).\nThe plastic mechanism produces the click; Hall readings produce button events.',20,245,'passive-button-gpio')
        elif filename=='04_Sensing':
            for pin in REWIRED['U10']:pin_net(tree,'U10',pin,'GND')
            for text in s.allof(tree,'text'):
                if 'AIN0-2:' in text[1]:
                    text[1]='AIN0-2: Hall position. AIN3-5: grounded unused channels.\nAIN6: input current. AIN7: wheel actuator rail voltage.\nHall sensors and their supply/enable circuitry are retained.\nButtons use passive plastic click mechanisms and sensing magnets.'
        elif filename=='08_Actuator_Rail':
            for text in s.allof(tree,'text'):
                if 'ACT capacitance:' in text[1]:
                    text[1]='ACT capacitance: 40 uF shared wheel-rail storage here; button driver storage removed.\nU13 reverse blocking, D2 clamp and R69 discharge remain for the motorized wheel.\nD1 protects the upstream supply. The autonomous wheel brake remains on Wheel.\nButton mechanics and Hall sensing do not use ACT_5V.'
        s.write(path,tree)
    after_refs,after=export_netlist(scratch/'Main-passive.xml')
    assert after_refs==before_refs-REMOVED
    allowed={(ref,pin) for ref,pins in REWIRED.items() for pin in pins}
    assert {k:v for k,v in before.items() if k[0] not in REMOVED and k not in allowed}=={
        k:v for k,v in after.items() if k not in allowed}
    assert not any(net.startswith('BTN_') for net in after.values())
    for pin in ('2','3','4'):assert after['U10',pin]=='GND'
    for pin in ('1','2','4','5'):assert after['U18',pin]=='GND'
    assert after['U18','8']=='HALL_EN' and after['U18','9']=='SENS_REQ' and after['U18','10']=='MCU_EN'
    for ref,net in [('U7','HALL_L'),('U8','HALL_M'),('U9','HALL_R')]:assert after[ref,'4']==net
    report={'removed_references':sorted(REMOVED),'removed_count':len(REMOVED),
            'retained_main_components':len(after_refs),'hall_sensing_retained':True,
            'shared_sensor_enable_and_wheel_interlock_retained':True,
            'unrelated_pin_connections_unchanged':True,
            'rewired_pins':{ref:{pin:after.get((ref,pin),'') for pin in sorted(pins)} for ref,pins in REWIRED.items()}}
    (HERE/'passive-buttons.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


def expected_inventory(original,netmap):
    result={ref:copy.deepcopy(data) for ref,data in original.items() if ref not in REMOVED}
    for ref,pins in REWIRED.items():
        result[ref]['pads']=sorted((pin,netmap.get((ref,pin),'') if pin in pins else net)
                                  for pin,net in result[ref]['pads'])
    return result


def update_pads(board,netmap):
    for f in board.GetFootprints():
        ref=f.GetReference()
        for pad in f.Pads():
            pin=pad.GetNumber()
            if pin not in REWIRED.get(ref,set()):continue
            name=netmap.get((ref,pin),'')
            if not name:pad.SetNetCode(0);continue
            net=board.FindNet(name)
            if net is None:
                net=p.NETINFO_ITEM(board,name);board.Add(net)
            pad.SetNet(net)


if __name__=='__main__':revise()
