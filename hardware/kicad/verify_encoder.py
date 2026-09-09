# SPDX-License-Identifier: GPL-3.0-or-later
"""Check separate encoder schematics and the physical harness pin contract."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
CONNECTOR_NETS = {1:'ENC_3V3', 2:'GND', 3:'ENC_SCLK_LOCAL', 4:'GND',
                  5:'ENC_MOSI_LOCAL', 6:'ENC_CS_LOCAL', 7:'GND', 8:'ENC_MISO_LOCAL'}
CONNECTOR_FP = 'Connector_JST:JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal'


def read_netlist(path):
    root = ET.parse(path).getroot()
    components = {c.get('ref'):c for c in root.findall('./components/comp')}
    pins = {}
    for net in root.findall('./nets/net'):
        for node in net.findall('node'):
            key = node.get('ref'), node.get('pin')
            if key in pins:
                raise ValueError(f'Duplicate pin in netlist: {key}')
            pins[key] = net.get('name')
    return components, pins


def verify(main, encoder, harness):
    mc, mp = main
    ec, ep = encoder
    errors = []
    def check(ok, message):
        if not ok:
            errors.append(message)
    def pin(mapping, ref, number):
        return mapping.get((ref, str(number)))
    check(set(ec) == {'J7','U27','C62'}, 'Encoder assembly must contain only J7, U27 and C62')
    check(not (set(mc) & set(ec)), 'Components must not appear on both board BOMs')
    for comps, mapping, ref in [(mc,mp,'J6'),(ec,ep,'J7')]:
        comp = comps.get(ref, ET.Element('comp'))
        fields = {f.get('name'):f.text for f in comp.findall('./fields/field')}
        check((fields.get('MPN'),fields.get('LCSC')) == ('SM08B-SRSS-TB(LF)(SN)','C160407'), f'{ref}: connector identity changed')
        check(comp.findtext('footprint') == CONNECTOR_FP, f'{ref}: wrong connector footprint')
        props = {p.get('name') for p in comp.findall('property')}
        check(not props & {'dnp','exclude_from_bom','exclude_from_board'}, f'{ref}: connector excluded from assembly')
        for number, net in CONNECTOR_NETS.items():
            check(pin(mapping,ref,number) == net, f'{ref}.{number}: expected {net}')
    for number, net in {13:'ENC_3V3',1:'ENC_SCLK_LOCAL',8:'ENC_MOSI_LOCAL',7:'ENC_CS_LOCAL',
                        5:'ENC_MISO_LOCAL',2:'GND',4:'GND',14:'GND'}.items():
        check(pin(ep,'U27',number) == net, f'U27.{number}: expected {net}')
    for number in [3,6,9,10,11,12]:
        check((pin(ep,'U27',number) or '').startswith('unconnected-'), f'U27.{number}: unused output must remain NC')
    check(pin(ep,'C62',1) == 'ENC_3V3' and pin(ep,'C62',2) == 'GND', 'C62 must bypass the encoder supply locally')
    check(ec.get('C62', ET.Element('comp')).findtext('value') == '1uF/50V', 'C62 bypass value changed')
    check(pin(mp,'U28',6) == 'ENC_3V3' and pin(mp,'U28',1) == '+3V3' and pin(mp,'U28',3) == 'HALL_EN', 'Encoder switched supply was bypassed')
    for ref, number, net in [('U29',14,'ENC_3V3'),('U29',3,'ENC_SCLK_LOCAL'),
                              ('U29',6,'ENC_MOSI_LOCAL'),('U29',8,'ENC_CS_LOCAL'),
                              ('U25',5,'ENC_MISO_LOCAL'),('U25',4,'CS_MA735')]:
        check(pin(mp,ref,number) == net, f'{ref}.{number}: encoder isolation path changed')
    check(not any(ref == 'U3' and net in set(CONNECTOR_NETS.values())-{'GND'} for (ref,_),net in mp.items()), 'Connector must not bypass SPI power-domain buffers')
    check(set(ep.values()) <= set(CONNECTOR_NETS.values()) | {v for v in ep.values() if v.startswith('unconnected-')}, 'Unexpected supply or signal on encoder board')
    check(harness.get('motherboard_connector') == 'J6' and harness.get('encoder_connector') == 'J7', 'Harness connector references changed')
    connections = harness.get('connections', [])
    actual = [(c.get('motherboard_pin'),c.get('encoder_pin'),c.get('net')) for c in connections]
    expected = [(n,n,net) for n,net in CONNECTOR_NETS.items()]
    check(sorted(actual, key=repr) == sorted(expected, key=repr), 'Harness must connect every numbered pin straight through, including all three grounds')
    return {'connector_pin_checks':16, 'harness_conductors':8,
            'motherboard_components':len(mc), 'encoder_components':len(ec),
            'scope':'Static two-board connectivity and harness specification; no cable, timing or magnetic acceptance',
            'errors':errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--netlist',type=Path,default=ROOT/'build/kicad-review/netlist.xml')
    parser.add_argument('--encoder-netlist',type=Path,default=ROOT/'build/encoder-review/netlist.xml')
    parser.add_argument('--harness',type=Path,default=ROOT/'hardware/encoder/harness.json')
    parser.add_argument('--output',type=Path,default=ROOT/'build/encoder-review/encoder-checks.json')
    args = parser.parse_args()
    report = verify(read_netlist(args.netlist), read_netlist(args.encoder_netlist),
                    json.loads(args.harness.read_text(encoding='utf-8')))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return int(bool(report['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
