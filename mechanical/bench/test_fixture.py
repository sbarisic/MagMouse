import json,unittest
from pathlib import Path
from build_fixture import PARAMS,validate_configuration,block,volume


class FixtureChecks(unittest.TestCase):
    def test_configuration(self):validate_configuration(PARAMS)
    def test_joint_clearance_rejected(self):
        with self.assertRaisesRegex(AssertionError,'clearance'):validate_configuration(dict(PARAMS,board_under_height=6))
    def test_missing_stop_rejected(self):
        with self.assertRaisesRegex(AssertionError,'Stop'):validate_configuration(dict(PARAMS,button_travel=5))
    def test_open_magnet_pocket_rejected(self):
        with self.assertRaisesRegex(AssertionError,'retaining'):validate_configuration(dict(PARAMS,magnet_diameter=9))
    def test_overlap_detection(self):
        a=block(10,10,1);b=block(2,2,2,0,0,.5)
        self.assertGreater(volume(a.intersect(b)),0)
    def test_exported_solids(self):
        from build123d import import_step
        folder=Path(__file__).parent/'generated';report=json.loads((folder/'validation.json').read_text())
        for row in report['parts']:
            part=import_step(folder/(row['name']+'.step'))
            self.assertTrue(part.is_valid,row['name']);self.assertEqual(1,len(part.solids()))
            self.assertLessEqual(max(part.bounding_box().size.X,part.bounding_box().size.Y),180)


if __name__=='__main__':unittest.main()
