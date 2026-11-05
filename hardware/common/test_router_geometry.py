import unittest
from router_geometry import route_opening,verify_sweep,verify_outer,sweep,make_routable
from shapely.geometry import box,LineString,Polygon

class RouterGeometry(unittest.TestCase):
    def test_weakened_physical_tab_rejected(self):
        from router_geometry import verify_material_tab
        material=box(-5,-5,5,5).difference(box(-.1,1,.1,6))
        with self.assertRaisesRegex(AssertionError,'full-width'):
            verify_material_tab(material,dict(center=(0,0),normal=(0,1),holes=[]))

    def test_exact_width_slot_survives(self):
        opening,paths=route_opening(box(0,0,10,2))
        self.assertGreater(opening.area,18)
        verify_sweep(opening,paths)

    def test_square_ends_fail_against_tool(self):
        original=box(0,0,10,2);opening,paths=route_opening(original)
        with self.assertRaisesRegex(AssertionError,'Unreachable'):verify_sweep(original,paths)

    def test_rounded_slot_passes(self):
        path=LineString([(1,1),(9,1)])
        verify_sweep(sweep([path]),[path])

    def test_undersized_passage(self):
        with self.assertRaises(AssertionError):route_opening(box(0,0,10,1.9))

    def test_inaccessible_pocket(self):
        pocket=box(0,0,4,4).union(box(3,1,10,1.5))
        with self.assertRaises(AssertionError):route_opening(pocket)

    def test_overcut(self):
        with self.assertRaisesRegex(AssertionError,'overcut'):
            verify_sweep(box(0,0,10,2),[LineString([(0,1),(10,1)])])

    def test_external_concavity(self):
        board=box(0,0,10,10).difference(box(4,5,5,11))
        with self.assertRaises(AssertionError):verify_outer(board)

    def test_rounding_preserves_tab_material(self):
        old=box(0,0,20,10).difference(box(2,2,8,4).union(box(13,2,18,4)))
        new,_=make_routable(old)
        self.assertTrue(new.covers(box(8,2,13,4)))
        self.assertLess(old.difference(new).area,1e-7)

if __name__=='__main__':unittest.main()
