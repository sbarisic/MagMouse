"""Fault injection for ADC connectivity, reference coverage and launch review."""
import unittest
from pathlib import Path
import pcbnew as p
from verify_main_analog import verify, outside_launch

BOARD = Path(__file__).resolve().parent / 'main/Main.kicad_pcb'


class MainAnalog(unittest.TestCase):
    def test_saved_analog_review(self):
        result = verify(p.LoadBoard(str(BOARD)))
        self.assertEqual([], result['errors'])
        self.assertEqual([], result['review_findings'])

    def test_disconnected_adc_input(self):
        board = p.LoadBoard(str(BOARD))
        pad = next(q for f in board.GetFootprints() if f.GetReference() == 'U10'
                   for q in f.Pads() if q.GetNumber() == '6')
        pad.Move(p.VECTOR2I(p.FromMM(100), 0))
        self.assertTrue(verify(board)['errors'])

    def test_remote_monitor_filter(self):
        board = p.LoadBoard(str(BOARD))
        cap = next(f for f in board.GetFootprints() if f.GetReference() == 'C36')
        cap.Move(p.VECTOR2I(p.FromMM(20), 0))
        self.assertTrue(any('filter capacitor' in e for e in verify(board)['errors']))

    def test_launch_does_not_exempt_long_run(self):
        board = p.BOARD()
        track = p.PCB_TRACK(board)
        track.SetStart(p.VECTOR2I(0, 0))
        track.SetEnd(p.VECTOR2I(p.FromMM(10), 0))
        track.SetWidth(p.FromMM(.2))
        outside = outside_launch(track, (0, 0))
        self.assertEqual(1, len(outside))
        self.assertAlmostEqual(1.4, outside[0][0][0])
        self.assertEqual((10, 0), outside[0][1])

    def test_boundary_via_is_not_exempt(self):
        board = p.BOARD()
        via = p.PCB_VIA(board)
        via.SetPosition(p.VECTOR2I(p.FromMM(1.4), 0))
        via.SetWidth(p.FromMM(.45))
        self.assertTrue(outside_launch(via, (0, 0)))


if __name__ == '__main__':
    unittest.main()
