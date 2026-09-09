# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify exported power connectivity, package pads and hardware enable truth tables.
Run export_review.py first. These checks do not simulate analog or USB behavior.
"""
import argparse
import itertools
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path(__file__).resolve().parent

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--footprints', type=Path, help='KiCad standard footprint directory')
    args = ap.parse_args()
    base = args.footprints
    if base is None:
        candidates = [Path(os.environ.get('KICAD10_FOOTPRINT_DIR', '')),
                      Path(os.environ.get('LOCALAPPDATA', '.')) / 'Programs/KiCad/10.0/share/kicad/footprints',
                      Path('/usr/share/kicad/footprints')]
        base = next((p for p in candidates if (p / 'Device.pretty').is_dir() or (p / 'Resistor_SMD.pretty').is_dir()), None)
    if base is None:
        ap.error('Supply --footprints PATH for the KiCad standard libraries')
    xml = ET.parse(ROOT / 'build/kicad-review/netlist.xml').getroot()
    components = {c.get('ref'): c for c in xml.findall('./components/comp')}
    source_refs = set()
    for p in PROJECT.glob('*.kicad_sch'):
        source_refs.update(re.findall(r'\(property\s+"Reference"\s+"([A-Z]+\d+)"', p.read_text(encoding='utf-8')))
    errors = []
    def check(condition, message):
        if not condition:
            errors.append(message)
    check(source_refs == set(components), f'Source/export reference mismatch: {sorted(source_refs ^ set(components))}')
    assigned = 0
    for ref, c in components.items():
        fp = c.findtext('footprint', '')
        if ':' not in fp:
            errors.append(f'{ref}: missing footprint'); continue
        library, name = fp.split(':', 1)
        path = (PROJECT if library == 'MagMouse' else base) / (library + '.pretty') / (name + '.kicad_mod')
        if not path.is_file():
            errors.append(f'{ref}: missing footprint {path}'); continue
        pads = set(re.findall(r'\(pad\s+"([^"]+)"', path.read_text(encoding='utf-8')))
        pins = {p.get('num') for p in c.findall('./units/unit/pins/pin')}
        check(pins <= pads, f'{ref}: symbol pins without footprint pads {sorted(pins-pads)}')
        assigned += 1
    nets = {n.get('name'): {(p.get('ref'), p.get('pin')) for p in n.findall('node')} for n in xml.findall('./nets/net')}
    pin_net = {p: net for net, pins in nets.items() for p in pins}
    expected = {}
    def device(ref, mapping):
        expected.update({(ref, str(pin)): net for pin, net in mapping.items()})
    device('J1', {'A5':'USB_CC1','B5':'USB_CC2','A4':'VBUS_USB','B4':'VBUS_USB','A6':'USB_DP','B6':'USB_DP','A7':'USB_DM','B7':'USB_DM'})
    device('U11', {1:'USB_CC1',2:'USB_CC2',3:'GND',4:'CC_VBUS_DET',7:'CC_OUT1',8:'CC_OUT2',10:'GND',11:'GND',12:'+3V3'})
    device('U12', {1:'USB_UVLO',2:'USB_OVLO',4:'USB_FAULT_N',5:'VBUS_USB',6:'PWR_5V',7:'USB_DVDT',8:'GND',9:'USB_ILM'})
    device('C88', {1:'PWR_5V',2:'GND'})
    device('C89', {1:'PWR_5V',2:'GND'})
    device('U13', {1:'ACT_UVLO',2:'ACT_OVLO',4:'ACT_FAULT_N',5:'PWR_5V',6:'ACT_5V',7:'ACT_DVDT',8:'GND',9:'ACT_ILM'})
    device('U2', {1:'GND',2:'PWR_5V',3:'PWR_5V',4:'GND',5:'GND',6:'+3V3',7:'BUCK_SW',8:'LOGIC_PG',9:'GND'})
    device('L1', {1:'BUCK_SW',2:'+3V3'})
    device('U3', {5:'VBUS_PRESENT_N',18:'CC_OUT1',19:'CC_OUT2',20:'ACT_REQ',21:'ACT_HEARTBEAT',22:'SENS_REQ',23:'MCU_USB_DM',24:'MCU_USB_DP',45:'MCU_EN'})
    device('U15', {1:'GND',2:'ACT_HEARTBEAT',3:'ARM_VALID',4:'GND',5:'ACT_PERMIT',6:'WD_CEXT',7:'WD_RCEXT',8:'+3V3'})
    device('D1', {1:'VBUS_USB',2:'GND'}); device('D2', {1:'ACT_5V',2:'GND'})
    device('D3', {1:'ACT_UVLO',3:'ACT_DRIVE_EN'}); device('D4', {1:'ACT_VMON',3:'+3V3'})
    device('Q1', {1:'SOURCE_OK',2:'GND',3:'ILM_MED_D'});device('Q2', {1:'SOURCE_3A',2:'GND',3:'ILM_HIGH_D'})
    device('Q3', {1:'VBUS_GATE',2:'GND',3:'VBUS_PRESENT_N'})
    device('U19', {1:'USB_IMON_BUF',2:'GND',3:'USB_ILM',4:'USB_IMON_BUF',5:'+3V3'})
    device('U20', {1:'USB_CC1',2:'USB_CC2',3:'GND'})
    for ref, a, b in [('R25','VBUS_USB','CC_VBUS_DET'),('R28','LOGIC_PG','MCU_EN'),('R44','USB_FAULT_N','MCU_EN'),('R45','ACT_FAULT_N','MCU_EN'),('R46','+3V3','WD_RCEXT'),('C27','WD_RCEXT','WD_CEXT'),('R56','USB_ILM','ILM_BASE_1'),('R57','ILM_BASE_1','ILM_BASE_2'),('R58','ILM_BASE_2','GND'),('R59','USB_ILM','ILM_MED_D'),('R60','USB_ILM','ILM_HIGH_D'),('R61','USB_ILM','ILM_HIGH_D'),('R65','VBUS_USB','VBUS_GATE'),('R66','VBUS_GATE','GND'),('R67','ACT_5V','ACT_VMON'),('R68','ACT_VMON','GND'),('R69','ACT_5V','GND')]:
        device(ref, {1:a,2:b})
    for i, tag in enumerate('LMR'):
        device(f'U{i+4}', {1:f'BTN_{tag}_ISENSE',2:f'BTN_{tag}_IN2',3:f'BTN_{tag}_IN1',4:f'BTN_{tag}_VREF',5:'ACT_5V',6:f'BTN_{tag}_COIL_P',7:'GND',8:f'BTN_{tag}_COIL_N',9:'GND'})
        device(f'U{i+7}', {1:'+3V3',2:'GND',3:'HALL_EN',4:f'HALL_{tag}',5:'GND'})
        device('U3', {8+2*i:f'BTN_{tag}_CMD1',9+2*i:f'BTN_{tag}_CMD2'})
        device(f'J{i+2}', {1:f'BTN_{tag}_COIL_P',2:f'BTN_{tag}_COIL_N'})
    device('U10', {15:'HALL_L',16:'HALL_M',1:'HALL_R',2:'BTN_L_ISENSE',3:'BTN_M_ISENSE',4:'BTN_R_ISENSE',5:'USB_IMON_ADC',6:'ACT_VMON',7:'+3V3',10:'+3V3',9:'GND',17:'GND',8:'ADC_DECAP',11:'ADC_CS',13:'SPI_SCLK',14:'SPI_MOSI',12:'SPI_MISO'})
    for pin, net in expected.items():
        check(pin_net.get(pin) == net, f'{pin}: expected {net}, got {pin_net.get(pin)}')
    for pin in [('U11','5'),('U12','10'),('U13','10')]:
        check(pin_net.get(pin, '').startswith('unconnected-'), f'{pin}: intentional NC was connected')
    check(not any('PENDING' in n for n in nets), 'A pending power net remains')
    for ref in ['U12','U13']:
        check(components[ref].findtext('value') == 'TPS259470LRPWR', f'{ref}: wrong eFuse variant')
    check(components['D1'].findtext('value') == 'SMBJ12A', 'Wrong input TVS')
    check(components['D2'].findtext('value') == 'SMBJ6.0A', 'Wrong actuator TVS')
    # Evaluate actual netlist gate connections for every arm/reset/source/command combination.
    def net(ref, pin): return pin_net[(ref, str(pin))]
    gatepins = [(1,2,3),(4,5,6),(9,10,8),(12,13,11)]
    cases = 0
    for cc1, cc2, req, sensors, reset, permit in itertools.product([False,True], repeat=6):
        for command_bits in itertools.product([False,True], repeat=6):
            state = {'GND':False,'+3V3':True,'CC_OUT1':cc1,'CC_OUT2':cc2,'ACT_REQ':req,'SENS_REQ':sensors,'MCU_EN':reset,'ACT_PERMIT':permit}
            for name, value in zip([f'BTN_{t}_CMD{i}' for t in 'LMR' for i in [1,2]], command_bits):state[name]=value
            for _ in range(6):
                for a,y in [(1,6),(3,4)]:
                    if net('U14',a) in state:state[net('U14',y)]=not state[net('U14',a)]
                for ref in ['U16','U17','U18']:
                    for a,b,y in gatepins:
                        if net(ref,a) in state and net(ref,b) in state:state[net(ref,y)] = state[net(ref,a)] and state[net(ref,b)]
            enabled = (not cc1) and req and sensors and reset and permit
            check(state.get('ACT_DRIVE_EN') == enabled, f'Enable truth table failed: {cc1,cc2,req,sensors,reset,permit}')
            check(state.get('HALL_EN') == (sensors and reset), 'Hall enable does not respect reset/request')
            for name, value in zip([f'BTN_{t}_IN{i}' for t in 'LMR' for i in [1,2]],command_bits):
                check(state.get(name) == (value and enabled), f'{name}: unsafe or incorrect gate output')
            check(state.get('SOURCE_3A') == (not cc1 and not cc2), '3 A selection decoding failed')
            cases += 1
    def resistance(ref):
        value=components[ref].findtext('value');return float(value.rstrip('kR')) * (1000 if value.endswith('k') else 1)
    rbase=sum(resistance(r) for r in ['R56','R57','R58'])
    conductances=[1/rbase,1/rbase+1/resistance('R59'),1/rbase+1/resistance('R59')+1/resistance('R60')+1/resistance('R61')]
    limits=[3334*g for g in conductances]
    # Conservative screening envelope, not a replacement for the manufacturer's model or measurements.
    check(limits[1]*1.15/0.99 < 1.5, '1.5 A source has no fault-limit tolerance margin')
    check(limits[2]*1.10/0.99 < 3.0, '3 A source has no fault-limit tolerance margin')
    report={'critical_pin_checks':len(expected),'footprints_checked':assigned,'logic_truth_table_cases':cases,
            'nominal_input_fault_limits_A':limits,'adc_voltage_scale':resistance('R68')/(resistance('R67')+resistance('R68')),
            'scope':'Static connectivity, package-pad and Boolean checks only; analog, USB-state and thermal acceptance require bench tests.',
            'errors':errors}
    (ROOT/'build/kicad-review/power-checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 1 if errors else 0

if __name__=='__main__':
    raise SystemExit(main())
