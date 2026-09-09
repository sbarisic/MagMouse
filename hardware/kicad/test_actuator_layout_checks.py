# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify that actuator copper checks detect physical opens in saved board copies."""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ActuatorLayoutChecks(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / 'hardware/kicad/MagMouse.kicad_pcb').read_text(encoding='utf-8')

    def run_check(self, source):
        with tempfile.TemporaryDirectory(prefix='magmouse-actuator-') as folder:
            board, report = Path(folder) / 'MagMouse.kicad_pcb', Path(folder) / 'check.json'
            board.write_text(source, encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'hardware/kicad/verify_actuator_layout.py'),
                                     '--board', str(board), '--output', str(report)],
                                    capture_output=True, text=True)
            self.assertIn(result.returncode, [0, 1], result.stderr)
            return json.loads(report.read_text(encoding='utf-8'))['errors']

    def remove_tracks(self, net, extra=lambda s: True):
        return re.sub(r'^\t\(segment\b.*?^\t\)\n',
                      lambda m: '' if f'(net "{net}")' in m[0] and extra(m[0]) else m[0],
                      self.source, flags=re.M | re.S)

    def test_current_layout_passes(self):
        self.assertEqual(self.run_check(self.source), [])

    def test_open_input_feed_fails(self):
        altered = self.remove_tracks('PWR_5V', lambda s: '(layer "B.Cu")' in s and '(width 1.5)' in s)
        self.assertNotEqual(altered, self.source)
        self.assertTrue(any("('U13', '5')" in e for e in self.run_check(altered)))

    def test_open_output_bypass_fails(self):
        altered = self.remove_tracks('ACT_5V', lambda s: '(start 144.25 144.9)' in s or
                                     '(end 144.25 144.9)' in s)
        self.assertNotEqual(altered, self.source)
        self.assertTrue(any("('C40', '1')" in e for e in self.run_check(altered)))

    def test_open_current_limit_fails(self):
        altered = self.remove_tracks('ACT_ILM')
        self.assertTrue(any('ACT_ILM' in e for e in self.run_check(altered)))

    def test_open_disable_clamp_fails(self):
        altered = self.remove_tracks('ACT_UVLO', lambda s: '(start 150.85 146.0375)' in s or
                                     '(end 150.85 146.0375)' in s)
        self.assertNotEqual(altered, self.source)
        self.assertTrue(any("('D3', '1')" in e for e in self.run_check(altered)))


if __name__ == '__main__':
    unittest.main()
