"""Verify routing from the exported mechanical Gerber, not only KiCad."""
import json
from collections import Counter
from verify_gerber_joins import GerberFile,MM,ROOT
from router_geometry import verify_panel,verify_material_tab,LineString,unary_union
from shapely.ops import polygonize
from build_panel import sha,atomic_text

def main():
    folder=ROOT/'hardware/bench';package=folder/'package'
    path=package/'gerbers/Panel-Edge_Cuts.gm1'
    lines=[];degrees=Counter()
    for obj in GerberFile.open(path).objects:
        # The generator exports tessellated straight contours. Reject a new
        # primitive rather than silently omitting it from cutter verification.
        assert type(obj).__name__=='Line','Unsupported routing primitive'
        obj=obj.converted(MM)
        a=(obj.x1,-obj.y1);b=(obj.x2,-obj.y2)
        assert a!=b,'Zero-length exported routing edge'
        lines.append(LineString([a,b]));degrees[a]+=1;degrees[b]+=1
    assert all(n==2 for n in degrees.values()),'Open or branching exported routing contour'
    polygons=list(polygonize(unary_union(lines)))
    assert polygons,'Mechanical Gerber has no closed contour'
    material=max(polygons,key=lambda x:x.area)
    manifest=json.loads((folder/'panel-manifest.json').read_text())
    verify_panel(material,manifest['router'])
    tabs=[verify_material_tab(material,t) for t in manifest['tabs']]
    atomic_text(package/'evidence/router-gerber.json',json.dumps(dict(status='PASS',
        gerber_sha256=sha(path),panel_sha256=manifest['panel_sha256'],
        openings=len(material.interiors),tool_diameter_mm=2,tolerance_mm=.002,
        minimum_perforation_slot_web_mm=min(t['minimum_perforation_slot_web_mm'] for t in tabs)),indent=2)+'\n')
    print('Exported router geometry PASS',len(material.interiors),'openings')

if __name__=='__main__':main()
