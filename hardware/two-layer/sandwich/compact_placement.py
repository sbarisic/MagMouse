"""Place full-size footprints within the 70 x 100 mm sandwich study.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import math
import sys
from pathlib import Path
import pcbnew as p

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'build/two-layer/python'))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from finish_copper import polygons
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.affinity import translate
from spaced_groups import goals as spaced_goals, BASELINE, COURTYARD_GAP_MM

FIXED = {'J1': (35,4), 'U3': (35,89.25), 'U35': (35.5,52.5), 'J8': (62,50)}
# Antenna end of U3 at its fixed 180-degree placement. Clearance extends
# sideways and outwards; the module itself occupies the feed/body side.
ANTENNA_CLEARANCE_MM = 5.0
ANTENNA_BODY = (FIXED['U3'][0]-7.7, FIXED['U3'][1]+5.25,
                FIXED['U3'][0]+7.7, FIXED['U3'][1]+9.75)
ANTENNA = (ANTENNA_BODY[0]-ANTENNA_CLEARANCE_MM, ANTENNA_BODY[1],
           ANTENNA_BODY[2]+ANTENNA_CLEARANCE_MM, ANTENNA_BODY[3]+ANTENNA_CLEARANCE_MM)


def shapes(footprint):
    footprint.BuildCourtyardCaches()
    courtyard=unary_union(polygons(footprint.GetCourtyard(p.F_CrtYd))+
                          polygons(footprint.GetCourtyard(p.B_CrtYd)))
    pads=p.SHAPE_POLY_SET()
    for pad in footprint.Pads():
        for layer in (p.F_Cu,p.B_Cu):
            if pad.IsOnLayer(layer):
                pad.TransformShapeToPolygon(pads,layer,0,p.FromMM(.002),p.ERROR_OUTSIDE)
    copper=unary_union(polygons(pads))
    occupied=unary_union([courtyard,copper.buffer(.15)])
    # The ESP32 courtyard includes its RF reservation beyond the physical body.
    physical=occupied
    if footprint.GetReference()=='U3':
        for zone in footprint.Zones():
            physical=physical.difference(unary_union(polygons(zone.Outline())))
    return occupied,physical,copper


def place(board,side,sheets,owners,outline_points):
    outline=Polygon(outline_points)
    source={f.GetReference():tuple(p.ToMM(f.GetPosition())) for f in board.GetFootprints()}
    fps={f.GetReference():f for f in board.GetFootprints()}
    goals,anchors=spaced_goals(side,fps,sheets)
    geometry={ref:shapes(f) for ref,f in fps.items()}
    occupied=[]
    if side=='Upper':
        x0,y0,x1,y1=ANTENNA
        occupied.append(Polygon([(x0,y0),(x1,y0),(x1,y1),(x0,y1)]))
    # Preserve connectors, mounting points, the optical/antenna anchors and Hall
    # sensor positions while distributing their surrounding circuitry.
    fixed=[ref for ref in fps if ref not in owners or ref in FIXED
           or ref.startswith('J') or ref in ('U7','U8','U9','U20','U1')]
    fixed.sort(key=lambda ref:0 if ref not in owners else 1)
    remaining=[ref for ref in fps if ref not in fixed]
    remaining.sort(key=lambda ref:(3 if ref.startswith('TP') else 0 if ref.startswith('U') or ref in anchors.values()
                                   else 1 if ref.startswith(('L','D')) else 2,
                                   -geometry[ref][0].area,ref))
    offsets=sorted(((ix*.25,iy*.25) for ix in range(-60,61) for iy in range(-60,61)),
                   key=lambda v:(v[0]*v[0]+v[1]*v[1],abs(v[1]),v[0],v[1]))
    placed={}
    for ref in fixed+remaining:
        f=fps[ref]
        gx,gy=goals.get(ref,source[ref])
        if ref in anchors:
            anchor=anchors[ref]
            if anchor in placed:
                gx+=placed[anchor]['packing_offset_mm'][0]
                gy+=placed[anchor]['packing_offset_mm'][1]
        dx,dy=gx-source[ref][0],gy-source[ref][1]
        a,body,copper=geometry[ref]
        obstacle=unary_union(occupied)
        found=None
        for ox,oy in ([(0,0)] if ref in fixed else offsets):
            tx,ty=dx+ox,dy+oy
            shifted=translate(a,tx,ty)
            body_shifted=translate(body,tx,ty)
            copper_shifted=translate(copper,tx,ty)
            # USB shell deliberately reaches the front edge; its pads stay inside.
            if ref!='J1' and not outline.covers(body_shifted):
                continue
            if not outline.covers(copper_shifted.buffer(.3)):
                continue
            gap=.025 if ref in fixed else .3 if ref.startswith(('C','L')) else COURTYARD_GAP_MM
            if shifted.buffer(gap).intersects(obstacle):
                continue
            if ref.startswith(('C','L')) and ref in anchors and anchors[ref] in placed:
                anchor=anchors[ref]
                old_distance=math.dist(BASELINE[side][ref],BASELINE[side][anchor])
                if math.dist((source[ref][0]+tx,source[ref][1]+ty),placed[anchor]['position_mm'])>old_distance+.75:
                    continue
            found=(tx,ty,shifted)
            break
        assert found is not None,f'No legal placement within search radius: {side} {ref}'
        tx,ty,shifted=found
        f.Move(p.VECTOR2I(p.FromMM(tx),p.FromMM(ty)))
        occupied.append(shifted)
        actual=tuple(p.ToMM(f.GetPosition()))
        goal=goals.get(ref,source[ref])
        placed[ref]={'source_position_mm':source[ref],'nominal_position_mm':goal,
                     'position_mm':actual,'packing_offset_mm':[round(actual[0]-goal[0],6),round(actual[1]-goal[1],6)]}
    return placed
