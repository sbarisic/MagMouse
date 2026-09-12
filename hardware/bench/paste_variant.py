"""Manufacturer-derived apertures for the bench stencil, without changing copper.

Geometry follows TI package examples. Rev-A selects 0.100 mm; the deliberate
20% nominal-volume reduction versus DSG/RTE/RGF 0.125 mm examples is documented
in STENCIL_REVIEW.md. Actual print/reflow validation remains an assembly task.
"""
import pcbnew as p
import math

def apply(board,name=None):
    for f in board.GetFootprints():
        ref=f.GetReference()
        if name is None:
            if not ref.startswith(('M_','W_','E_')):continue
            prefix,ref=ref.split('_',1)
            unit={'M':'Main','W':'Wheel','E':'Encoder'}[prefix]
        else:unit=name
        kind=('hall' if unit=='Main' and ref in ('U7','U8','U9') else
              'wson' if unit=='Main' and ref in ('U2','U4','U5','U6') else
              'adc' if (unit,ref) in (('Main','U10'),('Wheel','U23')) else None)
        if not kind:continue
        thermal_pin={'hall':'5','wson':'9','adc':'17'}[kind]
        ep=next(q for q in f.Pads() if q.GetNumber()==thermal_pin and q.IsOnLayer(p.F_Cu))
        # Reuse paste-only pads. Removing pads triggers a KiCad 10 SWIG lifetime
        # issue when a later board is loaded in the same Python process.
        old=[q for q in f.Pads() if q.IsOnLayer(p.F_Paste) and not q.IsOnLayer(p.F_Cu)]
        for q in old:
            layers=q.GetLayerSet();layers.RemoveLayer(p.F_Paste);q.SetLayerSet(layers)
        ls=ep.GetLayerSet();ls.RemoveLayer(p.F_Paste);ep.SetLayerSet(ls)
        width,height={'hall':(.76,.57),'wson':(.9,.7),'adc':(1.55,1.55)}[kind]
        offsets=[-.45,.45] if kind=='wson' else [0]
        assert len(old)>=len(offsets),(unit,ref,'missing source paste-only pads')
        for q,offset in zip(old,offsets):
            q.SetAttribute(p.PAD_ATTRIB_SMD);q.SetShape(p.PAD_SHAPE_ROUNDRECT)
            layers=p.LSET();layers.AddLayer(p.F_Paste);q.SetLayerSet(layers)
            q.SetSize(p.VECTOR2I(p.FromMM(width),p.FromMM(height)))
            q.SetRoundRectRadiusRatio(.05/min(width,height))
            angle=math.radians(ep.GetOrientationDegrees())
            delta=p.VECTOR2I(p.FromMM(offset*math.sin(angle)),p.FromMM(offset*math.cos(angle)))
            q.SetPosition(ep.GetPosition()+delta);q.SetOrientation(ep.GetOrientation())
    return []
