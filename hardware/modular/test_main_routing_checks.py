"""Reject open digital paths and a damaged saved reference plane."""
import unittest
from pathlib import Path
import pcbnew as p
from verify_main_routing import verify

BOARD = Path(__file__).resolve().parent / 'main/Main.kicad_pcb'


class MainRouting(unittest.TestCase):
    def test_saved_complete_routing(self):
        report = verify(p.LoadBoard(str(BOARD)))
        self.assertEqual([], report['errors'])
        self.assertEqual([], report['review_findings'])
        self.assertEqual(0, report['native_unconnected'])

    def test_open_spi3_header(self):
        board = p.LoadBoard(str(BOARD))
        pad = next(q for f in board.GetFootprints() if f.GetReference() == 'J8'
                   for q in f.Pads() if q.GetNumber() == '10')
        pad.Move(p.VECTOR2I(p.FromMM(100), 0))
        result = verify(board)
        self.assertTrue(any('SPI3 path missing' in e for e in result['errors']))
        self.assertGreater(result['native_unconnected'], 0)

    def test_missing_saved_ground(self):
        board = p.LoadBoard(str(BOARD))
        for zone in board.Zones():
            if not zone.GetIsRuleArea() and zone.GetLayer() == p.In1_Cu:
                zone.SetFilledPolysList(p.In1_Cu, p.SHAPE_POLY_SET())
        result = verify(board)
        self.assertTrue(any('saved ground outline' in e for e in result['errors']))

    def test_reference_plane_track(self):
        board = p.LoadBoard(str(BOARD))
        track = p.PCB_TRACK(board)
        track.SetLayer(p.In1_Cu)
        track.SetStart(p.VECTOR2I(p.FromMM(5), p.FromMM(50)))
        track.SetEnd(p.VECTOR2I(p.FromMM(6), p.FromMM(50)))
        track.SetWidth(p.FromMM(.15))
        board.Add(track)
        self.assertIn('A routed track occupies the In1 ground reference', verify(board)['errors'])

    def test_inner_trace_reference_void(self):
        board = p.LoadBoard(str(BOARD))
        track = max((t for t in board.GetTracks() if not isinstance(t,p.PCB_VIA)
                     and t.GetNetname()=='CS_DRV8316' and t.GetLayer()!=p.F_Cu),key=lambda t:t.GetLength())
        middle=(track.GetStart()+track.GetEnd())/2
        hole=p.SHAPE_POLY_SET();hole.NewOutline()
        for dx,dy in [(-.06,-.06),(.06,-.06),(.06,.06),(-.06,.06)]:
            hole.Append(middle.x+p.FromMM(dx),middle.y+p.FromMM(dy))
        for zone in board.Zones():
            if not zone.GetIsRuleArea() and zone.GetLayer()==p.In1_Cu:
                filled=p.SHAPE_POLY_SET(zone.GetFilledPolysList(p.In1_Cu))
                filled.BooleanSubtract(hole);zone.SetFilledPolysList(p.In1_Cu,filled)
        self.assertTrue(any(f['kind']=='primary_reference_gap' and f['net']=='CS_DRV8316'
                            for f in verify(board)['review_findings']))

    def test_return_vias_need_secondary_copper(self):
        board=p.LoadBoard(str(BOARD))
        for zone in board.Zones():
            if not zone.GetIsRuleArea() and zone.GetLayer() in [p.In2_Cu,p.B_Cu]:zone.UnFill()
        self.assertTrue(any('main return copper is missing' in e for e in verify(board)['errors']))


if __name__ == '__main__':
    unittest.main()
