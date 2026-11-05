# SPDX-License-Identifier: GPL-3.0-or-later
"""Reusable panel primitives; does not rebuild historical revisions."""
import uuid
import pcbnew as p
from shapely.geometry import Polygon, Point, box
UUID_REPLACEMENTS={}

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def root_sections(text):
    """Read complete direct children while respecting quoted strings/escapes."""
    depth, quoted, escaped, start = 0, False, False, None
    for i, c in enumerate(text):
        if quoted:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
        elif c == '"':
            quoted = True
        elif c == "(":
            if depth == 1:
                start = i
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 1 and start is not None:
                yield text[start:i + 1]
                start = None
    require(depth == 0 and not quoted, "Malformed source PCB")

def xy(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))

def uid(item): return item.m_Uuid.AsString()

def stable_uuid(item, name): UUID_REPLACEMENTS[uid(item)]=str(uuid.uuid5(uuid.NAMESPACE_URL,'MagMouse/bench/'+name))

def duplicate(item):
    raw=item.Duplicate(False) if isinstance(item,(p.ZONE,p.FOOTPRINT)) else item.Duplicate()
    return getattr(p,'Cast_to_'+item.GetClass())(raw)

def outline(board):
    poly=p.SHAPE_POLY_SET()
    assert board.GetBoardPolygonOutlines(poly,False), 'Open board outline'
    assert poly.OutlineCount()==1
    def coords(chain): return [(p.ToMM(chain.CPoint(i).x),p.ToMM(chain.CPoint(i).y)) for i in range(chain.PointCount())]
    return Polygon(coords(poly.Outline(0)),[coords(poly.Hole(0,i)) for i in range(poly.HoleCount(0))])

def add_segment(b,a,c,layer=p.Edge_Cuts):
    if xy(*a)==xy(*c):return
    s=p.PCB_SHAPE(b);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(xy(*a));s.SetEnd(xy(*c));s.SetWidth(p.FromMM(.05));s.SetLayer(layer)
    stable_uuid(s,f'segment-{layer}-{a}-{c}');b.Add(s)

def add_hole(b,x,y,d,ref):
    f=p.FOOTPRINT(b);f.SetReference(ref);f.SetValue('NPTH');f.SetExcludedFromBOM(True);f.SetExcludedFromPosFiles(True)
    f.SetPosition(xy(x,y));stable_uuid(f,ref);b.Add(f)
    pad=p.PAD(f);pad.SetAttribute(p.PAD_ATTRIB_NPTH);pad.SetShape(p.PAD_SHAPE_CIRCLE)
    pad.SetSize(xy(d,d));pad.SetDrillSize(xy(d,d));pad.SetLayerSet(p.LSET.AllCuMask());pad.SetPosition(xy(x,y));stable_uuid(pad,ref+'pad');f.Add(pad)
    for i,field in enumerate(f.GetFields()):
        field.SetVisible(False);stable_uuid(field,ref+'/field/'+str(i))

def tab_candidates(board, poly):
    """Only straight edges; drill row is 0.5 mm OUTSIDE finished unit edge."""
    # Candidate width 5 mm, 5 holes at 0.9 pitch: 0.3 mm web.
    coords=list(poly.simplify(.000001).exterior.coords); result=[]
    for a,c in zip(coords,coords[1:]):
        dx,dy=c[0]-a[0],c[1]-a[1];length=(dx*dx+dy*dy)**.5
        if length<6:continue
        tx,ty=dx/length,dy/length; nx,ny=-ty,tx
        mid=((a[0]+c[0])/2,(a[1]+c[1])/2)
        if poly.contains(Point(mid[0]+nx*.1,mid[1]+ny*.1)):nx,ny=-nx,-ny
        for distance in range(3,int(length)-2,3):
            x,y=a[0]+tx*distance,a[1]+ty*distance
            # Screen component courtyards (pads when absent) for support access.
            # Separate panel DRC and translated-copper checks cover copper.
            probe=Point(x,y).buffer(3)
            blocked=False
            for f in board.GetFootprints():
                shapes=[s for s in f.GraphicalItems() if s.GetLayer() in (p.F_CrtYd,p.B_CrtYd)] or list(f.Pads())
                for s in shapes:
                    r=s.GetBoundingBox()
                    if probe.intersects(box(p.ToMM(r.GetLeft()),p.ToMM(r.GetTop()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom()))):blocked=True;break
                if blocked:break
            if blocked:continue
            corners=[(x+tx*u+nx*v,y+ty*u+ny*v) for u,v in [(-2.5,-.1),(2.5,-.1),(2.5,2.1),(-2.5,2.1)]]
            holes=[(x+tx*u+nx*.5,y+ty*u+ny*.5) for u in (-1.8,-.9,0,.9,1.8)]
            result.append(dict(center=[x,y],normal=[nx,ny],polygon=corners,holes=holes))
    return result

def verify_tab_bridge(tab, unit, frame):
    """Require the entire 5 mm tab width to enter both substrates by 0.08 mm."""
    x,y=tab['center'];nx,ny=tab['normal'];tx,ty=-ny,nx
    def strip(a,b):
        return Polygon([(x+tx*u+nx*v,y+ty*u+ny*v) for u,v in [(-2.5,a),(2.5,a),(2.5,b),(-2.5,b)]])
    tab_poly=Polygon(tab['polygon'])
    assert tab_poly.buffer(1e-7).covers(strip(-.09,2.09)), 'Tab is not a full-width bridge'
    assert unit.buffer(1e-7).covers(strip(-.09,-.01)), 'Tab does not enter intended board across full width'
    assert frame.buffer(1e-7).covers(strip(2.01,2.09)), 'Tab does not enter frame across full width'
    return dict(board_overlap_depth_mm=.08,frame_overlap_depth_mm=.08,bridge_width_mm=5)
