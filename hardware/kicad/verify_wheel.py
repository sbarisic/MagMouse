# SPDX-License-Identifier: GPL-3.0-or-later
"""Check exported wheel wiring, shutdown logic and provisional brake arithmetic.

This is a static review, not motor, power-ramp, firmware or thermal simulation.
See WHEEL_REVIEW.md for datasheet bounds and measurements still required.
"""
import argparse
import itertools
import json
import math
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--netlist', type=Path, default=ROOT / 'build/kicad-review/netlist.xml')
    parser.add_argument('--encoder-netlist', type=Path, default=ROOT / 'build/encoder-review/netlist.xml')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/kicad-review/wheel-checks.json')
    args = parser.parse_args()
    xml = ET.parse(args.netlist).getroot()
    encoder = ET.parse(args.encoder_netlist).getroot()
    main_refs = {c.get('ref') for c in xml.findall('./components/comp')}
    encoder_refs = {c.get('ref') for c in encoder.findall('./components/comp')}
    # Shared net names describe the wired interface. verify_encoder.py checks
    # both physical connectors and the harness mapping independently.
    for comp in encoder.findall('./components/comp'):
        xml.find('components').append(comp)
    components = {c.get('ref'): c for c in xml.findall('./components/comp')}
    nets = {}
    for tree in [xml, encoder]:
        for n in tree.findall('./nets/net'):
            nets.setdefault(n.get('name'), set()).update((p.get('ref'), p.get('pin')) for p in n.findall('node'))
    pin_net = {pin: net for net, nodes in nets.items() for pin in nodes}
    errors, expected = [], {}
    if main_refs & encoder_refs:
        errors.append('Duplicate references across motherboard and encoder board')
    if {'U27', 'C62'} & main_refs or not {'U27', 'C62', 'J7'} <= encoder_refs or 'J6' not in main_refs:
        errors.append('Encoder board split is incomplete; export both current schematics')

    def check(condition, message):
        if not condition:
            errors.append(message)

    def device(ref, mapping):
        expected.update({(ref, str(pin)): net for pin, net in mapping.items()})

    def net(ref, pin):
        return pin_net.get((ref, str(pin)))

    def value(ref):
        return components[ref].findtext('value')

    def resistance(ref):
        raw = value(ref).split('/')[0]
        return float(raw.rstrip('RkM')) * {'R': 1, 'k': 1e3, 'M': 1e6}[raw[-1]]

    device('U21', {9:'ACT_5V',10:'ACT_5V',11:'ACT_5V',23:'ACT_DRIVE_EN',21:'WHEEL_DRVOFF',
                  27:'DRV_INHA',29:'DRV_INHB',31:'DRV_INHC',28:'WHEEL_RUN_EN',30:'WHEEL_RUN_EN',32:'WHEEL_RUN_EN',
                  36:'DRV_CS_LOCAL',35:'DRV_SCLK_LOCAL',34:'DRV_MOSI_LOCAL',37:'DRV_AVDD',25:'DRV_AVDD',
                  13:'WHEEL_PHASE_A',14:'WHEEL_PHASE_A',16:'WHEEL_PHASE_B',17:'WHEEL_PHASE_B',19:'WHEEL_PHASE_C',20:'WHEEL_PHASE_C',
                  40:'WHEEL_SOA',39:'WHEEL_SOB',38:'WHEEL_SOC',8:'WHEEL_CP',7:'WHEEL_CPH',6:'WHEEL_CPL',
                  5:'WHEEL_BUCK_SW',3:'WHEEL_BUCK_OUT',33:'DRV_MISO_LOCAL',22:'DRV_FAULT_LOCAL_N',
                  2:'GND',26:'GND',4:'GND',12:'GND',15:'GND',18:'GND',41:'GND'})
    device('U22', {1:'ACT_DRIVE_EN',2:'WHEEL_RUN_REQ',3:'WHEEL_RUN_EN',4:'WHEEL_PWM_A',5:'WHEEL_RUN_EN',6:'DRV_INHA',
                  9:'WHEEL_PWM_B',10:'WHEEL_RUN_EN',8:'DRV_INHB',12:'WHEEL_PWM_C',13:'WHEEL_RUN_EN',11:'DRV_INHC',7:'GND',14:'+3V3'})
    device('Q4', {1:'WHEEL_RUN_EN',2:'GND',3:'WHEEL_DRVOFF'})
    device('J5', {1:'WHEEL_PHASE_A',2:'WHEEL_PHASE_B',3:'WHEEL_PHASE_C'})
    device('U23', {15:'WHEEL_I_A',16:'WHEEL_I_B',1:'WHEEL_I_C',2:'ADC2_SPARE3',3:'ADC2_SPARE4',4:'ADC2_SPARE5',5:'ADC2_SPARE6',6:'ADC2_SPARE7',
                  7:'DRV_AVDD',10:'DRV_AVDD',9:'GND',17:'GND',8:'ADC2_DECAP',11:'ADC2_CS_LOCAL',13:'ADC2_SCLK_LOCAL',14:'ADC2_MOSI_LOCAL',12:'ADC2_MISO_LOCAL'})
    device('U27', {13:'ENC_3V3',1:'ENC_SCLK_LOCAL',8:'ENC_MOSI_LOCAL',7:'ENC_CS_LOCAL',14:'GND',2:'GND',4:'GND',5:'ENC_MISO_LOCAL'})
    device('U28', {1:'+3V3',2:'GND',3:'HALL_EN',5:'ENC_QOD',6:'ENC_3V3'})
    device('U30', {3:'BRAKE_SENSE',4:'BRAKE_REF',1:'BRAKE_OUT',5:'ACT_5V',2:'GND'})
    device('U31', {1:'BRAKE_REF',2:'GND'})
    device('Q5', {1:'BRAKE_GATE',2:'GND',3:'BRAKE_DRAIN'})
    channels = [(1,2,3),(4,5,6),(10,9,8),(13,12,11)]
    for ref, rail, bus, cs, local in [('U24','DRV_AVDD','SPI','CS_DRV8316','DRV'),
                                     ('U26','DRV_AVDD','MOTOR_SPI','CS_ADC2','ADC2'),
                                     ('U29','ENC_3V3','SPI','CS_MA735','ENC')]:
        device(ref, {7:'GND',14:rail,13:rail,12:'GND'})
        for (oe,a,y),source,dest in zip(channels,[bus+'_SCLK',bus+'_MOSI',cs],
                                      [local+'_SCLK_LOCAL',local+'_MOSI_LOCAL',local+'_CS_LOCAL']):
            device(ref, {oe:'GND',a:source,y:dest})
    device('U25', {7:'GND',14:'+3V3',1:'CS_DRV8316',2:'DRV_MISO_LOCAL',3:'SPI_MISO',
                  4:'CS_MA735',5:'ENC_MISO_LOCAL',6:'SPI_MISO',10:'CS_ADC2',9:'ADC2_MISO_LOCAL',8:'MOTOR_SPI_MISO',
                  13:'GND',12:'DRV_FAULT_LOCAL_N',11:'DRV_FAULT_N'})
    passive = {
        'R81':('WHEEL_BUCK_SW','WHEEL_BUCK_OUT'),'R82':('DRV_AVDD','WHEEL_DRVOFF'),
        'R83':('WHEEL_RUN_EN','GND'),'R84':('ACT_DRIVE_EN','GND'),
        'R86':('DRV_AVDD','DRV_CS_LOCAL'),'R87':('DRV_AVDD','DRV_MISO_LOCAL'),
        'R88':('DRV_AVDD','DRV_FAULT_LOCAL_N'),'R89':('DRV_FAULT_LOCAL_N','GND'),
        'R90':('DRV_INHA','GND'),'R91':('DRV_INHB','GND'),'R92':('DRV_INHC','GND'),
        'R98':('DRV_AVDD','ADC2_CS_LOCAL'),'R99':('ENC_3V3','ENC_CS_LOCAL'),
        'R100':('ADC2_MISO_LOCAL','GND'),'R101':('ENC_MISO_LOCAL','GND'),
        'R110':('HALL_EN','GND'),'R125':('ENC_QOD','ENC_3V3'),
        'R111':('ACT_5V','BRAKE_REF'),'R112':('ACT_5V','BRAKE_DIV_TOP'),
        'R113':('BRAKE_DIV_TOP','BRAKE_SENSE'),'R114':('BRAKE_SENSE','GND'),
        'R115':('BRAKE_OUT','BRAKE_FB_1'),'R116':('BRAKE_FB_1','BRAKE_FB_2'),
        'R117':('BRAKE_FB_2','BRAKE_SENSE'),'R119':('BRAKE_OUT','BRAKE_GATE'),'R120':('BRAKE_GATE','GND'),
        'C46':('WHEEL_CP','ACT_5V'),'C47':('WHEEL_CPH','WHEEL_CPL'),
        'C48':('DRV_AVDD','GND'),'C49':('DRV_AVDD','GND'),'C50':('WHEEL_BUCK_OUT','GND'),
        'C56':('DRV_AVDD','GND'),'C57':('DRV_AVDD','GND'),'C58':('ADC2_DECAP','GND'),
        'C62':('ENC_3V3','GND'),'C63':('+3V3','GND'),'C64':('ENC_3V3','GND'),
        'C65':('ACT_5V','GND'),'C66':('BRAKE_REF','GND'),'C67':('BRAKE_SENSE','GND'),
        'C68':('ACT_5V','GND'),'C69':('ACT_5V','GND')}
    for i, phase in enumerate('ABC'):
        passive[f'R{102+i}'] = ('WHEEL_SO'+phase,'WHEEL_I_'+phase)
        passive[f'C{59+i}'] = ('WHEEL_I_'+phase,'GND')
    for i in range(5):
        passive[f'R{105+i}'] = (f'ADC2_SPARE{3+i}','GND')
        check(value(f'R{105+i}') == '0R', 'Spare ADC channel link is not zero ohms')
    for i in range(4):
        passive[f'R{121+i}'] = ('ACT_5V','BRAKE_DRAIN')
    for ref, (a,b) in passive.items():
        device(ref, {1:a,2:b})
    for pin, required in expected.items():
        check(pin_net.get(pin) == required, f'{pin}: expected {required}, got {pin_net.get(pin)}')
    for ref, pins in {'U21':[1,24],'U27':[3,6,9,10,11,12],'U28':[4],'U31':[3],
                      'U24':[11],'U26':[11],'U29':[11]}.items():
        for pin in pins:
            check((net(ref,pin) or '').startswith('unconnected-'), f'{ref}.{pin}: intentional NC was connected')
    identities = {'U21':('DRV8316RRGFR','C5218861'),'U23':('ADS7038IRTER','C2871580'),
                  'U27':('MA735GGU-P','C17233427'),'U28':('TPS22919DCKR','C2149796'),
                  'U30':('TLV1811DBVR','C5373003'),'U31':('LM4040AIM3-2.5/NOPB','C139302'),
                  'Q5':('AO3400A','C20917')}
    identities.update({f'U{i}':('SN74LVC125APWR','C7813') for i in [24,25,26,29]})
    identities.update({f'R{i}':('RC2512JK-7W47RL','C136992') for i in range(121,125)})
    identities.update({r:('0603WAF330JT5E','C23140') for r in ['R5','R6','R58']})
    identities.update({f'R{i}':('0603WAF3300T5E','C23138') for i in range(102,105)})
    identities['R113'] = ('0603WAF3482T5E','C23141')
    for ref, (mpn,lcsc) in identities.items():
        fields = {f.get('name'):f.text for f in components[ref].findall('./fields/field')}
        check((fields.get('MPN'),fields.get('LCSC')) == (mpn,lcsc), f'{ref}: unreviewed part identity')
    check(value('R81') == '22R' and value('C50') == '22uF/25V', 'Unused buck termination differs from TI reference')
    for ref in ['R5','R6','R58']:
        check(value(ref) == '33R', f'{ref}: intended 33 ohm value changed')

    # Compare the custom copper lands against the manufacturer's top-view mapping.
    footprint_checks = 0
    for ref,name in [('U21','Texas_RGF0040E'),('U27','MPS_UTQFN14_2x2'),('J5','MotorWire_3x1mm_P2.54mm')]:
        check(components[ref].findtext('footprint') == 'MagMouse:'+name, f'{ref}: wrong package variant')
        raw = (ROOT/'hardware/kicad/MagMouse.pretty'/(name+'.kicad_mod')).read_text(encoding='utf-8')
        pads = {int(n):tuple(map(float,[x,y,w,h])) for n,x,y,w,h in re.findall(
            r'\(pad "(\d+)" \S+ \S+ \(at ([\d.\-]+) ([\d.\-]+)\) \(size ([\d.]+) ([\d.]+)\)',raw)}
        targets = {}
        if ref == 'U21':
            for i in range(12):
                targets[i+1]=(-2.4,-2.75+i*.5,.6,.25)
                targets[i+21]=(2.4,2.75-i*.5,.6,.25)
            for i in range(8):
                targets[i+13]=(-1.75+i*.5,3.4,.25,.6)
                targets[i+33]=(1.75-i*.5,-3.4,.25,.6)
            targets[41]=(0,0,3.7,5.7)
            check(raw.count('(pad ""') == 12, 'Driver EP requires the reviewed 12-window paste pattern')
        elif ref == 'U27':
            chamfered = {1,3,4,7,8,10,11,14}
            positions = [(i+1,-1,-.4+i*.4,False) for i in range(3)] + [(i+4,-.6+i*.4,1,True) for i in range(4)]
            positions += [(i+8,1,.4-i*.4,False) for i in range(3)] + [(i+11,.6-i*.4,-1,True) for i in range(4)]
            for n,x,y,vertical in positions:
                length=.75 if n==1 else .7
                if n==1:x=-.975
                targets[n]=(x,y,.2 if vertical else length,length if vertical else .2)
            check(raw.count('(chamfer_ratio 0.5)') == 8, 'Encoder corner lands need eight 0.10mm chamfers')
        else:
            targets={i+1:((i-1)*2.54,0,2,2) for i in range(3)}
            check(raw.count('(drill 1)') == 3, 'Motor wire pads require three 1mm holes')
        check(set(pads) == set(targets), f'{ref}: incorrect pad count/numbers')
        for number,geometry in targets.items():
            check(number in pads and all(abs(a-b)<.00001 for a,b in zip(pads.get(number,()),geometry)), f'{ref}.{number}: land geometry differs from reviewed package')
            footprint_checks += 1

    # Evaluate actual AND-gate connections, rather than assuming the RUN net is correct.
    cases = 0
    for permit, request, a, b, c in itertools.product([False,True], repeat=5):
        state = {'ACT_DRIVE_EN':permit,'WHEEL_RUN_REQ':request,'WHEEL_PWM_A':a,'WHEEL_PWM_B':b,'WHEEL_PWM_C':c}
        for _ in range(4):
            for x,y,z in [(1,2,3),(4,5,6),(9,10,8),(12,13,11)]:
                if net('U22',x) in state and net('U22',y) in state:
                    state[net('U22',z)] = state[net('U22',x)] and state[net('U22',y)]
        run = permit and request
        check(state.get(net('Q4',1)) == run, 'DRVOFF sink does not follow permit AND request')
        for pin, command in zip([27,29,31],[a,b,c]):
            check(state.get(net('U21',pin)) == (run and command), f'PWM pin {pin} bypasses hardware permit')
        for pin in [28,30,32]:
            check(state.get(net('U21',pin)) == run, 'Low-side driver input bypasses RUN')
        cases += 1

    rt = resistance('R112') + resistance('R113')
    rb = resistance('R114')
    rh = sum(resistance(f'R{i}') for i in [115,116,117])
    def thresholds(top, bottom, feedback, reference, low, high_drop):
        k = 1 + top/bottom + top/feedback
        return (reference*k-low*top/feedback,
                (reference*k+high_drop*top/feedback)/(1+top/feedback))
    nominal = thresholds(rt,rb,rh,2.5,0,0)
    corners = []
    # +/-1.7% bounds include 1% initial R and <=100ppm/C over -40..85C.
    # Reference +/-1%; comparator +/-4mV, plus 0.1mV bias allowance.
    for tr,br,fr,vr,offset,low,drop in itertools.product([-.017,.017],[-.017,.017],[-.017,.017],[-.01,.01],[-.0041,.0041],[0,.25],[0,.25]):
        corners.append(thresholds(rt*(1+tr),rb*(1+br),rh*(1+fr),2.5*(1+vr)+offset,low,drop))
    on = [c[0] for c in corners]; off = [c[1] for c in corners]
    check(min(off) > 5.55, 'Brake lacks 50mV release margin above the maximum normal USB rail')
    check(max(on) < 6.2, 'Brake turn-on exceeds provisional static ceiling')
    check(min(a-b for a,b in corners) > .15, 'Insufficient same-corner hysteresis')
    check(.25 < .65, 'Comparator VOL must be below minimum AO3400A threshold')
    fault_min = 3.1 * (resistance('R89')*.983)/(resistance('R88')*1.017+resistance('R89')*.983)
    check(fault_min > 2.2, 'nFAULT startup pull-up violates TI test-mode avoidance threshold')
    filters = []
    for i in range(3):
        check(value(f'C{59+i}') == '22pF/50V', 'Unreviewed CSA filter capacitor')
        filters.append(1/(2*math.pi*resistance(f'R{102+i}')*22e-12)/1e6)
    brake_r = 1/sum(1/resistance(f'R{i}') for i in range(121,125))
    # These are acceptance targets, not measured capacitance or response.
    peak_a, cap_f, response_s = .4, 47e-6, 10e-6
    peak_v = max(on) + peak_a*response_s/cap_f
    por_peak = 2.4 + peak_a*200e-6/cap_f
    check(peak_v < 6.5 and por_peak < min(on), 'Provisional response/POR budget has no rail margin')
    # 5% initial plus 200ppm/C through -40..85C, rounded outward to 6.4%.
    check(min(off)/(brake_r*1.064) > peak_a, 'Brake cannot sink the provisional peak returned current')
    report = {'critical_pin_checks':len(expected),'shutdown_truth_table_cases':cases,
              'part_identity_checks':len(identities),'custom_land_geometry_checks':footprint_checks,'brake_corner_cases':len(corners),
              'brake_nominal_on_off_V':nominal,'brake_on_range_V':[min(on),max(on)],
              'brake_off_range_V':[min(off),max(off)],'minimum_hysteresis_V':min(a-b for a,b in corners),
              'brake_parallel_ohms':brake_r,'brake_on_power_at_6V_W':36/brake_r,
              'brake_each_resistor_at_6V_W':36/resistance('R121'),
              'fault_startup_min_V':fault_min,'csa_filter_cutoffs_MHz':filters,
              'unverified_bench_targets':{'peak_return_A':peak_a,'average_return_W':.5,'effective_rail_capacitance_uF':47,
                                         'running_brake_response_us':10,'rail_peak_limit_V':6.5},
              'conditional_running_peak_V':peak_v,'conditional_POR_peak_V':por_peak,
              'scope':'Static netlist/Boolean/DC corner arithmetic only. No analog, firmware, motor or thermal acceptance.',
              'errors':errors}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
