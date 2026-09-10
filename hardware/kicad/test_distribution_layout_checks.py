# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the saved-copper audit with deliberately disconnected circuits."""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class DistributionLayoutChecks(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / 'hardware/kicad/MagMouse.kicad_pcb').read_text(encoding='utf-8')

    def run_check(self, source):
        with tempfile.TemporaryDirectory(prefix='magmouse-distribution-') as folder:
            board, report = Path(folder) / 'board.kicad_pcb', Path(folder) / 'check.json'
            board.write_text(source, encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'hardware/kicad/verify_distribution_layout.py'),
                                     '--board', str(board), '--output', str(report)],
                                    capture_output=True, text=True)
            self.assertIn(result.returncode, [0, 1], result.stderr)
            return json.loads(report.read_text(encoding='utf-8'))['errors']

    def test_saved_layout_passes(self):
        self.assertEqual(self.run_check(self.source), [])

    def test_missing_ground_reference_fails(self):
        altered = re.sub(r'^\t\(zone\b.*?^\t\)\n',
                         lambda m: '' if '(net "GND")' in m[0] and
                         '(layer "In1.Cu")' in m[0] else m[0],
                         self.source, flags=re.M | re.S)
        self.assertNotEqual(altered, self.source)
        self.assertTrue(any('GND' in e for e in self.run_check(altered)))

    def test_power_driver_sense_and_interlock_opens_fail(self):
        for net in ['ACT_5V', 'BTN_L_COIL_P', 'BTN_M_COIL_N', 'WHEEL_PHASE_B',
                    'BRAKE_DRAIN', 'BRAKE_SENSE', 'BRAKE_GATE', 'WD_RCEXT',
                    'ACT_HEARTBEAT', 'WHEEL_RUN_EN', 'DRV_INHA', 'BTN_R_IN2',
                    'WHEEL_I_A', 'DRV_AVDD']:
            with self.subTest(net=net):
                altered = re.sub(r'^\t\(segment\b.*?^\t\)\n',
                                 lambda m: '' if f'(net "{net}")' in m[0] else m[0],
                                 self.source, flags=re.M | re.S)
                self.assertNotEqual(altered, self.source)
                self.assertTrue(any(net in e for e in self.run_check(altered)))


if __name__ == '__main__':
    unittest.main()
