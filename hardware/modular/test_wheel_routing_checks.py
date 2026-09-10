"""Exercise routing guards against actual board mutations, with KiCad Python."""
import unittest
from pathlib import Path
import pcbnew as p
from verify_wheel_routing import verify

BOARD=Path(__file__).resolve().parent/'wheel/Wheel.kicad_pcb'


class WheelRouting(unittest.TestCase):
    def test_saved_routing(self):
        self.assertEqual([],verify(p.LoadBoard(str(BOARD)))['errors'])

    def test_missing_reference_plane(self):
        b=p.LoadBoard(str(BOARD))
        for z in b.Zones():
            if z.GetLayer()==p.In1_Cu:z.SetNet(b.FindNet('ACT_5V'))
        errors=verify(b)['errors']
        self.assertTrue(any('saved ground outline' in e for e in errors))
        self.assertTrue(any('ground shadow' in e for e in errors))

    def test_narrow_phase_launch(self):
        b=p.LoadBoard(str(BOARD));t=next(t for t in b.GetTracks() if t.GetNetname()=='WHEEL_PHASE_A')
        t.SetWidth(p.FromMM(.1))
        self.assertTrue(any('phase launch below' in e for e in verify(b)['errors']))

    def test_phase_encroaches_on_sensor(self):
        b=p.LoadBoard(str(BOARD));tracks=list(b.GetTracks())
        sense=next(t for t in tracks if t.GetNetname()=='WHEEL_SOA')
        phase=next(t for t in tracks if t.GetNetname()=='WHEEL_PHASE_A')
        phase.SetStart(sense.GetStart());phase.SetEnd(sense.GetEnd())
        # A direct crossing may cause KiCad to propagate the shorted net before
        # geometric inspection. Either guard must reject the changed board.
        self.assertTrue(any('switching copper projection' in e or 'changed a copper/pad net' in e for e in verify(b)['errors']))

    def test_adc_signal_via(self):
        b=p.LoadBoard(str(BOARD));t=next(t for t in b.GetTracks() if t.GetNetname()=='WHEEL_I_A')
        v=p.PCB_VIA(b);v.SetPosition(t.GetStart());v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(t.GetNet());b.Add(v)
        self.assertTrue(any('WHEEL_I_A: must stay front-only' in e for e in verify(b)['errors']))

    def test_disconnected_spi_pad(self):
        b=p.LoadBoard(str(BOARD));pad=next(q for f in b.GetFootprints() if f.GetReference()=='U26' for q in f.Pads() if q.GetNumber()=='3')
        pad.SetPosition(p.VECTOR2I(p.FromMM(52),p.FromMM(55)))
        errors=verify(b)['errors']
        self.assertTrue(any('ADC2_SCLK_LOCAL: whole-board endpoint continuity failed' in e for e in errors))


if __name__=='__main__':unittest.main()
