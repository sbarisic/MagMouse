"""Fault-injection checks for main source controls and actuator copper; KiCad Python."""
import unittest
from pathlib import Path
import pcbnew as p
from verify_main_controls import verify

BOARD = Path(__file__).resolve().parent / 'main/Main.kicad_pcb'


def move_pad(board, reference, number):
    pad = next(q for f in board.GetFootprints() if f.GetReference() == reference
               for q in f.Pads() if q.GetNumber() == number)
    pad.Move(p.VECTOR2I(p.FromMM(100), 0))


class MainControls(unittest.TestCase):
    def test_saved_routing(self):
        self.assertEqual([], verify(p.LoadBoard(str(BOARD)))['errors'])

    def test_open_cc_detector(self):
        board = p.LoadBoard(str(BOARD))
        move_pad(board, 'U11', '2')
        self.assertTrue(any('USB_CC2: disconnected' in e for e in verify(board)['errors']))

    def test_open_wheel_enable(self):
        board = p.LoadBoard(str(BOARD))
        move_pad(board, 'J8', '24')
        self.assertTrue(any('ACT_DRIVE_EN: disconnected' in e for e in verify(board)['errors']))

    def test_open_vbus_monitor_supply(self):
        board = p.LoadBoard(str(BOARD))
        move_pad(board, 'R65', '1')
        self.assertTrue(any('VBUS_USB:' in e and 'R65' in e for e in verify(board)['errors']))

    def test_wheel_feed_neckdown(self):
        board = p.LoadBoard(str(BOARD))
        for t in board.GetTracks():
            if not isinstance(t, p.PCB_VIA) and t.GetNetname() == 'ACT_5V' and t.GetLayer() == p.In2_Cu and 41<p.ToMM(t.GetPosition().y)<45:
                t.SetWidth(p.FromMM(.15))
        self.assertTrue(any('J10.1: exceeds copper resistance' in e for e in verify(board)['errors']))

    def test_insufficient_power_wire_barrel(self):
        board = p.LoadBoard(str(BOARD))
        pad=next(q for f in board.GetFootprints() if f.GetReference()=='J10' for q in f.Pads() if q.GetNumber()=='1')
        pad.SetDrillSize(p.VECTOR2I(p.FromMM(.8),p.FromMM(.8)))
        self.assertTrue(any('J10.1: fewer than three' in e for e in verify(board)['errors']))

    def test_lost_button_ground_spreader(self):
        board = p.LoadBoard(str(BOARD))
        for z in board.Zones():
            if z.GetZoneName() == 'ACTUATOR_U5_GND_B.Cu':
                z.SetZoneName('Removed spreader')
        self.assertTrue(any('ACTUATOR_U5_GND_B.Cu: missing' in e for e in verify(board)['errors']))


if __name__ == '__main__':
    unittest.main()
