"""Manufacturing handoff checks against real panel and Excellon data."""
import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path
import pcbnew as p
from build_panel import HERE
from manufacturing_review import inspect,normalize_job,validate_job,verify_open_drills


class ManufacturingReview(unittest.TestCase):
    def setUp(self):
        self.board=p.LoadBoard(str(HERE/'Panel.kicad_pcb'))
        self.manifest=json.loads((HERE/'panel-manifest.json').read_text())
        with (HERE/'package/all-vias.csv').open(encoding='utf-8-sig',newline='') as f:self.vias=list(csv.DictReader(f))

    def test_current_panel_and_all_open_drills(self):
        result,holes=inspect(self.board,self.manifest,self.vias)
        self.assertEqual(result['local_manufacturing_screen'],'PASS')
        verify_open_drills(holes,HERE/'package/gerbers')

    def test_metadata_normalization_preserves_material_stack(self):
        data=json.loads((HERE/'package/gerbers/Panel-job.gbrjob').read_text())
        original=copy.deepcopy(data['MaterialStackup'])
        data['GeneralSpecs']['ImpedanceControlled']=True
        data['GeneralSpecs']['Size']={'X':151.05,'Y':139.05}
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'job.json';path.write_text(json.dumps(data))
            normalize_job(path);fixed=json.loads(path.read_text());validate_job(fixed)
            self.assertEqual(fixed['MaterialStackup'],original)

    def test_wrong_stack_or_impedance_option_rejected(self):
        data=json.loads((HERE/'package/gerbers/Panel-job.gbrjob').read_text())
        altered=copy.deepcopy(data);altered['GeneralSpecs']['ImpedanceControlled']=True
        with self.assertRaisesRegex(AssertionError,'impedance'):validate_job(altered)
        altered=copy.deepcopy(data)
        next(r for r in altered['MaterialStackup'] if r['Name']=='In1.Cu')['Thickness']=.015
        with self.assertRaisesRegex(AssertionError,'stack'):validate_job(altered)
        altered=copy.deepcopy(data)
        next(r for r in altered['FilesAttributes'] if r['Path']=='Panel-In1_Cu.g1')['FileFunction']='Copper,L3,Inr'
        with self.assertRaisesRegex(AssertionError,'file-layer'):validate_job(altered)

    def test_component_hole_in_fill_inventory_rejected(self):
        bad=copy.deepcopy(self.vias);bad[0]['UUID']='component-hole'
        with self.assertRaisesRegex(AssertionError,'component hole'):inspect(self.board,self.manifest,bad)

    def test_insufficient_tab_width_rejected(self):
        self.manifest['tab_width_mm']=3
        with self.assertRaises(AssertionError):inspect(self.board,self.manifest,self.vias)

    def test_changed_open_drill_rejected(self):
        _,holes=inspect(self.board,self.manifest,self.vias)
        holes[0]['X_mm']+=.1
        with self.assertRaisesRegex(AssertionError,'open drill'):verify_open_drills(holes,HERE/'package/gerbers')


if __name__=='__main__':unittest.main()
