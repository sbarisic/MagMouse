"""Render all four current boards at one scale from their saved KiCad geometry."""
from pathlib import Path
import hashlib
import html
import json
import argparse
import sys
import pcbnew as p

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'build/two-layer/python'))
sys.path.insert(0,str(HERE.parent))
from finish_copper import polygons
import resvg_py

SPECS=[('Lower Main',HERE/'lower/Lower.kicad_pcb',8,'#59b4c5','Unrouted'),
       ('Upper Main',HERE/'upper/Upper.kicad_pcb',87,'#dd9d43','Unrouted'),
       ('Wheel',HERE/'wheel/Wheel.kicad_pcb',166,'#82c993','Routed'),
       ('Encoder',HERE.parent/'encoder/Encoder.kicad_pcb',230,'#bc9fe2','Routed')]


def coords(poly):
    return ' '.join(f'{x:.4f},{y:.4f}' for x,y in poly.exterior.coords)


def main(main_only=False):
    page_width=164 if main_only else 260
    title='MagMouse — Main boards with passive plastic buttons' if main_only else 'MagMouse — all four boards'
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{page_width*8}" height="1184" viewBox="0 0 {page_width} 148">',
         f'<rect width="{page_width}" height="148" fill="#101822"/>',
         '<style>text{font-family:Arial,sans-serif;fill:#e5edf4}</style>',
         f'<text x="8" y="8" font-size="{3.4 if main_only else 4}">{title}</text>',
         '<text x="8" y="14" font-size="2.2">2 copper layers • same scale • component-side placement views • traces hidden</text>']
    evidence={}
    for index,(name,path,tx,color,status) in enumerate(SPECS[:2] if main_only else SPECS):
        before=path.read_bytes()
        board=p.LoadBoard(str(path))
        assert board.GetCopperLayerCount()==2
        outline=p.SHAPE_POLY_SET()
        assert board.GetBoardPolygonOutlines(outline,False)
        bounds=outline.BBox()
        x0,y0=p.ToMM(bounds.GetPosition());width,height=p.ToMM(bounds.GetSize())
        board_shapes=polygons(outline)
        svg += [f'<text x="{tx}" y="23" font-size="3.2">{name}</text>',
                f'<text x="{tx}" y="28" font-size="2">{width:g} × {height:g} mm · {status}</text>',
                f'<g transform="translate({tx-x0},{32-y0})">']
        for poly in board_shapes:
            svg.append(f'<polygon points="{coords(poly)}" fill="#1d2d3a" stroke="#dce9ef" stroke-width=".25"/>')
        svg.append(f'<clipPath id="board{index}">')
        svg += [f'<polygon points="{coords(poly)}"/>' for poly in board_shapes]
        svg.append('</clipPath>')
        zones=list(board.Zones())+[z for f in board.GetFootprints() for z in f.Zones()]
        for z in zones:
            if not z.GetIsRuleArea():continue
            antenna='ANTENNA' in z.GetZoneName().upper()
            optical='APERTURE' in z.GetZoneName().upper()
            if not (antenna or optical):continue
            fill,stroke=('#402c3c','#da88b8') if antenna else ('#183e49','#67d5ef')
            for poly in polygons(z.Outline()):
                svg.append(f'<polygon clip-path="url(#board{index})" points="{coords(poly)}" fill="{fill}" stroke="{stroke}" stroke-width=".15" stroke-dasharray=".7,.5"/>')
        for f in board.GetFootprints():
            # Body outlines only, omitting reference/value fields and courtyards.
            for g in f.GraphicalItems():
                if not isinstance(g,p.PCB_SHAPE) or g.GetLayer()!=p.F_Fab:continue
                if g.GetShape()==p.SHAPE_T_SEGMENT:
                    a,b=p.ToMM(g.GetStart()),p.ToMM(g.GetEnd())
                    svg.append(f'<path d="M {a[0]},{a[1]} L {b[0]},{b[1]}" fill="none" stroke="{color}" stroke-opacity=".5" stroke-width=".09"/>')
                elif g.GetShape()==p.SHAPE_T_RECT:
                    a,b=p.ToMM(g.GetStart()),p.ToMM(g.GetEnd())
                    svg.append(f'<rect x="{min(a[0],b[0])}" y="{min(a[1],b[1])}" width="{abs(a[0]-b[0])}" height="{abs(a[1]-b[1])}" fill="none" stroke="{color}" stroke-opacity=".5" stroke-width=".09"/>')
            for pad in f.Pads():
                if not pad.IsOnLayer(p.F_Cu):continue
                shape=p.SHAPE_POLY_SET()
                pad.TransformShapeToPolygon(shape,p.F_Cu,0,p.FromMM(.01),p.ERROR_INSIDE)
                for poly in polygons(shape):
                    svg.append(f'<polygon points="{coords(poly)}" fill="{color}"/>')
                dx,dy=p.ToMM(pad.GetDrillSize())
                if dx and dx==dy:
                    x,y=p.ToMM(pad.GetPosition())
                    svg.append(f'<circle cx="{x}" cy="{y}" r="{dx/2}" fill="#101822"/>')
            ref=f.GetReference();x,y=p.ToMM(f.GetPosition())
            if ref in ('J101','J102','J103','J104'):
                positions=[p.ToMM(pad.GetPosition()) for pad in f.Pads()]
                x=sum(pt[0] for pt in positions)/len(positions)
                y=min(pt[1] for pt in positions)-1
            if ref.startswith('H'):
                svg.append(f'<circle cx="{x}" cy="{y}" r="2.5" fill="none" stroke="#e9c66e" stroke-width=".2"/>')
            elif ref.startswith(('U','J')):
                svg.append(f'<text x="{x+.8}" y="{y-1}" font-size="1.25">{html.escape(ref)}</text>')
        svg.append('</g>')
        assert path.read_bytes()==before
        evidence[name]={'path':str(path),'width_mm':width,'height_mm':height,
                        'sha256':hashlib.sha256(before).hexdigest()}
    footer='70 × 100 mm each • plastic click mechanisms with Hall sensing' if main_only else 'Main stack: 19 wires / 3 grounds     •     Wheel: 19 wires / 3 grounds'
    svg += [f'<text x="8" y="140" font-size="2">{footer}</text>',
            f'<path d="M {page_width-30},138 v 2 M {page_width-30},139 h 20 M {page_width-10},138 v 2" fill="none" stroke="#e5edf4" stroke-width=".3"/>',
            f'<text x="{page_width-20}" y="144" text-anchor="middle" font-size="2">20 mm</text>','</svg>']
    out=HERE/('main-boards.svg' if main_only else 'all-boards.svg');out.write_text('\n'.join(svg),encoding='utf-8')
    out.with_suffix('.png').write_bytes(resvg_py.svg_to_bytes(svg_path=str(out)))
    out.with_suffix('.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({name:[v['width_mm'],v['height_mm']] for name,v in evidence.items()}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--main-only',action='store_true')
    main(parser.parse_args().main_only)
