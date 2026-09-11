"""Fault injection for derived-panel source, copper, net and tab invariants."""
import copy
import json
import unittest
import pcbnew as p
from build_panel import HERE,xy
from export_bench import verify_panel


class PanelChecks(unittest.TestCase):
    def setUp(self):
        self.board=p.LoadBoard(str(HERE/'Panel.kicad_pcb'))
        self.manifest=json.loads((HERE/'panel-manifest.json').read_text())

    def test_valid_panel(self):
        self.assertEqual(verify_panel(self.board,self.manifest)['native_unrouted'],0)

    def test_stale_source(self):
        self.manifest['units']['Main']['sha256']='0'*64
        with self.assertRaises(AssertionError):verify_panel(self.board,self.manifest)

    def test_changed_track(self):
        track=next(t for t in self.board.GetTracks() if not isinstance(t,p.PCB_VIA))
        track.SetWidth(track.GetWidth()+p.FromMM(.05))
        with self.assertRaises(AssertionError):verify_panel(self.board,self.manifest)

    def test_cross_board_net(self):
        pad=next(q for f in self.board.GetFootprints() if f.GetReference().startswith('E_')
                 for q in f.Pads() if q.GetNetCode())
        pad.SetNet(self.board.FindNet('Main/GND'))
        with self.assertRaises(AssertionError):verify_panel(self.board,self.manifest)

    def test_tab_hole_inside_unit(self):
        self.manifest['tabs'][0]['holes'][0]=[47,70]
        with self.assertRaises(AssertionError):verify_panel(self.board,self.manifest)


if __name__=='__main__':unittest.main()
