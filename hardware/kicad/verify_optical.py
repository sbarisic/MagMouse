# SPDX-License-Identifier: GPL-3.0-or-later
"""Check optical power domains, SPI isolation and manufacturer land coordinates.

Run export_review.py first. This does not simulate ramp timing or prove lens fit.
"""
import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def review(xml, footprint=None, allocation=None):
    components = {c.get('ref'): c for c in xml.findall('./components/comp')}
    nets = {n.get('name'): {(p.get('ref'), p.get('pin')) for p in n.findall('node')}
            for n in xml.findall('./nets/net')}
    pin_net = {p: name for name, nodes in nets.items() for p in nodes}
    expected = {
        'U35': {3:'OPT_VDDPIX',4:'OPT_1V9',5:'OPT_3V3',7:'OPT_RESET_N',8:'GND',
                9:'PAW_MOTION_N',10:'OPT_SCLK',11:'OPT_MOSI',12:'OPT_MISO',13:'OPT_CS_N',15:'OPT_LED_P'},
        'U36': {1:'OPT_3V3',2:'GND',3:'OPT_3V3',5:'OPT_1V9'},
        'U37': {1:'CS_PAW',2:'SPI_MOSI',3:'OPT_MOSI',4:'CS_PAW',5:'SPI_SCLK',6:'OPT_SCLK',
                7:'GND',8:'SPI_MISO',9:'OPT_MISO',10:'CS_PAW',11:'OPT_RESET_N',12:'OPT_CTRL',13:'GND',14:'OPT_3V3'},
        'U38': {1:'+3V3',2:'GND',3:'HALL_EN',4:'OPT_RAMP_CT',6:'OPT_3V3'},
        'U39': {1:'GND',2:'CS_PAW',3:'GND',4:'OPT_CS_N',5:'OPT_3V3'},
        'R131': {1:'OPT_3V3',2:'OPT_CS_N'}, 'R132': {1:'OPT_1V9',2:'OPT_LED_P'},
        'R133': {1:'OPT_3V3',2:'OPT_SCLK'}, 'R134': {1:'OPT_MOSI',2:'GND'},
        'R135': {1:'OPT_3V3',2:'OPT_MISO'}, 'R136': {1:'OPT_3V3',2:'PAW_MOTION_N'},
        'R72': {1:'+3V3',2:'CS_PAW'}, 'R79': {1:'OPT_CTRL',2:'GND'},
        'TP40': {1:'OPT_3V3'}, 'TP41': {1:'OPT_1V9'}, 'TP42': {1:'OPT_VDDPIX'}, 'TP43': {1:'OPT_RESET_N'},
    }
    for ref, net in [('C77','+3V3'),('C78','+3V3'),('C79','OPT_RAMP_CT'),('C80','OPT_3V3'),
                     ('C81','OPT_3V3'),('C82','OPT_1V9'),('C83','OPT_1V9'),('C84','OPT_VDDPIX'),
                     ('C85','OPT_VDDPIX'),('C86','OPT_3V3'),('C87','OPT_3V3')]:
        expected[ref] = {1:net,2:'GND'}
    errors = []
    def check(ok, message):
        if not ok:
            errors.append(message)
    for ref, mapping in expected.items():
        check(ref in components, f'{ref}: missing component')
        for pin, name in mapping.items():
            check(pin_net.get((ref,str(pin))) == name, f'{ref}.{pin}: expected {name}')
        check(components.get(ref, ET.Element('comp')).find('./property[@name="dnp"]') is None,
              f'{ref}: required component marked DNP')
    for ref, pins in [('U35',[1,2,6,14,16]),('U36',[4]),('U38',[5])]:
        for pin in pins:
            name = pin_net.get((ref,str(pin)), '')
            check(name.startswith('unconnected-') and len(nets.get(name, ())) == 1, f'{ref}.{pin}: must remain NC')
    check(nets.get('OPT_VDDPIX') == {('U35','3'),('C84','1'),('C85','1'),('TP42','1')},
          'VDDPIX must supply only its own decoupling and test pad')
    check(nets.get('OPT_MISO') == {('U35','12'),('U37','9'),('R135','2')},
          'Raw sensor MISO must not join a shared or host-powered net')
    check(nets.get('OPT_CS_N') == {('U35','13'),('U39','4'),('R131','2')},
          'Sensor CS must be isolated from the powered host')
    identities = {
        'U35':('PMW3360DM-T2QU','C20612443'), 'U36':('TLV75519PDBVR','C2865381'),
        'U37':('SN74LVC125APWR','C7813'), 'U38':('TPS22918DBVR','C131941'),
        'U39':('SN74LVC1G125DBVR','C23654'), 'R132':('0603WAF390JT5E','C23154'),
        'C79':('CL10B102KB8NNNC','C1588'), 'C81':('CL10B225KP8NNNC','C100082'),
        'C82':('CL10B225KP8NNNC','C100082'), 'C84':('CL10A475KP8NNNC','C1705'),
    }
    for ref, identity in identities.items():
        comp = components.get(ref, ET.Element('comp'))
        fields = {f.get('name'): f.text for f in comp.findall('./fields/field')}
        check((fields.get('MPN'),fields.get('LCSC')) == identity, f'{ref}: unreviewed identity')
    values = {'R131':'10k','R132':'39R','R133':'100k','R134':'100k','R135':'10k','R136':'100k',
              'R72':'10k','R79':'10k','C77':'10uF/25V','C78':'10uF/25V','C79':'1nF/50V',
              'C80':'100nF','C81':'2.2uF/10V','C82':'2.2uF/10V','C83':'100nF',
              'C84':'4.7uF/10V','C85':'100nF','C86':'100nF','C87':'100nF'}
    for ref, value in values.items():
        check(components.get(ref,ET.Element('comp')).findtext('value') == value, f'{ref}: expected {value}')
    check(components.get('U35',ET.Element('comp')).findtext('footprint') ==
          'MagMouse:PixArt_PMW3360DM_T2QU', 'U35: requires custom staggered footprint')
    raw = footprint if footprint is not None else (HERE/'MagMouse.pretty/PixArt_PMW3360DM_T2QU.kicad_mod').read_text(encoding='utf-8')
    matches = re.findall(r'\(pad "(\d+)" thru_hole (?:rect|circle)\s+\(at ([\d.\-]+) ([\d.\-]+)\)\s+\(size ([\d.]+) ([\d.]+)\)\s+\(drill ([\d.]+)\)',raw)
    pads = {int(n):tuple(map(float,[x,y,w,h,d])) for n,x,y,w,h,d in matches}
    targets = {n:(round(5.66-(n-1)*1.78,3),-5.35,1.3,1.3,.7) for n in range(1,9)}
    targets.update({n:(round(5.66-13.35+(n-9)*1.78,3),5.35,1.3,1.3,.7) for n in range(9,17)})
    check(pads == targets and len(matches) == 16, 'PMW3360 top-view stagger, drill or optical origin mismatch')
    check('"Edge.Cuts"' not in raw, 'Sample-review footprint must not silently cut the board')
    spec = allocation if allocation is not None else json.loads((HERE/'gpio-allocation.json').read_text(encoding='utf-8'))
    devices = [d for b in spec['spi'] for d in b['devices'] if d['name']=='PMW3360']
    check(len(devices)==1 and devices[0].get('clock_target_hz')==2000000 and
          devices[0].get('spi_mode')==3, 'PMW3360 requires reviewed 2MHz mode-3 allocation')
    return {'critical_pin_checks':sum(map(len,expected.values())), 'part_identity_checks':len(identities),
            'sensor_pad_checks':16, 'optical_startup_allowance_mA':150,
            'motion_burst_wire_and_address_wait_us':87,
            'qualification':'OPEN: rail ramps/transients, power-off leakage, SROM rights, shared-bus deadlines and physical lens fit',
            'errors':errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--netlist',type=Path,default=ROOT/'build/kicad-review/netlist.xml')
    parser.add_argument('--output',type=Path,default=ROOT/'build/kicad-review/optical-checks.json')
    args = parser.parse_args()
    result = review(ET.parse(args.netlist).getroot())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    return int(bool(result['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
