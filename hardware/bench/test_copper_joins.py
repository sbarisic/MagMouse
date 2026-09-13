"""Reject thin contacts and unsupported tab bridges."""
import unittest
import pcbnew as p
from repair_copper_joins import capsule, covered, local_full_width_path, proposed_join
from build_panel import verify_tab_bridge
from shapely.geometry import box, Polygon

class CopperJoins(unittest.TestCase):
    def test_zone_entry_rejects_tangent_and_accepts_bridge(self):
        from contact_review import zone_entry
        land=box(-.5,-.5,.5,.5)
        zone=box(.4999,.4999,2,2)
        self.assertFalse(zone_entry(land,zone,.2))
        self.assertTrue(zone_entry(land,zone.union(capsule((0,0),(1,1),.2)),.2))

    def test_zone_entry_thermal_width_is_distinct(self):
        from contact_review import zone_entry
        land=box(-.5,-.5,.5,.5)
        zone=box(.7,-2,2,2).union(box(.49,-.125,.71,.125))
        self.assertTrue(zone_entry(land,zone,.25,.2))
        self.assertFalse(zone_entry(land,zone,.5,.2))

    def test_zone_entry_remote_contact_cannot_hide_tangent(self):
        from contact_review import zone_entry
        land=box(0,0,10,1)
        zone=box(-1,-1,.0001,.0001).union(box(9,-1,11,2))
        self.assertFalse(zone_entry(land,zone,.2))

    def test_export_detects_missing_unmodified_pad_and_wrong_net_bridge(self):
        from verify_gerber_joins import exported_match
        expected=box(0,0,1,1).union(box(2,0,3,1))
        self.assertGreater(exported_match(expected,box(0,0,1,1))[0],.9)
        self.assertGreater(exported_match(expected,box(0,0,3,1))[1],.9)
        self.assertEqual(exported_match(expected,expected),(0,0))

    def test_u16_marked_entries_reach_pad_centres(self):
        from repair_copper_joins import ROOT,xy
        b=p.LoadBoard(str(ROOT/'hardware/modular/main/Main.kicad_pcb'))
        f=next(f for f in b.GetFootprints() if f.GetReference()=='U16')
        for number in ['6','10','13']:
            q=next(q for q in f.Pads() if q.GetNumber()==number)
            self.assertTrue(any(type(t)==p.PCB_TRACK and t.GetLayer()==0 and t.GetNetCode()==q.GetNetCode() and
                xy(q.GetPosition()) in [xy(t.GetStart()),xy(t.GetEnd())] for t in b.GetTracks()),number)

    def test_shared_endpoint_is_export_witness_too(self):
        from repair_copper_joins import audit
        b=p.BOARD();net=p.NETINFO_ITEM(b,'signal');b.Add(net)
        self.make_track(b,net,(-1,0),(0,0),.2)
        self.make_track(b,net,(0,0),(1,0),.2)
        contacts=[];self.assertFalse(audit(b,contacts)[0])
        self.assertEqual(len(contacts),1)
        copper=capsule((-1,0),(1,0),.2).difference(box(-.0001,-1,.0001,1))
        self.assertFalse(covered(contacts[0],copper))
        self.assertFalse(local_full_width_path(contacts[0],copper))

    def make_track(self,b,net,a,c,width):
        from repair_copper_joins import add_bridge
        return add_bridge(b,dict(net_code=net.GetNetCode(),a=a,b=c,width_mm=width,layer=0))

    def test_audit_detects_one_nanometre_cap_overlap(self):
        from repair_copper_joins import audit
        b=p.BOARD();net=p.NETINFO_ITEM(b,'signal');b.Add(net)
        self.make_track(b,net,(20.8,32.1),(20.85,31.15),.2)
        self.make_track(b,net,(20.8,32.299999),(20.75,32.35),.2)
        self.assertEqual(len(audit(b)[0]),1)

    def test_audit_detects_one_micron_gap(self):
        from repair_copper_joins import audit
        b=p.BOARD();net=p.NETINFO_ITEM(b,'signal');b.Add(net)
        self.make_track(b,net,(-1,0),(0,0),.2)
        self.make_track(b,net,(.201,0),(1,0),.2)
        self.assertEqual(len(audit(b)[0]),1)

    def test_audit_detects_pad_entry(self):
        from repair_copper_joins import audit
        b=p.BOARD();net=p.NETINFO_ITEM(b,'signal');b.Add(net)
        self.make_track(b,net,(-1,0),(0,0),.4)
        f=p.FOOTPRINT(b);f.SetReference('U1');b.Add(f)
        q=p.PAD(f);q.SetNumber('1');q.SetAttribute(p.PAD_ATTRIB_SMD);q.SetShape(p.PAD_SHAPE_RECT)
        q.SetPosition(p.VECTOR2I(299999,0));q.SetSize(p.VECTOR2I(200000,400000));q.SetNet(net)
        layers=p.LSET();layers.AddLayer(p.F_Cu);q.SetLayerSet(layers);f.Add(q)
        findings,_=audit(b)
        self.assertEqual(len(findings),1);self.assertEqual(findings[0]['kind'],'pad')

    def test_audit_detects_land_only_neck(self):
        from repair_copper_joins import audit
        b=p.BOARD();net=p.NETINFO_ITEM(b,'signal');b.Add(net)
        for x in [0,449999]:
            v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(x,0));v.SetWidth(450000)
            v.SetDrill(200000);v.SetNet(net);b.Add(v)
        findings,_=audit(b)
        self.assertTrue(findings)
        self.assertTrue(all(j['kind']=='land-pair' for j in findings))

    def test_wheel_miso_loop_removed(self):
        from repair_copper_joins import ROOT,line,unary_union
        from shapely.ops import polygonize
        b=p.LoadBoard(str(ROOT/'hardware/modular/wheel/Wheel.kicad_pcb'))
        copper=unary_union([line(t) for t in b.GetTracks() if type(t)==p.PCB_TRACK and t.GetLayer()==0 and t.GetNetname()=='ADC2_MISO_LOCAL'])
        self.assertFalse(any(poly.area>.001 for poly in polygonize(copper)))

    def test_barely_touching(self):
        j=dict(a=(0,0),b=(.198,0),width_mm=.2)
        copper=capsule((-1,0),(0,0),.2).union(capsule((.198,0),(1,0),.2))
        self.assertFalse(covered(j,copper))
        self.assertFalse(local_full_width_path(j,copper))

    def test_broken(self):
        j=dict(a=(0,0),b=(.25,0),width_mm=.2)
        copper=capsule((-1,0),(0,0),.2).union(capsule((.25,0),(1,0),.2))
        self.assertFalse(covered(j,copper))
        self.assertFalse(local_full_width_path(j,copper))

    def test_shared_centerline(self):
        j=dict(a=(0,0),b=(.198,0),width_mm=.2)
        self.assertTrue(covered(j,capsule((-1,0),(1,0),.2)))

    def test_local_full_width_bend(self):
        j=dict(a=(0,0),b=(.198,0),width_mm=.2)
        copper=capsule((0,0),(0,.25),.2).union(capsule((0,.25),(.198,.25),.2)).union(capsule((.198,.25),(.198,0),.2))
        self.assertFalse(covered(j,copper))
        self.assertTrue(local_full_width_path(j,copper))

    def test_distant_bypass_does_not_excuse_thin_join(self):
        j=dict(a=(0,0),b=(.3,0),width_mm=.2)
        copper=capsule((0,0),(0,10),.2).union(capsule((0,10),(.3,10),.2)).union(capsule((.3,10),(.3,0),.2))
        self.assertFalse(local_full_width_path(j,copper))

    def test_wrong_net(self):
        b=p.BOARD();a=p.PCB_TRACK(b);c=p.PCB_TRACK(b)
        n1=p.NETINFO_ITEM(b,"A");n2=p.NETINFO_ITEM(b,"B");b.Add(n1);b.Add(n2)
        a.SetNet(n1);c.SetNet(n2)
        with self.assertRaises(AssertionError):proposed_join(a,c)

    def test_thin_via_entry_rejected(self):
        from repair_copper_joins import Point
        j=dict(a=(64.5,45.25),b=(64.9,45.05),width_mm=.3)
        copper=capsule((63.95,45.25),j['a'],.3).union(Point(j['b']).buffer(.3,quad_segs=64))
        self.assertFalse(covered(j,copper))
        self.assertTrue(covered(j,copper.union(capsule(j['a'],j['b'],.3))))

    def test_u6_coil_via_entry(self):
        from repair_copper_joins import ROOT,shape,unary_union,uid
        b=p.LoadBoard(str(ROOT/'hardware/modular/main/Main.kicad_pcb'))
        v=next(t for t in b.GetTracks() if uid(t)=='3695c18a-3263-4bd1-b8fa-bb6d2eeea201')
        copper=unary_union([shape(t,0) for t in b.GetTracks() if t.IsOnLayer(0) and t.GetNetCode()==v.GetNetCode()])
        self.assertTrue(covered(dict(a=(64.5,45.25),b=(64.9,45.05),width_mm=.3),copper))

class TabBridges(unittest.TestCase):
    def setUp(self):
        self.tab=dict(center=(0,0),normal=(0,1),polygon=[(-2.5,-.1),(2.5,-.1),(2.5,2.1),(-2.5,2.1)])
        self.unit=box(-5,-5,5,0)

    def test_full_width(self):
        verify_tab_bridge(self.tab,self.unit,box(-5,2,5,5))

    def test_dangling(self):
        with self.assertRaises(AssertionError):verify_tab_bridge(self.tab,self.unit,box(-5,3,5,5))

    def test_corner_only(self):
        with self.assertRaises(AssertionError):verify_tab_bridge(self.tab,self.unit,box(2.5,2.1,5,5))

    def test_narrow_bridge(self):
        self.tab['polygon']=[(-.1,-.1),(.1,-.1),(.1,2.1),(-.1,2.1)]
        with self.assertRaises(AssertionError):verify_tab_bridge(self.tab,self.unit,box(-5,2,5,5))

if __name__=='__main__':unittest.main()
