"""Nominal 2 mm cutter envelopes; geometry verification, not machine G-code."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'build/bench-python'))
from shapely.geometry import Polygon, LineString, Point, box, mapping, shape
from shapely.ops import unary_union
import math

DIAMETER=2.0
RADIUS=DIAMETER/2
TOLERANCE=.002
# Keep exactly-tool-width corridors as thin centre corridors, rather than
# losing them to polygon erosion. The nominal tool is still 2 mm. All swept
# contours are compared at the stated 2 um tolerance and clipped to the
# original permitted removal area, so unit outlines are never overcut.
CENTRE_SLACK=.0005
ARC_SEGMENTS=128
CONTOUR_SIMPLIFICATION=.00025

def parts(g):
    return list(g.geoms) if hasattr(g,'geoms') else [g]

def sweep(paths):
    return unary_union([p.buffer(RADIUS,quad_segs=ARC_SEGMENTS) for p in paths])

def verify_sweep(opening,paths):
    assert paths,'No cutter-centre path'
    actual=sweep(paths)
    assert opening.difference(actual.buffer(TOLERANCE)).area<1e-7,'Unreachable pocket or square internal corner'
    assert actual.difference(opening.buffer(TOLERANCE)).area<1e-7,'Router overcut'
    assert opening.geom_type=='Polygon' and opening.is_valid,'Disconnected or invalid routed opening'
    return dict(missing_mm2=opening.difference(actual.buffer(TOLERANCE)).area,
                overcut_mm2=actual.difference(opening.buffer(TOLERANCE)).area)

def route_opening(original):
    core=original.buffer(-RADIUS+CENTRE_SLACK,quad_segs=ARC_SEGMENTS)
    assert not core.is_empty,'Passage smaller than 2 mm tool'
    paths=[]
    for piece in parts(core):
        paths.extend(LineString(r.coords) for r in [piece.exterior,*piece.interiors])
    # Pocket-clearing paths also demonstrate coverage of wide waste areas.
    # Factories may instead remove a waste slug after contour routing.
    x0,y0,x1,y1=core.bounds;y=y0
    while y<=y1:
        for line in parts(core.intersection(LineString([(x0-1,y),(x1+1,y)]))):
            if line.geom_type=='LineString' and line.length>1e-8:paths.append(line)
        y+=RADIUS
    opening=original.intersection(sweep(paths))
    assert opening.geom_type=='Polygon','Narrow passage separates routed opening'
    corners=[];coords=list(original.exterior.coords)[:-1]
    sign=1 if original.exterior.is_ccw else -1
    for i,b in enumerate(coords):
        a=coords[i-1];c=coords[(i+1)%len(coords)]
        u=(b[0]-a[0],b[1]-a[1]);v=(c[0]-b[0],c[1]-b[1])
        turn=sign*math.atan2(u[0]*v[1]-u[1]*v[0],u[0]*v[0]+u[1]*v[1])
        if turn>1e-7:corners.append(Point(b).buffer(RADIUS+TOLERANCE))
    retained=original.difference(opening.buffer(TOLERANCE))
    assert retained.difference(unary_union(corners)).area<1e-7,('Unreachable passage/pocket beyond corner rounding',retained.difference(unary_union(corners)).area,retained.difference(unary_union(corners)).bounds)
    verify_sweep(opening,paths)
    return opening,paths

def verify_outer(poly):
    # Cutter approaches from outside; sharp convex board corners are valid.
    path=LineString(poly.buffer(RADIUS,quad_segs=ARC_SEGMENTS).exterior.coords)
    required=poly.buffer(DIAMETER,quad_segs=ARC_SEGMENTS).difference(poly)
    actual=sweep([path])
    assert required.difference(actual.buffer(TOLERANCE)).area<1e-7,'Outer contour has inaccessible concavity'
    assert actual.intersection(poly.buffer(-TOLERANCE)).area<1e-7,'Outer route overcut'
    return dict(status='PASS',tool_diameter_mm=DIAMETER)

def make_routable(material):
    openings=[];records=[]
    for i,ring in enumerate(material.interiors):
        original=Polygon(ring);opening,paths=route_opening(original)
        openings.append(opening)
        records.append(dict(index=i+1,paths=[list(p.coords) for p in paths],
            retained_shoulder_area_mm2=original.difference(opening).area,
            retained_patches=[dict(bounds_mm=list(g.bounds),area_mm2=g.area)
                for g in parts(original.difference(opening.buffer(TOLERANCE))) if g.area>1e-5],
            **verify_sweep(opening,paths)))
    result=Polygon(material.exterior).difference(unary_union(openings))
    assert result.geom_type=='Polygon' and result.is_valid
    assert material.difference(result).area<1e-7,'Router change removed protected material'
    verify_outer(Polygon(result.exterior))
    return result,dict(tool_diameter_mm=DIAMETER,minimum_internal_radius_mm=RADIUS,
        tolerance_mm=TOLERANCE,centre_corridor_slack_mm=CENTRE_SLACK,
        contour_simplification_mm=CONTOUR_SIMPLIFICATION,
        note='Nominal tool-envelope model, not G-code or factory CAM approval. Exact-width corridors retained; published cutouts clipped to original removal region.',
        openings=records)

def verify_panel(material,review):
    assert review['tool_diameter_mm']==DIAMETER and review['tolerance_mm']==TOLERANCE
    assert len(material.interiors)==len(review['openings'])
    remaining=[Polygon(r) for r in material.interiors]
    for record in review['openings']:
        paths=[LineString(c) for c in record['paths']];envelope=sweep(paths)
        opening=min(remaining,key=lambda g:g.symmetric_difference(envelope).area)
        verify_sweep(opening,paths);remaining.remove(opening)
    verify_outer(Polygon(material.exterior))

def verify_material_tab(material,tab):
    x,y=tab['center'];nx,ny=tab['normal'];tx,ty=-ny,nx
    bridge=Polygon([(x+tx*u+nx*v,y+ty*u+ny*v) for u,v in [(-2.5,-.09),(2.5,-.09),(2.5,2.09),(-2.5,2.09)]])
    assert material.buffer(1e-7).covers(bridge),'Machined tab loses full-width attachment'
    webs=[]
    for hx,hy in tab['holes']:
        hole=Point(hx,hy).buffer(.3)
        assert material.covers(hole),'Router cuts a perforation'
        web=material.boundary.distance(hole)
        assert web>=.2-1e-6,'Insufficient perforation-to-slot web'
        webs.append(web)
    return dict(bridge_width_mm=5,minimum_perforation_slot_web_mm=min(webs) if webs else None)
