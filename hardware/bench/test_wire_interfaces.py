import unittest
import pcbnew as p
from build_panel import SOURCES
from verify_wire_interfaces import verify,verify_fill,verify_fixture_alignment
from export_bench import via_inventory


class WireChecks(unittest.TestCase):
    def setUp(self):self.boards={n:p.LoadBoard(str(path)) for n,path in SOURCES.items()}

    def pad(self,name,ref,pin):
        return next(q for f in self.boards[name].GetFootprints() if f.GetReference()==ref for q in f.Pads() if q.GetNumber()==pin)

    def test_current_interfaces(self):self.assertEqual(86,verify(self.boards)['plated_wire_holes'])

    def test_wrong_mapping(self):
        q=self.pad('Wheel','J9','29');q.SetNet(self.boards['Wheel'].FindNet('GND'))
        with self.assertRaises(AssertionError):verify(self.boards)

    def test_missing_ground(self):
        q=self.pad('Main','J8','1');q.SetNet(self.boards['Main'].FindNet('+3V3'))
        with self.assertRaises(AssertionError):verify(self.boards)

    def test_paste_on_wire_land(self):
        q=self.pad('Main','J8','1');layers=q.GetLayerSet();layers.AddLayer(p.F_Paste);q.SetLayerSet(layers)
        with self.assertRaisesRegex(AssertionError,'paste'):verify(self.boards)

    def test_wire_hole_in_fill_list(self):
        b=self.boards['Encoder'];rows=via_inventory(b);verify_fill(b,rows)
        rows.append({'UUID':self.pad('Encoder','J7','1').m_Uuid.AsString()})
        with self.assertRaisesRegex(AssertionError,'component hole'):verify_fill(b,rows)

    def test_fill_coordinates_changed(self):
        b=self.boards['Encoder'];rows=via_inventory(b);rows[0]['KiCad X mm']+=1
        with self.assertRaisesRegex(AssertionError,'coordinate'):verify_fill(b,rows)

    def test_fixture_support_alignment(self):verify_fixture_alignment()

    def test_displaced_fixture_support(self):
        import json
        from build_panel import ROOT
        report=json.loads((ROOT/'mechanical/bench/generated/assembly-clearance.json').read_text())
        report['saddles'][0]['x']+=2
        with self.assertRaisesRegex(AssertionError,'saddle'):verify_fixture_alignment(report)


if __name__=='__main__':unittest.main()
