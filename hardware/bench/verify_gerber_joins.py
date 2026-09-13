"""Independent exported-Gerber copper width witnesses, using gerbonara.

Install gerbonara into build/gerber-python. Run with KiCad Python, after export.
Dark/clear primitives are applied in file order; arc error is at most 0.0002 mm.
"""
import json
import sys
from pathlib import Path
from repair_copper_joins import ROOT, covered, local_full_width_path, Point, LineString, Polygon, unary_union, audit, shape, polyset, p
sys.path.insert(0,str(ROOT/'build/gerber-python'))
from shapely import prepare
from gerbonara import GerberFile
from gerbonara.utils import MM
from gerbonara.graphic_primitives import Circle, Line
from build_panel import OFFSETS, SOURCES, sha
from shapely.affinity import affine_transform

def exported_match(expected, actual, tolerance=.0005):
    """Compare all copper, including unmodified pads, vias and zone contacts."""
    missing=expected.difference(actual.buffer(tolerance))
    extra=actual.difference(expected.buffer(tolerance))
    return missing.area,extra.area

def copper(path):
    result=Polygon();batch=[];polarity=True
    for obj in GerberFile.open(path).objects:
        for prim in obj.to_primitives(unit=MM):
            if prim.polarity_dark!=polarity:
                group=unary_union(batch)
                result=result.union(group) if polarity else result.difference(group)
                batch=[];polarity=prim.polarity_dark
            if isinstance(prim,Circle):g=Point(prim.x,prim.y).buffer(prim.r,quad_segs=128)
            elif isinstance(prim,Line):g=LineString([(prim.x1,prim.y1),(prim.x2,prim.y2)]).buffer(prim.width/2,quad_segs=128)
            else:
                outline=prim.to_arc_poly().approximate_arcs(max_error=.0002).outline
                g=Polygon(outline).buffer(0) if len(outline)>=3 else Polygon()
            batch.append(g)
    group=unary_union(batch)
    return result.union(group) if polarity else result.difference(group)

def main():
    package=ROOT/'hardware/bench/package';manifest=json.loads((ROOT/'hardware/bench/copper-join-repairs.json').read_text())
    for name,path in SOURCES.items():assert sha(path)==manifest['source_sha256'][name], 'Stale repair source'
    results=[];boards={};contacts={}
    for name,path in SOURCES.items():
        boards[name]=p.LoadBoard(str(path));contacts[name]=[]
        findings,_=audit(boards[name],contacts[name])
        assert not findings,(name,'Source contact audit failed',findings)
    for layer,filename in [(0,'F_Cu'),(4,'In1_Cu'),(6,'In2_Cu'),(2,'B_Cu')]:
        path=package/'gerbers'/('Panel-'+filename+{0:'.gtl',4:'.g1',6:'.g2',2:'.gbl'}[layer]);g=copper(path);prepare(g);count=0
        for name,data in manifest['boards'].items():
            ox,oy=OFFSETS[name]
            for j in data['findings']:
                if j['layer']!=layer:continue
                witness=dict(j,path=[(x+ox,-y-oy) for x,y in j.get('path',[j['a'],j['b']])])
                assert covered(witness,g),(name,j,'Gerber full-width witness failed')
                count+=1
        full=[]
        for name,b in boards.items():
            ox,oy=OFFSETS[name]
            items=[t for t in b.GetTracks() if t.IsOnLayer(layer)]
            items += [q for f in b.GetFootprints() for q in f.Pads() if q.IsOnLayer(layer) and q.GetAttribute()!=p.PAD_ATTRIB_NPTH]
            geometries=[shape(q,layer) for q in items]
            geometries += [polyset(z.GetFilledPolysList(layer)) for z in b.Zones() if z.IsOnLayer(layer) and not z.GetIsRuleArea()]
            expected=affine_transform(unary_union(geometries),[1,0,0,-1,ox,-oy])
            # Board spacing is 2 mm. A 0.1 mm crop captures excess copper without
            # including another unit; the panel transform verifier covers edges.
            actual=g.intersection(expected.envelope.buffer(.1))
            missing,extra=exported_match(expected,actual)
            assert missing<1e-7 and extra<1e-7,(name,filename,'Whole copper mismatch',missing,extra)
            prepare(actual)
            checked=0
            for j in contacts[name]:
                if j['layer']!=layer:continue
                a,c=[(x+ox,-y-oy) for x,y in [j['a'],j['b']]]
                witness=dict(j,a=a,b=c)
                assert covered(witness,actual) or local_full_width_path(witness,actual),(name,j,'Exported contact failed')
                checked+=1
            full.append(dict(board=name,source_elements=len(items),contacts=checked,missing_mm2=missing,extra_mm2=extra))
        results.append(dict(layer=filename,gerber_sha256=sha(path),verified_joins=count,whole_board=full))
        print(filename,count,'PASS',flush=True)
    (package/'evidence/gerber-joins.json').write_text(json.dumps(dict(status='PASS',source_sha256=manifest['source_sha256'],width_tolerance_mm=.002,layers=results),indent=2)+'\n')

if __name__=='__main__':main()
