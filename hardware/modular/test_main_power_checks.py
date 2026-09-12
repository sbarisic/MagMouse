"""Negative copper checks for the shaped main's input power; KiCad Python."""
import unittest
from pathlib import Path
import pcbnew as p
from verify_main_power import verify, verify_stackup

BOARD = Path(__file__).resolve().parent / 'main/Main.kicad_pcb'


class MainPower(unittest.TestCase):
    def test_wrong_inductor_land_pattern(self):
        board = p.LoadBoard(str(BOARD))
        pad = next(q for f in board.GetFootprints() if f.GetReference() == 'L1' for q in f.Pads())
        pad.SetSize(p.VECTOR2I(p.FromMM(1.1),p.FromMM(3.7)))
        self.assertTrue(any('L1 recommended land' in e for e in verify(board)['errors']))

    def test_saved_routing(self):
        self.assertEqual([], verify(p.LoadBoard(str(BOARD)))['errors'])
        self.assertEqual([], verify_stackup(BOARD.read_text(encoding='utf-8')))

    def test_disconnected_output_bypass(self):
        board = p.LoadBoard(str(BOARD))
        cap = next(f for f in board.GetFootprints() if f.GetReference() == 'C88')
        cap.Move(p.VECTOR2I(0, -p.FromMM(8)))
        errors = verify(board)['errors']
        self.assertTrue(any('PWR_5V:' in e and 'C88' in e for e in errors))

    def test_insufficient_input_vias(self):
        board = p.LoadBoard(str(BOARD))
        for v in board.GetTracks():
            if isinstance(v, p.PCB_VIA) and v.GetNetname() == 'VBUS_USB' and p.ToMM(v.GetPosition().y) < 12:
                v.SetDrill(p.FromMM(.2))
        self.assertTrue(any('power-transition vias' in e for e in verify(board)['errors']))

    def test_power_neckdown(self):
        board = p.LoadBoard(str(BOARD))
        for t in board.GetTracks():
            if t.GetNetname() == 'PWR_5V' and not isinstance(t, p.PCB_VIA) and t.GetLayer() == p.In2_Cu:
                t.SetWidth(p.FromMM(.15))
        self.assertTrue(any('resistance regression budget' in e for e in verify(board)['errors']))

    def test_missing_reference_plane(self):
        board = p.LoadBoard(str(BOARD))
        for z in board.Zones():
            if not z.GetIsRuleArea() and z.GetLayer() == p.In1_Cu:
                z.SetNet(board.FindNet('PWR_5V'))
        self.assertTrue(any('saved ground reference outline' in e for e in verify(board)['errors']))

    def test_ilimit_input_disconnected(self):
        board = p.LoadBoard(str(BOARD))
        pad = next(q for f in board.GetFootprints() if f.GetReference() == 'U19'
                   for q in f.Pads() if q.GetNumber() == '3')
        pad.Move(p.VECTOR2I(0, -p.FromMM(12)))
        self.assertTrue(any('USB_ILM:' in e for e in verify(board)['errors']))

    def test_switch_node_via(self):
        board = p.LoadBoard(str(BOARD))
        t = next(t for t in board.GetTracks() if t.GetNetname() == 'BUCK_SW')
        via = p.PCB_VIA(board); via.SetPosition(t.GetStart()); via.SetNet(t.GetNet())
        via.SetWidth(p.FromMM(.6)); via.SetDrill(p.FromMM(.3)); via.SetLayerPair(p.F_Cu, p.B_Cu)
        board.Add(via)
        self.assertTrue(any('BUCK_SW must stay' in e for e in verify(board)['errors']))


if __name__ == '__main__':
    unittest.main()
