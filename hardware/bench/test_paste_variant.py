"""Review the variant's real copper preservation and thermal-land coverage."""
import unittest
import pcbnew as p
from build_panel import SOURCES
from paste_variant import apply
from review_details import paste_measurements

class PasteVariant(unittest.TestCase):
    def test_panel_mechanical_footprints_are_not_components(self):
        b=p.BOARD();f=p.FOOTPRINT(b);f.SetReference('MB6_1');b.Add(f)
        apply(b)
        self.assertEqual(len(list(b.GetFootprints())),1)

    def test_copper_preserved_and_manufacturer_coverage(self):
        b=p.LoadBoard(str(SOURCES['Main']))
        def copper():
            return sorted((f.GetReference(),q.GetNumber(),q.GetPosition().x,q.GetPosition().y,
                q.GetSize().x,q.GetSize().y,q.GetNetname()) for f in b.GetFootprints()
                for q in f.Pads() if q.IsOnLayer(p.F_Cu))
        original=copper();retained=apply(b,'Main');self.assertEqual(original,copper())
        selected={r:{'purchase_mpn':'test'} for r in ('U2','U7','U10')}
        _,coverage,_=paste_measurements(b,selected)
        for ref,pin,minimum,maximum in [('U2','9',86,88),('U7','5',89,91),('U10','17',84,86)]:
            value=next(r['Coverage_percent'] for r in coverage if r['Reference']==ref and r['Pad']==pin)
            self.assertTrue(minimum<value<maximum,(ref,value))

    def test_measuring_underprinted_hall_detects_deficit(self):
        b=p.LoadBoard(str(SOURCES['Main']));retained=apply(b,'Main')
        f=next(f for f in b.GetFootprints() if f.GetReference()=='U7')
        q=next(q for q in f.Pads() if q.IsOnLayer(p.F_Paste) and not q.IsOnLayer(p.F_Cu))
        q.SetSize(p.VECTOR2I(p.FromMM(.3),p.FromMM(.3)))
        _,coverage,_=paste_measurements(b,{'U7':{'purchase_mpn':'test'}})
        value=next(r['Coverage_percent'] for r in coverage if r['Pad']=='5')
        self.assertLess(value,30)

if __name__=='__main__':unittest.main()
