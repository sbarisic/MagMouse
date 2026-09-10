# SPDX-License-Identifier: GPL-3.0-or-later
"""Prove the layout check rejects open copper despite unchanged schematic nets.

Run with KiCad's Python. Each check gets a fresh process to isolate pcbnew's
native board ownership and test only the saved PCB that a reviewer receives.
"""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[2]


class BuckLayoutChecks(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / 'hardware/kicad/MagMouse.kicad_pcb').read_text(encoding='utf-8')

    def run_check(self, source):
        with tempfile.TemporaryDirectory(prefix='magmouse-buck-') as folder:
            board = Path(folder) / 'MagMouse.kicad_pcb'
            output = Path(folder) / 'check.json'
            board.write_text(source, encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'hardware/kicad/verify_buck_layout.py'),
                                     '--board', str(board), '--output', str(output)],
                                    capture_output=True, text=True)
            self.assertIn(result.returncode, [0, 1], result.stderr)
            return json.loads(output.read_text(encoding='utf-8'))['errors']

    def remove_segment(self, predicate):
        segment = next(m for m in re.finditer(r'^\t\(segment\b.*?^\t\)\n', self.source, re.M | re.S)
                       if predicate(m[0]))
        return self.source[:segment.start()] + self.source[segment.end():]

    def test_current_layout_passes(self):
        self.assertEqual(self.run_check(self.source), [])

    def test_open_switch_route_fails(self):
        altered = self.remove_segment(lambda s: '(net "BUCK_SW")' in s)
        self.assertTrue(any("('L1', '1')" in error for error in self.run_check(altered)))

    def test_open_voltage_sense_fails(self):
        # Other distributed +3V3 branches also use 0.15 mm tracks now. Cut the
        # actual sense-pad connections instead of the first track of that width.
        board = pcb.LoadBoard(str(ROOT / 'hardware/kicad/MagMouse.kicad_pcb'))
        pad = next(p for f in board.GetFootprints() if f.GetReference() == 'U2'
                   for p in f.Pads() if p.GetNumber() == '6')
        ids = {t.m_Uuid.AsString() for t in board.GetTracks()
               if not isinstance(t, pcb.PCB_VIA) and t.GetNetname() == '+3V3'
               and t.GetLayer() == pcb.F_Cu
               and (pad.HitTest(t.GetStart()) or pad.HitTest(t.GetEnd()))}
        self.assertTrue(ids, 'Expected copper touching U2 voltage-sense pad')
        altered = re.sub(r'^\t\(segment\b.*?^\t\)\n',
                         lambda m: '' if any(uid in m[0] for uid in ids) else m[0],
                         self.source, flags=re.M | re.S)
        self.assertTrue(any("('U2', '6')" in error for error in self.run_check(altered)))


if __name__ == '__main__':
    unittest.main()
