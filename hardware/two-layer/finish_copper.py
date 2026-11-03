"""Restore minimum trace widths and stitch overlapping outer ground islands.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import argparse
import sys
import pcbnew as p
from prepare import ROOT,DEST
sys.path.insert(0,str(ROOT/'build/two-layer/python'))
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union


def polygons(shape):
    def ring(chain):
        return [(p.ToMM(chain.CPoint(i).x),p.ToMM(chain.CPoint(i).y)) for i in range(chain.PointCount())]
    return [Polygon(ring(shape.COutline(i)),[ring(shape.CHole(i,j)) for j in range(shape.HoleCount(i))])
            for i in range(shape.OutlineCount())]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('board')
    name=ap.parse_args().board
    path=DEST/name.lower()/(name+'.kicad_pcb')
    b=p.LoadBoard(str(path))
    widened=0
    for t in b.GetTracks():
        if not isinstance(t,p.PCB_VIA) and t.GetWidth()<p.FromMM(.127):
            t.SetWidth(p.FromMM(.127))
            widened+=1
    b.BuildConnectivity()
    # Include unanchored opposite-side copper while choosing stitch sites. A via
    # can then join it to a grounded island on the other face. Restore the normal
    # island-removal policy before saving the final fill.
    island_modes=[]
    if name=='Main':
        for zone in b.Zones():
            if zone.GetNetname()=='GND' and not zone.GetIsRuleArea():
                island_modes.append((zone,zone.GetIslandRemovalMode()))
                zone.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_NEVER)
    p.ZONE_FILLER(b).Fill(b.Zones())
    ground={layer:unary_union([poly for z in b.Zones() if z.GetNetname()=='GND' and not z.GetIsRuleArea()
                  and z.GetLayerSet().Contains(layer) for poly in polygons(z.GetFilledPolysList(layer))])
            for layer in (p.F_Cu,p.B_Cu)}
    all_vias=[Point(*p.ToMM(t.GetPosition())) for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
    # Keep new stitching holes out of all component lands and existing drills.
    forbidden=[]
    for f in b.GetFootprints():
        for pad in f.Pads():
            poly=p.SHAPE_POLY_SET()
            for layer in (p.F_Cu,p.B_Cu):
                if pad.IsOnLayer(layer):pad.TransformShapeToPolygon(poly,layer,p.FromMM(.25),p.FromMM(.005),p.ERROR_OUTSIDE)
            forbidden.extend(polygons(poly))
    avoid=unary_union(forbidden+[v.buffer(.5) for v in all_vias])
    overlap=ground[p.F_Cu].intersection(ground[p.B_Cu]).buffer(-.24).difference(avoid)
    areas=list(overlap.geoms) if hasattr(overlap,'geoms') else [overlap]
    added=0
    for area in areas:
        if area.is_empty or area.area<.02:continue
        pt=area.representative_point()
        if any(pt.distance(v)<.65 for v in all_vias):continue
        via=p.PCB_VIA(b)
        via.SetPosition(p.VECTOR2I(p.FromMM(pt.x),p.FromMM(pt.y)))
        via.SetWidth(p.FromMM(.45));via.SetDrill(p.FromMM(.2))
        via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu)
        via.SetNetCode(b.FindNet('GND').GetNetCode())
        b.Add(via);all_vias.append(pt);added+=1
    b.BuildConnectivity()
    for zone,mode in island_modes:zone.SetIslandRemovalMode(mode)
    p.ZONE_FILLER(b).Fill(b.Zones())
    p.SaveBoard(str(path),b)
    print(name,'minimum-width corrections',widened,'ground stitches',added)


if __name__=='__main__':main()
