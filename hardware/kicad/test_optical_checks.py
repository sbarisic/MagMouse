# SPDX-License-Identifier: GPL-3.0-or-later
"""Inject optical power, bus-contention and footprint faults into review inputs."""
import copy
import unittest
import xml.etree.ElementTree as ET
from verify_optical import review, HERE


class OpticalChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ET.parse(HERE.parents[1]/'build/kicad-review/netlist.xml').getroot()

    def rejects_reconnection(self, ref, pin, target, diagnostic):
        root = copy.deepcopy(self.source)
        destination = root.find(f'./nets/net[@name="{target}"]')
        source = next(n for n in root.findall('./nets/net')
                      if n.find(f'node[@ref="{ref}"][@pin="{pin}"]') is not None)
        node = source.find(f'node[@ref="{ref}"][@pin="{pin}"]')
        source.remove(node)
        destination.append(node)
        self.assertTrue(any(diagnostic in e for e in review(root)['errors']))

    def test_current_schematic(self):
        self.assertEqual(review(self.source)['errors'], [])

    def test_internal_ldo_output_cannot_be_externally_powered(self):
        self.rejects_reconnection('U35','3','OPT_1V9','U35.3')

    def test_reset_miso_cannot_contend_with_shared_bus(self):
        self.rejects_reconnection('U35','12','SPI_MISO','U35.12')

    def test_chip_select_cannot_back_power_sensor(self):
        self.rejects_reconnection('U35','13','CS_PAW','U35.13')

    def test_spi_gate_cannot_be_permanently_enabled(self):
        self.rejects_reconnection('U37','10','GND','U37.10')

    def test_reset_must_overcome_internal_pullup(self):
        self.rejects_reconnection('U35','7','OPT_CTRL','U35.7')

    def test_sensor_cannot_bypass_firmware_qualified_enable(self):
        self.rejects_reconnection('U38','3','+3V3','U38.3')

    def test_ramp_capacitor_cannot_be_omitted(self):
        root = copy.deepcopy(self.source)
        root.find('./components/comp[@ref="C79"]/value').text = 'DNP'
        self.assertTrue(any('C79' in e for e in review(root)['errors']))

    def test_standard_dip_pitch_cannot_replace_staggered_rows(self):
        raw = (HERE/'MagMouse.pretty/PixArt_PMW3360DM_T2QU.kicad_mod').read_text(encoding='utf-8')
        changed = raw.replace('(at 3.88 -5.35)', '(at 3.12 -5.35)')
        self.assertNotEqual(raw, changed)
        self.assertTrue(any('stagger' in e for e in review(self.source,footprint=changed)['errors']))


if __name__ == '__main__':
    unittest.main()
