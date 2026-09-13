"""Source contact inventory and local filled-zone entry checks.

Uses saved copper, never refills or saves the board. Native DRC remains the
authority for net connectivity, clearances and required unconnected pads.
"""
from collections import Counter
from repair_copper_joins import *

LAYERS=(0,4,6,2)

def zone_entry(land, zone, width, gap=0):
    """A width-qualified path must leave the land into this zone locally.

    Only this land and this zone participate: another net branch cannot rescue
    a poor zone entry. Thermal connections use their configured spoke width.
    """
    radius=(width-TOL)/2
    patches=land.intersection(zone)
    if patches.is_empty:return False
    patches=list(patches.geoms) if hasattr(patches,'geoms') else [patches]
    for patch in patches:
        local=patch.envelope.buffer(gap+2*width)
        local_land=land.intersection(local);local_zone=zone.intersection(local)
        copper=local_land.union(local_zone)
        safe=copper.buffer(-radius,quad_segs=64)
        inner=local_land.buffer(-radius,quad_segs=64)
        outside=local_zone.difference(land.buffer(gap+width/2))
        if not any(g.intersects(inner) and g.intersects(outside)
                   for g in (list(safe.geoms) if hasattr(safe,'geoms') else [safe])):return False
    return True

def inventory(board):
    pads=[q for f in board.GetFootprints() for q in f.Pads()]
    vias=[t for t in board.GetTracks() if isinstance(t,p.PCB_VIA)]
    tracks=[t for t in board.GetTracks() if type(t)==p.PCB_TRACK and t.GetLength()>0]
    rows=[];findings=[]
    for layer in LAYERS:
        zones=[z for z in board.Zones() if z.IsOnLayer(layer) and not z.GetIsRuleArea()]
        zone_polys={uid(z):polyset(z.GetFilledPolysList(layer)) for z in zones}
        items=[q for q in pads+vias+tracks if q.IsOnLayer(layer)]
        polys=[shape(q,layer) for q in items];tree=STRtree(polys)
        for i,q in enumerate(items):
            kind='via' if isinstance(q,p.PCB_VIA) else 'trace' if type(q)==p.PCB_TRACK else 'pad'
            poly=polys[i];net=q.GetNetCode()
            neighbours=[uid(items[int(k)]) for k in tree.query(poly.buffer(TOL),predicate='intersects')
                        if int(k)!=i and net and items[int(k)].GetNetCode()==net]
            contacts=[]
            for z in zones:
                if not net or z.GetNetCode()!=net:continue
                zp=zone_polys[uid(z)]
                if not poly.intersects(zp):continue
                pieces=list(zp.geoms) if hasattr(zp,'geoms') else [zp]
                touching=unary_union([piece for piece in pieces if piece.intersects(poly)])
                if touching.difference(poly.buffer(z.GetMinThickness()/2e6+TOL)).is_empty:
                    # A disconnected fill fragment may form a small apron at a
                    # pad edge. It is not a connection to the surrounding plane.
                    contacts.append(dict(zone_uuid=uid(z),classification='pad-local-fill-island-no-plane-return',pass_width=True))
                    continue
                width=q.GetWidth(layer)/1e6 if kind=='via' else q.GetWidth()/1e6 if kind=='trace' else min(q.GetSize().x,q.GetSize().y)/1e6
                mode=q.GetLocalZoneConnection() if kind=='pad' else p.ZONE_CONNECTION_FULL
                if mode==p.ZONE_CONNECTION_INHERITED:mode=z.GetPadConnection()
                thermal=kind=='pad' and (mode==p.ZONE_CONNECTION_THERMAL or
                    mode==p.ZONE_CONNECTION_THT_THERMAL and q.GetAttribute()==p.PAD_ATTRIB_PTH)
                gap=0
                # A zone is not a track of the pad diameter. Its existing
                # minimum feature rule defines the generic land-to-pour screen;
                # routed power/return acceptance remains in the strict checks.
                if kind!='trace' and not thermal:width=min(width,z.GetMinThickness()/1e6)
                if thermal:
                    spoke=(q.GetLocalThermalSpokeWidthOverride() or 0)/1e6 or z.GetThermalReliefSpokeWidth()/1e6
                    gap=(q.GetLocalThermalGapOverride() or 0)/1e6 or z.GetThermalReliefGap()/1e6
                    width=min(width,spoke)
                thermal_pad=None
                if kind=='trace':
                    for k in tree.query(poly,predicate='intersects'):
                        candidate=items[int(k)]
                        if not isinstance(candidate,p.PAD) or candidate.GetNetCode()!=net:continue
                        pm=candidate.GetLocalZoneConnection()
                        if pm==p.ZONE_CONNECTION_INHERITED:pm=z.GetPadConnection()
                        if pm==p.ZONE_CONNECTION_THERMAL or pm==p.ZONE_CONNECTION_THT_THERMAL and candidate.GetAttribute()==p.PAD_ATTRIB_PTH:
                            cg=(candidate.GetLocalThermalGapOverride() or z.GetThermalReliefGap())/1e6
                            if not line(q).difference(polys[int(k)].buffer(cg)).is_empty:continue
                            thermal_pad=candidate;break
                    if thermal_pad is not None:
                        width=min(width,(thermal_pad.GetLocalThermalSpokeWidthOverride() or z.GetThermalReliefSpokeWidth())/1e6)
                        gap=(thermal_pad.GetLocalThermalGapOverride() or z.GetThermalReliefGap())/1e6
                        thermal=True
                ok=zone_entry(poly,zp,width,gap)
                entry=dict(zone_uuid=uid(z),thermal=thermal,width_mm=width,gap_mm=gap,pass_width=ok)
                if thermal_pad is not None:entry['thermal_pad']=thermal_pad.GetParentFootprint().GetReference()+'.'+thermal_pad.GetNumber()
                contacts.append(entry)
                if not ok:findings.append(dict(kind='zone-entry',item_uuid=uid(q),reference=q.GetParentFootprint().GetReference()+'.'+q.GetNumber() if kind=='pad' else '',net=q.GetNetname(),layer=layer,**entry))
            connected_zone=any(c.get('classification')!='pad-local-fill-island-no-plane-return' for c in contacts)
            state='connected-on-layer' if neighbours or connected_zone else 'unnetted' if not net else 'no-contact-on-this-layer'
            rows.append(dict(uuid=uid(q),kind=kind,layer=layer,net=q.GetNetname(),state=state,
                neighbours=neighbours,zones=contacts,
                reference=q.GetParentFootprint().GetReference()+'.'+q.GetNumber() if kind=='pad' else '',
                position_mm=xy(q.GetPosition()) if kind!='trace' else None,
                drill_mm=q.GetDrillValue()/1e6 if kind=='via' else [q.GetDrillSize().x/1e6,q.GetDrillSize().y/1e6] if kind=='pad' else None))
    connected={r['uuid'] for r in rows if r['state']=='connected-on-layer'}
    for r in rows:
        if r['state']!='no-contact-on-this-layer':continue
        if r['net'].startswith('unconnected-('):r['state']='schematic-NC-pad'
        elif r['uuid'] in connected and r['kind']=='via':r['state']='unused-via-layer'
        elif r['uuid'] in connected and r['kind']=='pad' and any(r['drill_mm']):r['state']='unused-plated-pad-layer'
        else:findings.append(dict(kind='unclassified-isolated-element',uuid=r['uuid'],layer=r['layer'],reference=r['reference']))
    return dict(elements=rows,zone_findings=findings,states=dict(Counter(r['state'] for r in rows)),
        classification_note='No-contact-on-this-layer is not an exemption from native connectivity. Through-hole/via barrels join enabled layers; native zero-unrouted/parity gates must also pass.')

if __name__=='__main__':
    from build_panel import SOURCES,sha,atomic_text
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'build/contact-review.json')
    args=parser.parse_args();result={}
    for name,path in SOURCES.items():
        data=inventory(p.LoadBoard(str(path)));data['source_sha256']=sha(path);result[name]=data
        print(name,data['states'],'zone findings',len(data['zone_findings']),flush=True)
    atomic_text(args.output,json.dumps(result,indent=2)+'\n')
    if any(d['zone_findings'] for d in result.values()):raise SystemExit(1)

