import unittest
import pcbnew as p
from straighten_tracks import candidates, mm
from shapely.geometry import LineString

class StraightenTests(unittest.TestCase):
    def board(self, points, widths=None, net='SIGNAL'):
        b=p.BOARD();n=p.NETINFO_ITEM(b,net);b.Add(n)
        for i,(a,z) in enumerate(zip(points,points[1:])):
            t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*a));t.SetEnd(p.VECTOR2I(*z))
            t.SetWidth((widths or [150000]*len(points))[i]);t.SetLayer(p.F_Cu);t.SetNetCode(n.GetNetCode());b.Add(t)
        return b

    def test_grid_steps_become_straight_with_width_preserved(self):
        b=self.board([(0,0),(50000,0),(100000,50000),(150000,50000),(200000,100000)])
        changes=candidates(b)
        self.assertEqual(len(changes),1)
        old,coords=changes[0]
        self.assertEqual(len(coords),2)
        self.assertEqual({t.GetWidth() for t in old},{150000})
        self.assertEqual(set(coords),{(0,0),(200000,100000)})

    def test_nanometre_endpoint_rounding(self):
        b=self.board([(0,0),(50000,50000),(100000,100000)])
        t=list(b.GetTracks())[0]
        a=t.GetEnd();t.SetEnd(p.VECTOR2I(a.x-1,a.y-1))
        self.assertEqual(len(candidates(b)),1)

    def test_usb_is_untouched(self):
        self.assertEqual(candidates(self.board([(0,0),(50000,0),(100000,50000)],net='USB_DP')),[])

    def test_overlapping_caps_are_joined(self):
        b=self.board([(0,0),(50000,0),(150000,0)])
        for t in b.GetTracks():
            if t.GetStart().x==50000:t.SetStart(p.VECTOR2I(100000,0))
        changes=candidates(b)
        self.assertEqual(len(changes),1)
        self.assertEqual(set(changes[0][1]),{(0,0),(150000,0)})

    def test_nonoverlapping_caps_are_not_joined(self):
        b=self.board([(0,0),(50000,0),(400000,0)])
        for t in b.GetTracks():
            if t.GetStart().x==50000:t.SetStart(p.VECTOR2I(300000,0))
        self.assertEqual(candidates(b),[])

    def test_width_transition_is_untouched(self):
        self.assertEqual(candidates(self.board([(0,0),(50000,0),(100000,50000)],widths=[150000,200000])),[])

    def test_real_corner_is_retained(self):
        b=self.board([(0,0),(500000,0),(1000000,0),(1000000,1000000)])
        _,coords=candidates(b)[0]
        self.assertIn((1000000,0),coords)
        self.assertEqual(len(coords),2)

    def test_branch_is_retained(self):
        b=self.board([(0,0),(500000,0),(1000000,0)])
        t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(500000,0));t.SetEnd(p.VECTOR2I(500000,500000))
        t.SetWidth(150000);t.SetLayer(p.F_Cu);t.SetNetCode(list(b.GetTracks())[0].GetNetCode());b.Add(t)
        self.assertEqual(candidates(b),[])

if __name__=='__main__':unittest.main()
