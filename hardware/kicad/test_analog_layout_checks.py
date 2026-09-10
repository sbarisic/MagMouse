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
from verify_analog_layout import split_findings

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
        self.assertFalse(report['fixed_placement_review_complete'])
        self.assertTrue(report['deferred_mechanical_findings'])
        self.assertFalse(any(f['net'].startswith('HALL_') for f in report['review_findings']))
        self.assertEqual(code, 1)

    def test_only_hall_geometry_can_be_deferred(self):
        hall = {'kind': 'reference_shadow', 'net': 'HALL_R'}
        fixed = {'kind': 'switching_proximity', 'net': 'WHEEL_SOA', 'aggressor': 'WHEEL_PHASE_A'}
        button = {'kind': 'long_analog_net', 'net': 'BTN_R_ISENSE'}
        self.assertEqual(split_findings([hall, fixed, button]), ([fixed, button], [hall]))

    def test_fixed_front_traces_have_saved_reference_coverage(self):
        _, report = self.check(self.source)
        for net, metrics in report['analog_nets'].items():
            if not net.startswith('HALL_'):
                self.assertEqual(metrics['front_shadow_missing_mm2'], 0, net)

    def test_control_reroutes_preserve_separation_and_reference(self):
        code, report = self.check(self.source)
        self.assertEqual(code, 0)
        self.assertEqual(len(report['guarded_switching_separations']), 5)
        self.assertTrue(all(pair['passed'] for pair in report['guarded_switching_separations']))
        for net in ['BTN_R_IN2', 'DRV_INHC']:
            self.assertEqual(report['control_route_checks'][net]['front_shadow_missing_mm2'], 0)

    def test_removed_control_branch_cannot_return_beside_wheel_sense(self):
        # Reintroduce the former B.Cu IN2 branch beside the SOA transition via.
        # This 1.9 mm branch stays below the control copper-length ceiling;
        # the default check must reject its coupling geometry independently
        # of the other, still-open analog review findings.
        segment = '''\t(segment
        (start 134.35 162.8)
        (end 134.35 160.9)
        (width 0.15)
        (layer "B.Cu")
        (net "BTN_R_IN2")
        (uuid "00000000-0000-4000-8000-000000000034")
\t)
'''
        altered = self.source.rstrip()[:-1] + segment + ')\n'
        code, report = self.check(altered)
        self.assertEqual(code, 1)
        self.assertTrue(any('WHEEL_SOA/BTN_R_IN2: guarded switching separation' in e
                            for e in report['errors']))
        self.assertFalse(any('BTN_R_IN2: control route exceeds' in e for e in report['errors']))

    def test_open_control_reroutes_fail(self):
        for net in ['BTN_R_IN2', 'DRV_INHC']:
            with self.subTest(net=net):
                altered = re.sub(r'^\t\(segment\b.*?^\t\)\n',
                                 lambda m: '' if f'(net "{net}")' in m[0] else m[0],
                                 self.source, flags=re.M | re.S)
                code, report = self.check(altered)
                self.assertEqual(code, 1)
                self.assertTrue(any(net + ': disconnected' in e for e in report['errors']))

    def test_redundant_brake_output_copper_fails_length_guard(self):
        segment = next(m[0] for m in re.finditer(r'^\t\(segment\b.*?^\t\)\n',
                       self.source, re.M | re.S) if '(net "BRAKE_OUT")' in m[0])
        # Isolated extra copper does not disconnect any required pad. Native DRC
        # also rejects this fixture; the focused check must detect its length.
        segment = re.sub(r'\(start [^)]+\)', '(start 70 70)', segment)
        segment = re.sub(r'\(end [^)]+\)', '(end 90 70)', segment)
        segment = re.sub(r'\(uuid "[^"]+"\)',
                         '(uuid "00000000-0000-4000-8000-000000000033")', segment)
        altered = self.source.rstrip()[:-1] + segment + ')\n'
        code, report = self.check(altered)
        self.assertEqual(code, 1)
        self.assertTrue(any('BRAKE_OUT: total copper' in e for e in report['errors']))

    def test_open_analog_connections_fail(self):
        for net in ['HALL_L', 'WHEEL_SOB', 'BTN_R_ISENSE', 'ACT_VMON']:
            with self.subTest(net=net):
                altered = re.sub(r'^\t\(segment\b.*?^\t\)\n',
                                 lambda m: '' if f'(net "{net}")' in m[0] else m[0],
                                 self.source, flags=re.M | re.S)
                self.assertNotEqual(altered, self.source)
                code, report = self.check(altered, require_reviewed=True)
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
