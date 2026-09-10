# SPDX-License-Identifier: GPL-3.0-or-later
"""Fault-injection tests for USB copper checks; run with KiCad's Python."""
import re
import tempfile
import unittest
from pathlib import Path
import pcbnew as pcb
from verify_usb_layout import verify, verify_stackup, ROOT


class UsbLayoutChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'hardware/kicad/MagMouse.kicad_pcb').read_text(encoding='utf-8')

    def load(self, source=None):
        with tempfile.TemporaryDirectory(prefix='magmouse-usb-') as folder:
            path = Path(folder) / 'MagMouse.kicad_pcb'
            path.write_text(self.source if source is None else source, encoding='utf-8')
            return pcb.LoadBoard(str(path))

    def without_net(self, net, kind='segment'):
        return re.sub(r'^\t\(' + kind + r'\b.*?^\t\)\n',
                      lambda m: '' if f'(net "{net}")' in m[0] else m[0],
                      self.source, flags=re.M | re.S)

    def test_changed_reference_dielectric_is_detected(self):
        self.assertEqual(verify_stackup(self.source), [])
        altered = self.source.replace('(thickness 0.109)', '(thickness 0.2)', 1)
        self.assertNotEqual(altered, self.source)
        self.assertTrue(any('dielectric 1' in e for e in verify_stackup(altered)))

    def test_saved_board_passes(self):
        self.assertEqual(verify(self.load())['errors'], [])

    def test_each_data_leg_open_is_detected(self):
        for net in ['USB_DP', 'USB_DM', 'MCU_USB_DP', 'MCU_USB_DM']:
            with self.subTest(net=net):
                errors = verify(self.load(self.without_net(net)))['errors']
                self.assertTrue(any(net in error for error in errors), errors)

    def test_wrong_width_is_detected(self):
        board = self.load()
        track = next(t for t in board.GetTracks() if t.GetNetname() == 'USB_DP')
        track.SetWidth(pcb.FromMM(0.2))
        self.assertTrue(any('width' in e for e in verify(board)['errors']))

    def test_signal_layer_change_is_detected(self):
        board = self.load()
        track = next(t for t in board.GetTracks() if t.GetNetname() == 'USB_DP')
        track.SetLayer(pcb.B_Cu)
        self.assertTrue(any('F.Cu' in e for e in verify(board)['errors']))

    def test_signal_via_is_detected(self):
        board = self.load()
        track = next(t for t in board.GetTracks() if t.GetNetname() == 'USB_DP')
        via = pcb.PCB_VIA(board)
        via.SetPosition(track.GetStart())
        via.SetWidth(pcb.FromMM(0.6))
        via.SetDrill(pcb.FromMM(0.3))
        via.SetViaType(pcb.VIATYPE_THROUGH)
        via.SetLayerPair(pcb.F_Cu, pcb.B_Cu)
        via.SetNet(track.GetNet())
        board.Add(via)
        self.assertTrue(any('signal vias' in e for e in verify(board)['errors']))

    def test_missing_saved_plane_is_detected(self):
        board = self.load()
        for zone in board.Zones():
            if not zone.GetIsRuleArea() and zone.GetLayer() == pcb.In1_Cu:
                zone.UnFill()
        self.assertTrue(any('reference' in e for e in verify(board)['errors']))

    def test_local_plane_void_is_detected_even_with_connected_ground(self):
        board = self.load()
        track = max((t for t in board.GetTracks() if t.GetNetname() == 'USB_DP'),
                    key=lambda t: t.GetLength())
        middle = (track.GetStart() + track.GetEnd()) / 2
        hole = pcb.SHAPE_POLY_SET()
        hole.NewOutline()
        # A 0.10 mm notch at the trace centerline is intentionally much smaller
        # than the complete plane. A global ground-net continuity check misses it.
        for dx, dy in [(-0.05, -0.05), (0.05, -0.05), (0.05, 0.05), (-0.05, 0.05)]:
            hole.Append(middle.x + pcb.FromMM(dx), middle.y + pcb.FromMM(dy))
        for zone in board.Zones():
            if zone.GetIsRuleArea() or zone.GetLayer() != pcb.In1_Cu:
                continue
            filled = pcb.SHAPE_POLY_SET(zone.GetFilledPolysList(pcb.In1_Cu))
            filled.BooleanSubtract(hole)
            zone.SetFilledPolysList(pcb.In1_Cu, filled)
        report = verify(board)
        self.assertGreater(report['uncovered_reference_area_sum_mm2'], 0)
        self.assertTrue(any('USB reference' in e for e in report['errors']))
        self.assertFalse(any('ESD grounding' in e for e in report['errors']))

    def test_direct_esd_ground_via_removal_is_detected(self):
        board = self.load()
        pad = next(p for f in board.GetFootprints() if f.GetReference() == 'U1'
                   for p in f.Pads() if p.GetNumber() == '3')
        ids = {t.m_Uuid.AsString() for t in board.GetTracks()
               if isinstance(t, pcb.PCB_VIA) and pad.HitTest(t.GetPosition())}
        self.assertTrue(ids)
        source = re.sub(r'^\t\(via\b.*?^\t\)\n',
                        lambda m: '' if any(uid in m[0] for uid in ids) else m[0],
                        self.source, flags=re.M | re.S)
        self.assertTrue(any('ESD grounding' in e for e in verify(self.load(source))['errors']))

    def test_pair_spacing_loss_is_detected(self):
        board = self.load()
        for track in board.GetTracks():
            if track.GetNetname() == 'USB_DM':
                track.Move(pcb.VECTOR2I(pcb.FromMM(1), 0))
        self.assertTrue(any('spacing' in e for e in verify(board)['errors']))


if __name__ == '__main__':
    unittest.main()
