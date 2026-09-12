"""Failure-oriented tests for the actual printed openings and exclusions."""
import csv
from dataclasses import replace
import unittest
import pcbnew as p
from build_panel import SOURCES, HERE
from paste_variant import apply
from review_details import paste_measurements, pad_polygon
from stencil_policy import POLICY, exclude_non_reflow, verify_geometry, verify_transforms


class StencilAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (HERE/'package/population.csv').open(encoding='utf-8-sig', newline='') as f:
            cls.population = list(csv.DictReader(f))

    def unit(self, name='Main'):
        board = p.LoadBoard(str(SOURCES[name]))
        apply(board, name)
        selected = {r['reference']:r for r in self.population
                    if r['board']==name and r['method']=='TOP SMT REFLOW'}
        exclude_non_reflow(board, selected)
        return board, selected

    def test_all_boards_pass_and_c90_rgb_remain(self):
        for name in SOURCES:
            board, selected = self.unit(name)
            self.assertGreaterEqual(verify_geometry(board,selected), POLICY.minimum_area_ratio)
            if name == 'Main': self.assertIn('D5',selected)
            if name == 'Wheel': self.assertIn('C90',selected)

    def test_encoder_rejects_0125mm(self):
        board, selected = self.unit('Encoder')
        with self.assertRaisesRegex(AssertionError,'release ratio'):
            verify_geometry(board,selected,replace(POLICY,thickness_mm=.125))

    def test_unintended_paste_exclusions(self):
        for ref in ['U32','U35','J8','J10']:
            with self.subTest(ref=ref):
                board, selected = self.unit()
                pad=next(q for q in board.FindFootprintByReference(ref).Pads() if q.IsOnLayer(p.F_Cu))
                layers=pad.GetLayerSet();layers.AddLayer(p.F_Paste);pad.SetLayerSet(layers)
                with self.assertRaisesRegex(AssertionError,'excluded reference'):
                    verify_geometry(board,selected)

    def test_missing_signal_land_deposit(self):
        board, selected = self.unit('Encoder')
        pad=next(q for q in board.FindFootprintByReference('U27').Pads() if q.GetNumber()=='1')
        layers=pad.GetLayerSet();layers.RemoveLayer(p.F_Paste);pad.SetLayerSet(layers)
        with self.assertRaisesRegex(AssertionError,'missing land deposit'):
            verify_geometry(board,selected)

    def test_overlapping_thermal_windows(self):
        board, selected = self.unit()
        pads=[q for q in board.FindFootprintByReference('U2').Pads() if q.IsOnLayer(p.F_Paste) and not q.IsOnLayer(p.F_Cu)]
        pads[1].SetPosition(pads[0].GetPosition())
        with self.assertRaisesRegex(AssertionError,'overlapping apertures'):
            verify_geometry(board,selected)

    def test_modified_compound_efuse_is_not_whitelisted(self):
        board, selected = self.unit()
        pad=next(q for q in board.FindFootprintByReference('U12').Pads() if q.IsOnLayer(p.F_Paste) and not q.IsOnLayer(p.F_Cu))
        pad.Move(p.VECTOR2I(p.FromMM(.02),0))
        with self.assertRaisesRegex(AssertionError,'overlapping apertures'):
            verify_geometry(board,selected)

    def test_physical_apertures_do_not_double_count_usb_and_efuse(self):
        board, selected = self.unit()
        rows,_,_=paste_measurements(board,selected)
        for ref,merged in [('J1',4),('U12',4),('U13',4)]:
            local=[r for r in rows if r['Reference']==ref]
            self.assertEqual(sum(r['Primitive_count']-1 for r in local),merged)

    def test_panel_transforms_and_missing_thermal_deposit(self):
        board, selected = self.unit('Encoder')
        rows,_,_=paste_measurements(board,selected)
        expected=[dict(Board='Encoder',**r) for r in rows]
        actual=[dict(r,Reference='E_'+r['Reference']) for r in rows]
        verify_transforms(actual,expected,{'Encoder':(0,0)})
        with self.assertRaisesRegex(AssertionError,'transformation mismatch'):
            verify_transforms(actual,expected,{'Encoder':(.01,0)})
        with self.assertRaisesRegex(AssertionError,'transformation mismatch'):
            verify_transforms(actual[1:],expected,{'Encoder':(0,0)})
        from shapely import wkt
        changed=[dict(r) for r in actual]
        # Same centroid and area, different polygon: the old summary-only
        # transform check would not identify this change.
        from shapely.affinity import scale
        changed[0]['Polygon_wkt']=scale(wkt.loads(changed[0]['Polygon_wkt']),2,.5).wkt
        with self.assertRaisesRegex(AssertionError,'transformation mismatch'):
            verify_transforms(changed,expected,{'Encoder':(0,0)})

    def test_all_copper_drills_and_placements_preserved(self):
        from export_bench import track_key, fill_vertices
        def snapshot(board):
            pads=[];footprints=[]
            for f in board.GetFootprints():
                footprints.append((f.GetReference(),tuple(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer()))
                for q in f.Pads():
                    layers=[layer for layer in (p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu,p.F_Mask,p.B_Mask) if q.IsOnLayer(layer)]
                    if not layers: continue
                    pads.append((f.GetReference(),q.GetNumber(),q.GetAttribute(),q.GetNetname(),
                        tuple(q.GetDrillSize()),q.GetDrillShape(),tuple(q.GetPosition()),q.GetOrientationDegrees(),
                        tuple((layer,pad_polygon(q,layer).wkt) for layer in layers)))
            return sorted(footprints),sorted(pads),sorted(track_key(t) for t in board.GetTracks()),fill_vertices(board)
        for name,path in SOURCES.items():
            board=p.LoadBoard(str(path));before=snapshot(board)
            apply(board,name)
            exclude_non_reflow(board,{r['reference'] for r in self.population if r['board']==name and r['method']=='TOP SMT REFLOW'})
            self.assertEqual(before,snapshot(board),name)


if __name__=='__main__': unittest.main()
