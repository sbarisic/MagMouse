"""Measure the saved two-layer copper using KiCad direct electrical contacts."""
import json
import math
import sys
from pathlib import Path
import pcbnew as p
from export_quote import BOARDS, HERE, ROOT, polygons, sha
from shapely.ops import unary_union
sys.path.insert(0,str(ROOT/'hardware/common'))
from copper_graph import CopperGraph, RHO, uid

# Currents are explicit calculation cases. Input/supply rows exercise the 2 A
# total USB ceiling; a phase-current limit is a separate operating condition.
loads={
    'Lower': [(f'J1.{pin}','J103.2',2.0) for pin in ('A4','A9','B4','B9')]
             + [('J103.3','U2.2',1.0),('J103.3','U2.3',1.0),('U2.7','L1.1',1.0),('L1.2','J103.4',1.0)],
    'Upper': [('J104.2','U12.5',2.0),('U12.6','J104.3',2.0),('U12.6','U13.5',2.0),('U13.6','J10.1',2.0)],
    'Wheel': [('J11.1',f'U21.{pin}',2.0) for pin in (9,10,11)]
             + [(f'U21.{pin}',f'J5.{phase}',.5) for phase,pins in enumerate(((13,14),(16,17),(19,20)),1) for pin in pins]
             + [('J11.1',f'R{r}.1',6.5/11.75) for r in range(121,125)]
             + [('Q5.3',f'R{r}.2',6.5/11.75) for r in range(121,125)]
}
def route_report(graph,source,dest,current):
    first,last=(graph.pads[tuple(label.split('.'))] for label in (source,dest))
    assert first.GetNetname()==last.GetNetname()
    resistance,keys=graph.path(uid(first),uid(last))
    elements=[graph.items[k] for k in keys]
    segments=[t for t in elements if isinstance(t,p.PCB_TRACK) and not isinstance(t,p.PCB_VIA)]
    barrels=[t for t in elements if isinstance(t,p.PCB_VIA)]
    def width(t):return p.ToMM(t.GetWidth())
    def length(t):return p.ToMM(t.GetLength())
    narrow=min(width(t) for t in segments)
    # IPC-2221 external-conductor correlation at an assumed 10 C rise.
    # The long uniform conductor formula is a screen for short necks, too.
    min_width=(current/(.048*10**.44))**(1/.725)*.0254**2/.035
    constrained=[t for t in segments if width(t)<min_width]
    return dict(source=source,destination=dest,net=first.GetNetname(),case_A=round(current,4),
        path_mohm=round(resistance*1000,3),drop_mV=round(resistance*current*1000,3),
        path_loss_mW=round(resistance*current**2*1000,3),min_width_mm=narrow,
        uniform_10C_screen_width_mm=round(min_width,4),length_below_screen_mm=round(sum(map(length,constrained)),3),
        counted_vias=len(barrels),neck_sections=[{'start_mm':list(p.ToMM(t.GetStart())),'end_mm':list(p.ToMM(t.GetEnd())),
            'layer':t.GetLayerName(),'width_mm':width(t),'length_mm':round(length(t),4)} for t in constrained],
        via_sections=[{'xy_mm':list(p.ToMM(t.GetPosition())),'drill_mm':p.ToMM(t.GetDrillValue()),
            'land_mm':p.ToMM(t.GetWidth(p.F_Cu)),'single_barrel_mohm':round(graph.cost[uid(t)]*1000,3),
            'single_barrel_mW_at_case':round(graph.cost[uid(t)]*current**2*1000,3)} for t in barrels])
def inspect(name,path):
    b=p.LoadBoard(str(path));b.BuildConnectivity();g=CopperGraph(b)
    thickness=p.ToMM(b.GetDesignSettings().GetBoardThickness())
    for key,item in g.items.items():
        if isinstance(item,p.PCB_VIA):
            g.cost[key]=RHO*thickness/1000/(math.pi*p.ToMM(item.GetDrillValue())*.020)
    outline=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(outline,False)
    area=unary_union(polygons(outline)).area;layers={}
    for layer in (p.F_Cu,p.B_Cu):
        fill=unary_union([poly for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname()=='GND' and z.IsOnLayer(layer)
                          for poly in polygons(z.GetFilledPolysList(layer))])
        layers[b.GetLayerName(layer)]={'filled_mm2':round(fill.area,3),'percent':round(100*fill.area/area,2)}
    vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND']
    return dict(sha256=sha(path),outline_area_mm2=round(area,3),gnd_fill=layers,gnd_vias=len(vias),
        gnd_via_positions_mm=[list(p.ToMM(t.GetPosition())) for t in vias],
        power_paths=[route_report(g,*args) for args in loads.get(name,[])])
if __name__=='__main__':
    results={n:inspect(n,path) for n,path in BOARDS.items()}
    dest=HERE/'routing-review/power-and-ground.json'
    dest.write_text(json.dumps(results,indent=2)+'\n')
    for name,data in results.items():
        print(name,data['gnd_fill'],data['gnd_vias'])
        for q in data['power_paths']:print(q['source'],q['destination'],q['path_mohm'],q['min_width_mm'],q['length_below_screen_mm'],q['counted_vias'])
