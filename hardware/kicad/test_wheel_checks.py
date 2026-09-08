# SPDX-License-Identifier: GPL-3.0-or-later
"""Mutation checks: the wheel review must reject dangerous exported-netlist edits."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent


class WheelChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ET.parse(HERE.parents[1] / 'build/kicad-review/netlist.xml').getroot()

    def rejects(self, edit, diagnostic):
        root = copy.deepcopy(self.source)
        edit(root)
        with tempfile.TemporaryDirectory(prefix='magmouse-wheel-') as folder:
            netlist, output = Path(folder)/'netlist.xml', Path(folder)/'checks.json'
            ET.ElementTree(root).write(netlist,encoding='utf-8',xml_declaration=True)
            result = subprocess.run([sys.executable,str(HERE/'verify_wheel.py'),
                                     '--netlist',str(netlist),'--output',str(output)],capture_output=True,text=True)
            self.assertEqual(result.returncode,1,result.stderr)
            errors = json.loads(output.read_text(encoding='utf-8'))['errors']
            self.assertTrue(any(diagnostic in error for error in errors),errors)

    @staticmethod
    def reconnect(root, ref, pin, target):
        destination = next(n for n in root.findall('./nets/net') if n.get('name') == target)
        for net in root.findall('./nets/net'):
            for node in net.findall('node'):
                if (node.get('ref'),node.get('pin')) == (ref,pin):
                    net.remove(node)
                    destination.append(node)
                    return
        raise AssertionError('Fixture pin missing')

    def test_request_cannot_bypass_hardware_permit(self):
        self.rejects(lambda r:self.reconnect(r,'Q4','1','WHEEL_RUN_REQ'),'DRVOFF sink')

    def test_brake_cannot_depend_on_logic_supply(self):
        self.rejects(lambda r:self.reconnect(r,'U30','5','+3V3'),"('U30', '5'): expected ACT_5V")

    def test_mixed_adc_power_domain_is_rejected(self):
        self.rejects(lambda r:self.reconnect(r,'U23','7','+3V3'),"('U23', '7'): expected DRV_AVDD")

    def test_wrong_33_ohm_catalog_number_is_rejected(self):
        def edit(r):
            r.find('./components/comp[@ref="R5"]/fields/field[@name="LCSC"]').text='C23138'
        self.rejects(edit,'R5: unreviewed part identity')

    def test_brake_below_normal_rail_is_rejected(self):
        def edit(r):
            r.find('./components/comp[@ref="R113"]/value').text='22k'
        self.rejects(edit,'Brake lacks 50mV release margin')


if __name__ == '__main__':
    unittest.main()
