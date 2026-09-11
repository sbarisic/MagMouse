"""Fault-injection checks for pricing file coverage and CAD coordinate transfer."""
from pathlib import Path
import tempfile
import unittest
import pcbnew as p
from export_quote_packages import validate_coverage, make_cpl, validate_drills, via_inventory


class QuoteChecks(unittest.TestCase):
    def setUp(self):
        self.comps = {'R1':{}, 'R2':{}, 'TP1':{}}
        self.assembly = ['R1','R2']
        self.exclusions = [{'Designator':'TP1'}]
        self.bom = [{'Designator':'R1,R2','Quantity':2}]
        self.cpl = [{'Designator':'R1'},{'Designator':'R2'}]

    def check(self):
        validate_coverage(self.comps,self.assembly,self.exclusions,self.bom,self.cpl)

    def test_complete_partition(self):
        self.check()

    def test_missing_cpl_rejected(self):
        self.cpl.pop()
        with self.assertRaisesRegex(ValueError,'coverage'): self.check()

    def test_duplicate_bom_reference_rejected(self):
        self.bom[0]['Designator'] += ',R1'
        with self.assertRaisesRegex(ValueError,'duplicate'): self.check()

    def test_silent_omission_rejected(self):
        self.comps['U1'] = {}
        with self.assertRaisesRegex(ValueError,'Unaccounted'): self.check()

    def test_wrong_quantity_rejected(self):
        self.bom[0]['Quantity'] = 5
        with self.assertRaisesRegex(ValueError,'quantity'): self.check()

    def test_cpl_origin_and_rotation(self):
        board = p.BOARD(); fp = p.FOOTPRINT(board); fp.SetReference('R1')
        fp.SetPosition(p.VECTOR2I(p.FromMM(10),p.FromMM(20))); fp.SetOrientationDegrees(-90)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'pos.csv'
            path.write_text('Ref,PosX,PosY,Rot,Side\nR1,10,-20,-90,top\n')
            self.assertEqual(make_cpl(path,['R1'],{'R1':fp})[0]['Rotation'],'270.000000')
            path.write_text('Ref,PosX,PosY,Rot,Side\nR1,10,20,-90,top\n')
            with self.assertRaisesRegex(ValueError,'origin'): make_cpl(path,['R1'],{'R1':fp})

    def test_via_drill_origin(self):
        vias = [{'Gerber/CPL X mm':10.,'Gerber/CPL Y mm':-20.,'Drill mm':.3}]
        text = '; absolute / metric / decimal\nMETRIC\n; TA.AperFunction,ViaDrill\nT1C0.300\nT1\nX10Y-20\n'
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'drill.drl'; path.write_text(text)
            validate_drills(path,vias)
            path.write_text(text.replace('Y-20','Y20'))
            with self.assertRaisesRegex(ValueError,'origin'): validate_drills(path,vias)

    def test_off_center_via_drill_overlap(self):
        board=p.BOARD();fp=p.FOOTPRINT(board);fp.SetReference('U1');board.Add(fp)
        pad=p.PAD(fp);pad.SetNumber('1');pad.SetAttribute(p.PAD_ATTRIB_SMD)
        pad.SetShape(p.PAD_SHAPE_RECT);pad.SetSize(p.VECTOR2I(p.FromMM(1),p.FromMM(1)))
        layers=p.LSET();layers.AddLayer(p.F_Cu);pad.SetLayerSet(layers);fp.Add(pad)
        via=p.PCB_VIA(board);via.SetPosition(p.VECTOR2I(p.FromMM(.6),0))
        via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));board.Add(via)
        self.assertIn('U1.1',via_inventory(board)[0]['SMD pad drill overlap'])


if __name__ == '__main__':
    unittest.main()
