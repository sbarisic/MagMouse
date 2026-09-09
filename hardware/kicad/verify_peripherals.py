# SPDX-License-Identifier: GPL-3.0-or-later
"""Check IMU/RGB wiring and boot/power boundaries; this is not hardware validation."""
import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def review(xml):
    components = {c.get('ref'): c for c in xml.findall('./components/comp')}
    nets = {n.get('name'): {(p.get('ref'), p.get('pin')) for p in n.findall('node')}
            for n in xml.findall('./nets/net')}
    pin_net = {p: name for name, nodes in nets.items() for p in nodes}
    expected = {
        'U32': {1:'SPI_MISO',4:'IMU_INT1',5:'+3V3',6:'GND',7:'GND',8:'+3V3',
                9:'IMU_PIN9',12:'CS_IMU',13:'SPI_SCLK',14:'SPI_MOSI'},
        'U33': {1:'PWR_5V',2:'GND',3:'HALL_EN',5:'RGB_5V'},
        'U34': {2:'RGB_DATA',3:'GND',4:'RGB_BUFFER_OUT',5:'RGB_5V'},
        'D5': {1:'RGB_DIN',2:'RGB_5V',4:'GND'},
        'R126': {1:'IMU_PIN9',2:'GND'}, 'R127': {1:'+3V3',2:'IMU_INT1'},
        'R128': {1:'RGB_BUFFER_OUT',2:'RGB_DIN'}, 'R129': {1:'RGB_DIN',2:'GND'},
        'R130': {1:'RGB_5V',2:'GND'}, 'R78': {1:'RGB_DATA',2:'GND'},
        'R73': {1:'+3V3',2:'CS_IMU'}, 'TP38': {1:'RGB_5V'}, 'TP39': {1:'RGB_DIN'},
    }
    for ref, supply in [('C70','+3V3'),('C71','+3V3'),('C72','+3V3'),('C73','PWR_5V'),
                        ('C74','RGB_5V'),('C75','RGB_5V'),('C76','RGB_5V')]:
        expected[ref] = {1:supply,2:'GND'}
    errors = []

    def check(ok, message):
        if not ok:
            errors.append(message)

    for ref, mapping in expected.items():
        check(ref in components, f'{ref}: missing component')
        for pin, name in mapping.items():
            check(pin_net.get((ref,str(pin))) == name, f'{ref}.{pin}: expected {name}')
    for ref, pins in [('U32',[2,3,10,11]),('U33',[4]),('U34',[1]),('D5',[3])]:
        for pin in pins:
            name = pin_net.get((ref,str(pin)), '')
            check(name.startswith('unconnected-') and len(nets.get(name, ())) == 1,
                  f'{ref}.{pin}: reserved/unused pin must remain NC')
    identities = {
        'U32': ('ICM-42688-P','C1850418'), 'U33': ('TPS7A2450DBVR','C2864436'),
        'U34': ('SN74LV1T34DBVR','C100024'), 'D5': ('SK6805-EC15','C2890035'),
        'C71': ('CL10B225KP8NNNC','C100082'), 'C72': ('CL10B103KB8NNNC','C1589'),
        'R128': ('0603WAF3300T5E','C23138'),
    }
    values = {'R126':'10k','R127':'10k','R128':'330R','R129':'100k','R130':'10k',
              'R78':'10k','R73':'10k','C70':'100nF','C71':'2.2uF/10V','C72':'10nF',
              'C73':'10uF/25V','C74':'10uF/25V','C75':'100nF','C76':'100nF'}
    for ref, identity in identities.items():
        comp = components.get(ref, ET.Element('comp'))
        fields = {f.get('name'):f.text for f in comp.findall('./fields/field')}
        check((fields.get('MPN'),fields.get('LCSC')) == identity, f'{ref}: unreviewed part identity')
    for ref, value in values.items():
        comp = components.get(ref, ET.Element('comp'))
        check(comp.findtext('value') == value, f'{ref}: expected fitted {value}')
    for ref in expected:
        comp = components.get(ref, ET.Element('comp'))
        check(comp.find('./property[@name="dnp"]') is None, f'{ref}: required part marked DNP')
    check(nets.get('RGB_DATA') == {('U3','41'),('R78','1'),('TP30','1'),('U34','2')},
          'GPIO45 must connect only to host pulldown, test pad and buffer input')
    check(components.get('U32',ET.Element('comp')).findtext('footprint') ==
          'Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y', 'U32: wrong LGA package')
    check(components.get('D5',ET.Element('comp')).findtext('footprint') ==
          'MagMouse:OPSCO_SK6805_EC15', 'D5: wrong LED package')
    raw = (HERE/'MagMouse.pretty/OPSCO_SK6805_EC15.kicad_mod').read_text(encoding='utf-8')
    pads = {int(n):tuple(map(float,[x,y,w,h])) for n,x,y,w,h in re.findall(
        r'\(pad "(\d+)" smd rect\s+\(at ([\d.\-]+) ([\d.\-]+)\)\s+\(size ([\d.]+) ([\d.]+)\)',raw)}
    targets = {1:(-.475,.475,.55,.55),2:(.475,.475,.55,.55),
               3:(.475,-.475,.55,.55),4:(-.475,-.475,.55,.55)}
    check(pads == targets, 'LED top-view pad numbering/geometry mismatch')
    return {'critical_pin_checks':sum(map(len,expected.values())),
            'part_identity_checks':len(identities), 'led_pad_checks':4,
            'rgb_supply_nominal_ceiling_V':5.0,
            'rgb_regulated_range_V':[5*.9875,5*1.0125],
            'qualification': 'OPEN: RGB dropout/startup/discharge and DIN timing; IMU vibration, SPI contention and USB suspend current',
            'errors':errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--netlist',type=Path,default=ROOT/'build/kicad-review/netlist.xml')
    parser.add_argument('--output',type=Path,default=ROOT/'build/kicad-review/peripheral-checks.json')
    args = parser.parse_args()
    result = review(ET.parse(args.netlist).getroot())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    return int(bool(result['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
