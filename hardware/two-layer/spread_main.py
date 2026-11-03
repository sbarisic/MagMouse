"""Create a spacious Main placement, retaining local component-group geometry.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json
import math
import pcbnew as p
from prepare import ROOT,DEST,SOURCES,signature

path=DEST/'main/Main.kicad_pcb'
b=p.LoadBoard(str(SOURCES['Main']/'Main.kicad_pcb'))
before=signature(b)
fps=list(b.GetFootprints())
anchors={f.GetReference():p.ToMM(f.GetPosition()) for f in fps
         if f.GetReference().startswith(('U','J','L','Q'))}
def owner(xy):
    return min(anchors,key=lambda k:math.dist(xy,anchors[k]))
offsets={ref:(xy[0],xy[1]) for ref,xy in anchors.items()}
# Put the MCU near the USB input rather than doubling its original USB distance.
offsets['U3']=(75,-119)
offsets['U1']=(40,-10)
assign={f.GetReference():owner(p.ToMM(f.GetPosition())) for f in fps}
for ref in ('C4','C5','C6','R3','R4','R5','R6','SW1','SW2'):
    assign[ref]='U3'
net_groups={}
for f in fps:
    for pad in f.Pads():net_groups.setdefault(pad.GetNetname(),set()).add(assign[f.GetReference()])
def delta(ref):
    dx,dy=offsets[ref]
    return p.VECTOR2I(p.FromMM(dx),p.FromMM(dy))
removed=0
for t in list(b.GetTracks()):
    if not isinstance(t,p.PCB_VIA) and t.GetLayer() not in (p.F_Cu,p.B_Cu):
        b.Remove(t);t.thisown=False;removed+=1;continue
    a=owner(p.ToMM(t.GetStart()));c=owner(p.ToMM(t.GetEnd()))
    # Keep only local traces; long inter-group paths are freshly routed.
    intergroup=t.GetNetname()!='GND' and len(net_groups.get(t.GetNetname(),set()))>1
    if intergroup or a!=c or a not in net_groups.get(t.GetNetname(),set()) or (not isinstance(t,p.PCB_VIA) and p.ToMM(t.GetLength())>5):
        b.Remove(t);t.thisown=False;removed+=1
    else:
        t.Move(delta(a))
        if a=='U3':
            def rotated(v):
                x,y=p.ToMM(v)
                return p.VECTOR2I(p.FromMM(230-x),p.FromMM(-40-y))
            if isinstance(t,p.PCB_VIA):t.SetPosition(rotated(t.GetPosition()))
            else:t.SetStart(rotated(t.GetStart()));t.SetEnd(rotated(t.GetEnd()))
for f in fps:
    group=assign[f.GetReference()]
    f.Move(delta(group))
    if group=='U3':f.Rotate(p.VECTOR2I(p.FromMM(115),p.FromMM(-20)),p.EDA_ANGLE(180,p.DEGREES_T))
for z in list(b.Zones()):
    if not z.GetIsRuleArea():
        b.Remove(z);z.thisown=False
    else:
        if z.GetZoneName()=='WHEEL MECHANICS PROVISIONAL':
            # The motor/wheel is separately supported on the bench; an old shell
            # reservation must not occupy the newly placed MCU.
            b.Remove(z);z.thisown=False;continue
        layers=z.GetLayerSet();layers.RemoveLayer(p.In1_Cu);layers.RemoveLayer(p.In2_Cu)
        z.SetLayerSetAndRemoveUnusedFills(layers)
        ref=('U35' if 'PMW3360 APERTURE' in z.GetZoneName() else
             'J8' if z.GetZoneName().startswith('J8 SOLDERED') else owner(p.ToMM(z.GetBoundingBox().GetCenter())))
        z.Move(delta(ref))
for d in list(b.GetDrawings()):
    b.Remove(d);d.thisown=False
b.SetCopperLayerCount(2)
layers=b.GetEnabledLayers();layers.RemoveLayer(p.In1_Cu);layers.RemoveLayer(p.In2_Cu);b.SetEnabledLayers(layers)
b.GetDesignSettings().m_HasStackup=False
# USB connector front is at y=4 after moving its group. Provide a shallow notch.
points=[(-10,-45),(74.6,-45),(74.6,3.4),(85.4,3.4),(85.4,-45),(170,-45),(170,250),(-10,250)]
for a,c in zip(points,points[1:]+points[:1]):
    d=p.PCB_SHAPE(b);d.SetShape(p.SHAPE_T_SEGMENT);d.SetLayer(p.Edge_Cuts)
    d.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));d.SetEnd(p.VECTOR2I(p.FromMM(c[0]),p.FromMM(c[1])))
    d.SetWidth(p.FromMM(.05));b.Add(d)
for layer in (p.F_Cu,p.B_Cu):
    z=p.ZONE(b);z.SetLayer(layer);z.SetNetCode(b.FindNet('GND').GetNetCode())
    z.SetZoneName('TWO_LAYER_GND_'+b.GetLayerName(layer));z.SetLocalClearance(p.FromMM(.2))
    z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetMinThickness(p.FromMM(.15));z.Outline().NewOutline()
    for x,y in points:z.Outline().Append(p.FromMM(x),p.FromMM(y))
    b.Add(z)
assert signature(b)==before
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
record={f.GetReference():{'group':assign[f.GetReference()],
    'position_mm':p.ToMM(f.GetPosition()),'translation_mm':offsets[assign[f.GetReference()]],
    'rotation_about_group_center_deg':180 if assign[f.GetReference()]=='U3' else 0} for f in fps}
(DEST/'main-placement.json').write_text(json.dumps(record,indent=2)+'\n')
print('Main: 180 x 295 mm grouped placement;',removed,'inter-group/inner tracks removed')
