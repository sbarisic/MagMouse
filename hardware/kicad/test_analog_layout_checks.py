# SPDX-License-Identifier: GPL-3.0-or-later
"""Fault injection for analog connectivity, reference and review gates."""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[2]


class AnalogLayoutChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'hardware/kicad/MagMouse.kicad_pcb').read_text(encoding='utf-8')

    def check(self, source, require_reviewed=False):
        with tempfile.TemporaryDirectory(prefix='magmouse-analog-') as folder:
            board, report = Path(folder) / 'board.kicad_pcb', Path(folder) / 'report.json'
            board.write_text(source, encoding='utf-8')
            command = [sys.executable, str(ROOT / 'hardware/kicad/verify_analog_layout.py'),
                       '--board', str(board), '--output', str(report)]
            if require_reviewed:
                command.append('--require-reviewed')
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertIn(result.returncode, [0, 1], result.stderr)
            return result.returncode, json.loads(report.read_text(encoding='utf-8'))

    def test_saved_connectivity_and_filters_pass(self):
        code, report = self.check(self.source)
        self.assertEqual(code, 0)
        self.assertEqual(report['errors'], [])
        self.assertEqual(len(report['analog_nets']), 22)

    def test_unresolved_findings_block_review_freeze(self):
        code, report = self.check(self.source, require_reviewed=True)
        self.assertEqual(report['errors'], [])
        self.assertTrue(report['review_findings'])
        self.assertFalse(report['review_complete'])
        self.assertEqual(code, 1)

    def test_open_analog_connections_fail(self):
        for net in ['HALL_L', 'WHEEL_SOB', 'BTN_R_ISENSE', 'ACT_VMON']:
            with self.subTest(net=net):
                altered = re.sub(r'^\t\(segment\b.*?^\t\)\n',
                                 lambda m: '' if f'(net "{net}")' in m[0] else m[0],
                                 self.source, flags=re.M | re.S)
                self.assertNotEqual(altered, self.source)
                code, report = self.check(altered)
                self.assertEqual(code, 1)
                self.assertTrue(any(net + ': disconnected' in e for e in report['errors']))

    def test_filter_layer_change_fails(self):
        altered = re.sub(r'^\t\(segment\b.*?^\t\)\n',
                         lambda m: m[0].replace('(layer "F.Cu")', '(layer "B.Cu")')
                         if '(net "WHEEL_I_B")' in m[0] else m[0], self.source, flags=re.M | re.S)
        self.assertNotEqual(altered, self.source)
        _, report = self.check(altered)
        self.assertTrue(any('WHEEL_I_B: ADC input filter must remain front-only' in e for e in report['errors']))

    def test_missing_reference_plane_fails(self):
        altered = re.sub(r'^\t\(zone\b.*?^\t\)\n',
                         lambda m: '' if '(net "GND")' in m[0] and '(layer "In1.Cu")' in m[0] else m[0],
                         self.source, flags=re.M | re.S)
        self.assertNotEqual(altered, self.source)
        _, report = self.check(altered)
        self.assertTrue(any('no saved filled In1 ground plane' in e for e in report['errors']))

    def test_monitor_capacitor_ground_open_fails(self):
        board = pcb.LoadBoard(str(ROOT / 'hardware/kicad/MagMouse.kicad_pcb'))
        board.BuildConnectivity()
        pad = next(p for f in board.GetFootprints() if f.GetReference() == 'C36'
                   for p in f.Pads() if p.GetNumber() == '2')
        ids = {t.m_Uuid.AsString() for t in board.GetConnectivity().GetConnectedTracks(pad)}
        altered = re.sub(r'^\t\((?:segment|via)\b.*?^\t\)\n',
                         lambda m: '' if any(i in m[0] for i in ids) else m[0],
                         self.source, flags=re.M | re.S)
        self.assertNotEqual(altered, self.source)
        _, report = self.check(altered)
        self.assertTrue(any('C36.2: analog ground' in e for e in report['errors']))


if __name__ == '__main__':
    unittest.main()
