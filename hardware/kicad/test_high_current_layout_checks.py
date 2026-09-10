# SPDX-License-Identifier: GPL-3.0-or-later
"""Fault injection for actuator resistance, heat-spreading and storage checks."""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class HighCurrentLayoutChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'hardware/kicad/MagMouse.kicad_pcb').read_text(encoding='utf-8')

    def check(self, source):
        with tempfile.TemporaryDirectory(prefix='magmouse-high-current-') as folder:
            board, report = Path(folder) / 'board.kicad_pcb', Path(folder) / 'check.json'
            board.write_text(source, encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'hardware/kicad/verify_high_current_layout.py'),
                                     '--board', str(board), '--output', str(report)],
                                    capture_output=True, text=True)
            self.assertIn(result.returncode, [0, 1], result.stderr)
            return json.loads(report.read_text(encoding='utf-8'))['errors']

    def test_saved_board_passes(self):
        self.assertEqual(self.check(self.source), [])

    def test_open_power_paths_fail(self):
        for net, label in [('PWR_5V', 'U12.6 -> U13.5'), ('ACT_5V', 'U13.6 -> U4.5'),
                           ('WHEEL_PHASE_A', 'U21.13 -> J5.1'), ('BRAKE_DRAIN', 'Q5.3 -> R121.2')]:
            with self.subTest(net=net):
                altered = re.sub(r'^\t\(segment\b.*?^\t\)\n',
                                 lambda m: '' if f'(net "{net}")' in m[0] else m[0],
                                 self.source, flags=re.M | re.S)
                self.assertNotEqual(altered, self.source)
                self.assertTrue(any(label + ': no copper path' in e for e in self.check(altered)))

    def test_narrow_connected_phase_fails_resistance_budget(self):
        altered = re.sub(r'^\t\(segment\b.*?^\t\)\n',
                         lambda m: re.sub(r'\(width [0-9.]+\)', '(width 0.15)', m[0])
                         if '(net "WHEEL_PHASE_B")' in m[0] else m[0], self.source, flags=re.M | re.S)
        self.assertNotEqual(altered, self.source)
        errors = self.check(altered)
        self.assertFalse(any('no copper path' in e for e in errors))
        self.assertTrue(any('U21.16 -> J5.2:' in e and 'layout budget' in e for e in errors))

    def test_missing_back_spreader_fails(self):
        altered = re.sub(r'^\t\(zone\b.*?^\t\)\n',
                         lambda m: '' if '(name "ACTUATOR_U4_GND_B.Cu")' in m[0] else m[0],
                         self.source, flags=re.M | re.S)
        self.assertNotEqual(altered, self.source)
        self.assertTrue(any('ACTUATOR_U4_GND_B.Cu' in e for e in self.check(altered)))

    def test_thermal_reliefs_fail_solid_connection_requirement(self):
        altered = re.sub(r'^\t\(zone\b.*?^\t\)\n',
                         lambda m: m[0].replace('(connect_pads yes', '(connect_pads')
                         if '(name "ACTUATOR_U21_GND_F.Cu")' in m[0] else m[0],
                         self.source, flags=re.M | re.S)
        self.assertNotEqual(altered, self.source)
        self.assertTrue(any('expected solid pad connections' in e for e in self.check(altered)))

    def test_empty_saved_fill_fails_area_requirement(self):
        def empty(zone):
            if '(name "ACTUATOR_U5_GND_F.Cu")' not in zone[0]:
                return zone[0]
            return re.sub(r'^\t\t\(filled_polygon\b.*?^\t\t\)\n', '', zone[0], flags=re.M | re.S)
        altered = re.sub(r'^\t\(zone\b.*?^\t\)\n', empty, self.source, flags=re.M | re.S)
        self.assertNotEqual(altered, self.source)
        self.assertTrue(any('ACTUATOR_U5_GND_F.Cu:' in e and 'below' in e for e in self.check(altered)))

    def test_changed_bulk_value_requires_new_storage_review(self):
        altered = re.sub(r'^\t\(footprint\b.*?^\t\)\n',
                         lambda m: m[0].replace('"10uF/25V"', '"1uF/25V"')
                         if '(property "Reference" "C8"' in m[0] else m[0],
                         self.source, flags=re.M | re.S)
        self.assertNotEqual(altered, self.source)
        self.assertTrue(any('C8: ACT capacitor value differs' in e for e in self.check(altered)))

    def test_thinner_stack_copper_requires_model_review(self):
        altered = self.source.replace('(thickness 0.035)', '(thickness 0.018)')
        self.assertNotEqual(altered, self.source)
        self.assertTrue(any('copper thickness differs' in e for e in self.check(altered)))


if __name__ == '__main__':
    unittest.main()
