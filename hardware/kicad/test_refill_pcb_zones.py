# SPDX-License-Identifier: GPL-3.0-or-later
"""Check project-aware filling and preservation of existing routing."""

from pathlib import Path
import shutil
import tempfile
import unittest

import pcbnew as pcb

from refill_pcb_zones import refill
from verify_analog_layout import verify

SOURCE = Path(__file__).with_name('MagMouse.kicad_pcb')


def geometry(path):
    board = pcb.LoadBoard(str(path))
    tracks = sorted((t.m_Uuid.AsString(), t.GetNetname(), t.GetLayer(),
                     t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y,
                     t.GetWidth(pcb.F_Cu) if isinstance(t, pcb.PCB_VIA) else t.GetWidth())
                    for t in board.GetTracks())
    parts = sorted((f.GetReference(), f.GetPosition().x, f.GetPosition().y,
                    f.GetOrientationDegrees(), f.GetLayer()) for f in board.GetFootprints())
    return tracks, parts


class RefillChecks(unittest.TestCase):
    def test_missing_project_rejected_without_modifying_board(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / SOURCE.name
            shutil.copyfile(SOURCE, target)
            before = target.read_bytes()
            with self.assertRaisesRegex(ValueError, 'matching'):
                refill(target)
            self.assertEqual(before, target.read_bytes())

    def test_refill_preserves_project_routing_and_placement(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / SOURCE.name
            for suffix in ['.kicad_pcb', '.kicad_pro', '.kicad_dru']:
                shutil.copyfile(SOURCE.with_suffix(suffix), target.with_suffix(suffix))
            original = geometry(target)
            project = target.with_suffix('.kicad_pro').read_bytes()
            rules = target.with_suffix('.kicad_dru').read_bytes()
            report = refill(target)
            self.assertEqual(original, geometry(target))
            self.assertEqual(project, target.with_suffix('.kicad_pro').read_bytes())
            self.assertEqual(rules, target.with_suffix('.kicad_dru').read_bytes())
            self.assertEqual(report['native_unconnected_before'], report['native_unconnected_after'])
            analog = verify(pcb.LoadBoard(str(target)))
            self.assertEqual(analog['errors'], [])
            for net, metrics in analog['analog_nets'].items():
                if not net.startswith('HALL_'):
                    self.assertEqual(metrics['front_shadow_missing_mm2'], 0, net)


if __name__ == '__main__':
    unittest.main()
