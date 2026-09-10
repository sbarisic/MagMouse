"""Regression mutations against real exported schematic netlists.

Run export_review.py for both modular projects first, then:
python -m unittest discover -s hardware/modular -p test_split_checks.py
"""
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

from verify_split import verify

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"build/modular/main-netlist.xml"
MAIN=ROOT/"build/modular/main-review/netlist.xml"
WHEEL=ROOT/"build/modular/wheel-review/netlist.xml"


class SplitChecks(unittest.TestCase):
    def test_exported_projects(self):
        result=verify(BASE,MAIN,WHEEL)
        self.assertEqual([],result["errors"])
        self.assertEqual(988,result["preserved_baseline_pin_checks"])
        self.assertTrue(result["open_review_gates"])
        self.assertGreater(result["wheel_rail"]["bulk_initial_and_endurance_screen_uF"],47)
        self.assertFalse(result["wheel_rail"]["meets_effective_requirement"])
        self.assertLess(result["wheel_rail"]["conditional_transient"]["peak_before_unmodeled_inductance_V"],6.5)

    def mutate(self,board,callback):
        source=MAIN if board=="main" else WHEEL
        tree=ET.parse(source)
        callback(tree)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"netlist.xml"
            tree.write(path)
            return verify(BASE,path if board=="main" else MAIN,path if board=="wheel" else WHEEL)["errors"]

    def test_wrong_cable_pin(self):
        def edit(tree):
            p=next(p for p in tree.findall("./nets/net/node") if p.get("ref")=="J9" and p.get("pin")=="2")
            p.set("pin","4")
        self.assertTrue(any("Signal cable pin" in e for e in self.mutate("wheel",edit)))

    def test_unreversed_wheel_connector(self):
        def edit(tree):
            for node in tree.findall('./nets/net/node'):
                if node.get('ref')=='J9':node.set('pin',str(31-int(node.get('pin'))))
        self.assertTrue(any('Signal cable pin' in e for e in self.mutate('wheel',edit)))

    def test_fault_pullup_not_strengthened(self):
        def edit(tree):tree.find('./components/comp[@ref="R88"]/value').text="10k"
        self.assertTrue(any("startup threshold" in e for e in self.mutate("wheel",edit)))

    def test_enable_pulldown_too_weak(self):
        def edit(tree):tree.find('./components/comp[@ref="R84"]/value').text="100k"
        self.assertTrue(any("may wake" in e for e in self.mutate("wheel",edit)))

    def test_analog_pin_moved_to_different_net(self):
        def edit(tree):
            n=next(n for n in tree.findall("./nets/net") if n.get("name")=="WHEEL_I_A")
            n.set("name","WHEEL_PHASE_A")
        self.assertTrue(any("changed net" in e for e in self.mutate("wheel",edit)))

    def test_bulk_or_tvs_reversed(self):
        for ref in ('C90','D6'):
            with self.subTest(ref=ref):
                def edit(tree):
                    for node in tree.findall('./nets/net/node'):
                        if node.get('ref') == ref:
                            node.set('pin', '2' if node.get('pin') == '1' else '1')
                self.assertTrue(any(ref in e and 'polarity' in e for e in self.mutate('wheel',edit)))

    def test_bulk_substituted_with_unreviewed_capacitor(self):
        def edit(tree):
            tree.find('./components/comp[@ref="C90"]/value').text='10uF/25V'
        self.assertTrue(any('insufficient' in e for e in self.mutate('wheel',edit)))

    def test_local_clamp_missing(self):
        def edit(tree):
            parent=tree.find('./components')
            parent.remove(parent.find('comp[@ref="D6"]'))
        self.assertTrue(any('D6: missing' in e for e in self.mutate('wheel',edit)))

    def test_local_bleed_disconnected(self):
        def edit(tree):
            for net in tree.findall('./nets/net'):
                for node in list(net):
                    if node.get('ref') == 'R146' and node.get('pin') == '2':net.remove(node)
        self.assertTrue(any('R146: local rail' in e for e in self.mutate('wheel',edit)))


if __name__=="__main__":unittest.main()
