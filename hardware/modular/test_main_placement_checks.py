"""Negative checks for the real split main PCB. Run with KiCad Python."""
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path
import pcbnew as p
from verify_main_placement import review

ROOT=Path(__file__).resolve().parents[2]
BOARD=ROOT/'hardware/modular/main/Main.kicad_pcb'
NETLIST=ROOT/'build/modular/main-review/netlist.xml'
DRC=ROOT/'build/modular/main-drc.json'


class MainPlacement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate inputs from current CAD; an old build-cache netlist can hide
        # or falsely report schematic/placement changes.
        cli=Path(sys.executable).with_name('kicad-cli.exe')
        NETLIST.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run([str(cli),'sch','export','netlist','--format','kicadxml',
            '-o',str(NETLIST),str(BOARD.with_suffix('.kicad_sch'))],check=True,capture_output=True)
        subprocess.run([str(cli),'pcb','drc','--schematic-parity','--format','json',
            '--output',str(DRC),str(BOARD)],check=True,capture_output=True)

    def test_saved_placement(self):
        self.assertEqual([],review(BOARD,NETLIST,DRC)['errors'])

    def mutate(self,edit):
        b=p.LoadBoard(str(BOARD));edit(b,{f.GetReference():f for f in b.GetFootprints()})
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'Main.kicad_pcb';p.SaveBoard(str(path),b)
            return review(path,NETLIST,DRC)['errors']

    def test_component_outside_contour(self):
        errors=self.mutate(lambda b,f:f['U12'].SetPosition(p.VECTOR2I(p.FromMM(2),p.FromMM(10))))
        self.assertTrue(any('U12: courtyard outside' in e for e in errors))

    def test_wrong_wire_array_orientation(self):
        errors=self.mutate(lambda b,f:f['J8'].SetOrientationDegrees(180))
        self.assertTrue(any('solder-array position/orientation' in e for e in errors))

    def test_wrong_optical_datum(self):
        errors=self.mutate(lambda b,f:f['U35'].SetPosition(p.VECTOR2I(p.FromMM(41.5),p.FromMM(72.5))))
        self.assertTrue(any('Optical datum changed' in e for e in errors))


if __name__=='__main__':unittest.main()
