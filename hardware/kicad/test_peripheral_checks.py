# SPDX-License-Identifier: GPL-3.0-or-later
"""Reject faults that can damage the RGB LED, affect boot or invalidate IMU wiring."""
import copy
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from verify_peripherals import review


class PeripheralChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ET.parse(Path(__file__).resolve().parents[2]/'build/kicad-review/netlist.xml').getroot()

    def rejects_reconnection(self, ref, pin, target, diagnostic):
        root = copy.deepcopy(self.source)
        destination = root.find(f'./nets/net[@name="{target}"]')
        found = False
        for net in root.findall('./nets/net'):
            for node in list(net.findall('node')):
                if (node.get('ref'),node.get('pin')) == (ref,pin):
                    net.remove(node)
                    destination.append(node)
                    found = True
        self.assertTrue(found)
        self.assertTrue(any(diagnostic in e for e in review(root)['errors']))

    def test_current_schematic(self):
        self.assertEqual(review(self.source)['errors'], [])

    def test_led_cannot_use_regenerating_rail(self):
        self.rejects_reconnection('D5','2','ACT_5V','D5.2')

    def test_gpio45_cannot_bypass_level_buffer(self):
        self.rejects_reconnection('D5','1','RGB_DATA','GPIO45')

    def test_imu_reserved_ground_pin_cannot_be_powered(self):
        self.rejects_reconnection('U32','7','+3V3','U32.7')

    def test_rgb_cannot_stay_enabled_in_suspend(self):
        self.rejects_reconnection('U33','3','+3V3','U33.3')


if __name__ == '__main__':
    unittest.main()
