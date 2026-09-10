"""Negative checks against the actual wheel PCB; run with KiCad Python."""
import tempfile
import unittest
from pathlib import Path
import pcbnew as p
from verify_wheel_placement import review

ROOT=Path(__file__).resolve().parents[2]
BOARD=ROOT/'hardware/modular/wheel/Wheel.kicad_pcb'
NETLIST=ROOT/'build/modular/wheel-review/netlist.xml'
DRC=ROOT/'build/modular/wheel-drc.json'


class WheelPlacement(unittest.TestCase):
    def test_saved_placement(self):
        result=review(BOARD,NETLIST,DRC)
        self.assertEqual([],result['errors'])
        self.assertEqual(result['unconnected_items'],0)

    def mutate(self,edit):
        b=p.LoadBoard(str(BOARD));edit(b,{f.GetReference():f for f in b.GetFootprints()})
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'mutation.kicad_pcb';p.SaveBoard(str(path),b)
            # The unchanged DRC report is only a fixture. These mutations must
            # fail the independent geometric/net checks, not rely on fresh DRC.
            return review(path,NETLIST,DRC)['errors']

    def test_connector_rotated_wrong_way(self):
        errors=self.mutate(lambda b,f:f['J9'].SetOrientationDegrees(0))
        self.assertTrue(any('cable contract' in e for e in errors))

    def test_adc_moved_to_phase_side(self):
        errors=self.mutate(lambda b,f:f['U23'].SetPosition(p.VECTOR2I(p.FromMM(28),p.FromMM(46))))
        self.assertTrue(any('phase-exit side' in e for e in errors))

    def test_current_channel_pad_wrong_net(self):
        def edit(b,f):
            pads={pad.GetNumber():pad for pad in f['U23'].Pads()}
            pads['15'].SetNet(pads['16'].GetNet())
        self.assertTrue(any('wrong net WHEEL_I_A' in e for e in self.mutate(edit)))


if __name__=='__main__':unittest.main()
