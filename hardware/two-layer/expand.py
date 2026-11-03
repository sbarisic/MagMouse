"""Give the bench routing variant rectangular routing/ground margins.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import pcbnew as p
from prepare import DEST

for name, bounds in [('Main', (-15, 0, 95, 125)), ('Wheel', (-10, -5, 70, 70))]:
    path = DEST/name.lower()/(name+'.kicad_pcb')
    b = p.LoadBoard(str(path))
    for drawing in list(b.GetDrawings()):
        if drawing.GetLayer() == p.Edge_Cuts:
            b.Remove(drawing)
            drawing.thisown = False
    x0,y0,x1,y1 = bounds
    points = [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    for a,c in zip(points,points[1:]+points[:1]):
        line=p.PCB_SHAPE(b)
        line.SetShape(p.SHAPE_T_SEGMENT)
        line.SetLayer(p.Edge_Cuts)
        line.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])))
        line.SetEnd(p.VECTOR2I(p.FromMM(c[0]),p.FromMM(c[1])))
        line.SetWidth(p.FromMM(.05))
        b.Add(line)
    for layer in (p.F_Cu,p.B_Cu):
        existing=next((z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer()==layer
            and (name=='Wheel' or z.GetZoneName()=='MAIN_RETURN_B.Cu')),None)
        z=existing or p.ZONE(b)
        if not existing:
            z.SetLayer(layer)
            z.SetNetCode(b.FindNet('GND').GetNetCode())
            z.SetLocalClearance(p.FromMM(.2))
            z.SetPadConnection(p.ZONE_CONNECTION_FULL)
            z.SetMinThickness(p.FromMM(.15))
            b.Add(z)
        z.SetZoneName('TWO_LAYER_GND_'+b.GetLayerName(layer))
        z.Outline().RemoveAllContours()
        z.Outline().NewOutline()
        for x,y in points:z.Outline().Append(p.FromMM(x),p.FromMM(y))
        z.UnFill()
    b.BuildConnectivity()
    p.ZONE_FILLER(b).Fill(b.Zones())
    p.SaveBoard(str(path),b)
    print(name,'outline',x1-x0,'x',y1-y0,'mm')
