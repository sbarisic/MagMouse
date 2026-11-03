"""Record two-layer reference-copper coverage; this is not electrical simulation.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json
import pcbnew as p
from finish_copper import polygons,unary_union
from prepare import DEST

groups={
    'Main':['HALL_L','HALL_M','HALL_R','BTN_L_ISENSE','BTN_M_ISENSE',
            'BTN_R_ISENSE','USB_IMON_ADC','USB_IMON_BUF','USB_DP','USB_DM',
            'MCU_USB_DP','MCU_USB_DM'],
    'Wheel':['WHEEL_SOA','WHEEL_SOB','WHEEL_SOC','WHEEL_I_A','WHEEL_I_B',
             'WHEEL_I_C','ADC2_DECAP','BRAKE_REF','BRAKE_SENSE'],
    'Encoder':['ENC_SCLK_LOCAL','ENC_MOSI_LOCAL','ENC_MISO_LOCAL','ENC_CS_LOCAL']}
result={}
for name,nets in groups.items():
    b=p.LoadBoard(str(DEST/name.lower()/(name+'.kicad_pcb')))
    grounds={layer:unary_union([poly for z in b.Zones() if z.GetNetname()=='GND'
        and not z.GetIsRuleArea() and z.IsOnLayer(layer)
        for poly in polygons(z.GetFilledPolysList(layer))]) for layer in (p.F_Cu,p.B_Cu)}
    result[name]={}
    for net in nets:
        tracks=[t for t in b.GetTracks() if t.GetNetname()==net and not isinstance(t,p.PCB_VIA)]
        uncovered=0
        area=0
        for layer,opposite in ((p.F_Cu,p.B_Cu),(p.B_Cu,p.F_Cu)):
            shape=p.SHAPE_POLY_SET()
            for t in tracks:
                if t.GetLayer()==layer:t.TransformShapeToPolygon(shape,layer,0,p.FromMM(.001),p.ERROR_OUTSIDE)
            geometry=unary_union(polygons(shape))
            area+=geometry.area
            uncovered+=geometry.difference(grounds[opposite]).area
        result[name][net]={'track_length_mm':round(sum(p.ToMM(t.GetLength()) for t in tracks),4),
            'layers':sorted({b.GetLayerName(t.GetLayer()) for t in tracks}),
            'projected_track_area_mm2':round(area,6),
            'area_without_opposite_layer_gnd_mm2':round(uncovered,6)}
out=DEST/'review';out.mkdir(exist_ok=True)
(out/'reference-copper.json').write_text(json.dumps({
    'interpretation':'Raw geometric screen, including own-pad/via clearances. Nonzero area is not a measured electrical failure; zero area is not impedance or noise certification.',
    'boards':result},indent=2)+'\n')
