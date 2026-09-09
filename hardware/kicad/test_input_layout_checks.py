# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify that input copper checks detect physical opens in saved board copies."""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class InputLayoutChecks(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / 'hardware/kicad/MagMouse.kicad_pcb').read_text(encoding='utf-8')

    def run_check(self, source):
        with tempfile.TemporaryDirectory(prefix='magmouse-input-') as folder:
            board, report = Path(folder) / 'MagMouse.kicad_pcb', Path(folder) / 'check.json'
            board.write_text(source, encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'hardware/kicad/verify_input_layout.py'),
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

    def test_open_protected_feed_fails(self):
        altered = self.remove_tracks('PWR_5V', lambda s: '(width 2)' in s)
        self.assertNotEqual(altered, self.source)
        self.assertTrue(any("('C1', '1')" in e for e in self.run_check(altered)))

    def test_open_output_bypass_fails(self):
        altered = self.remove_tracks('PWR_5V', lambda s: '(start 110.65 107.9)' in s or
                                    '(end 110.65 107.9)' in s)
        self.assertNotEqual(altered, self.source)
        self.assertTrue(any("('C88', '1')" in e for e in self.run_check(altered)))

    def test_open_current_limit_fails(self):
        altered = self.remove_tracks('USB_ILM')
        self.assertTrue(any('USB_ILM' in e for e in self.run_check(altered)))

    def test_open_source_command_fails(self):
        altered = self.remove_tracks('SOURCE_3A')
        self.assertTrue(any('SOURCE_3A' in e for e in self.run_check(altered)))

    def test_open_cc_input_fails(self):
        altered = self.remove_tracks('USB_CC1')
        self.assertTrue(any("('U11', '1')" in e for e in self.run_check(altered)))

    def test_open_typec_supply_fails(self):
        altered = self.remove_tracks('+3V3', lambda s: '(layer "In2.Cu")' in s and '(width 0.5)' in s)
        self.assertNotEqual(altered, self.source)
        self.assertTrue(any("('U11', '12')" in e for e in self.run_check(altered)))

    def test_floating_sink_mode_fails(self):
        altered = self.remove_tracks('GND', lambda s: '(start 137.4 110.825)' in s or
                                    '(end 137.4 110.825)' in s)
        self.assertNotEqual(altered, self.source)
        self.assertTrue(any("('U11', '3')" in e for e in self.run_check(altered)))


if __name__ == '__main__':
    unittest.main()
