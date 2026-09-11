"""Read-only, conservative courtyard-space screen; not a merged PCB design."""
import hashlib
import html
import json
import math
from pathlib import Path
import pcbnew as p

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'hardware/quotes/cost-reduction-2026-09-11'
STEP = .5


def bounds(fp):
    items = [s for s in fp.GraphicalItems() if s.GetLayer() == p.F_CrtYd]
    if not items:
        items = list(fp.Pads())
    boxes = [s.GetBoundingBox() for s in items]
    return [p.ToMM(min(b.GetLeft() for b in boxes)), p.ToMM(min(b.GetTop() for b in boxes)),
            p.ToMM(max(b.GetRight() for b in boxes)), p.ToMM(max(b.GetBottom() for b in boxes))]


def largest_rectangle(mask):
    heights = [0]*len(mask[0]); best = (0,0,0,0,0)
    for y, row in enumerate(mask):
        heights = [h+1 if free else 0 for h,free in zip(heights,row)]
        stack = []
        for x,h in enumerate(heights+[0]):
            start = x
            while stack and stack[-1][1] > h:
                start,old = stack.pop()
                if old*(x-start) > best[0]:
                    best = old*(x-start), start, y-old+1, x-start, old
            if not stack or stack[-1][1] < h:
                stack.append((start,h))
    return dict(area_mm2=best[0]*STEP*STEP,x_mm=best[1]*STEP,y_mm=best[2]*STEP,
                width_mm=best[3]*STEP,height_mm=best[4]*STEP)


def main():
    paths = {n:ROOT/f'hardware/modular/{n.lower()}/{n}.kicad_pcb' for n in ['Main','Wheel']}
    hashes = {n:hashlib.sha256(f.read_bytes()).hexdigest() for n,f in paths.items()}
    boards = {n:p.LoadBoard(str(f)) for n,f in paths.items()}
    fps = {n:{f.GetReference():bounds(f) for f in b.GetFootprints()
              if not f.IsExcludedFromBOM() and not f.IsDNP()} for n,b in boards.items()}
    outline = p.SHAPE_POLY_SET()
    assert boards['Main'].GetBoardPolygonOutlines(outline,False)
    reservations = [z for z in boards['Main'].Zones() if z.GetIsRuleArea()
                    and not z.GetZoneName().startswith('J8 FFC EXIT')]
    main_parts = {r:b for r,b in fps['Main'].items() if r not in ['J8','J10']}
    wheel_parts = {r:b for r,b in fps['Wheel'].items() if r not in ['J9','J11']}
    wheel_box = [min(b[0] for b in wheel_parts.values()),min(b[1] for b in wheel_parts.values()),
                 max(b[2] for b in wheel_parts.values()),max(b[3] for b in wheel_parts.values())]
    free = []; inside_count = 0
    for y in range(250):
        row = []
        for x in range(160):
            left,top = x*STEP,y*STEP
            corners = [p.VECTOR2I(p.FromMM(a),p.FromMM(b)) for a,b in
                       [(left,top),(left+STEP,top),(left,top+STEP),(left+STEP,top+STEP)]]
            inside = all(outline.Contains(c) for c in corners)
            inside_count += inside
            blocked = any(left < b[2] and left+STEP > b[0] and top < b[3] and top+STEP > b[1]
                          for b in main_parts.values())
            blocked |= any(any(z.Outline().Contains(c) for c in corners) for z in reservations)
            row.append(inside and not blocked)
        free.append(row)
    largest = largest_rectangle(free)
    ww,wh = wheel_box[2]-wheel_box[0],wheel_box[3]-wheel_box[1]
    # Scan every axis-aligned origin for an empty rectangle at both rotations.
    prefix = [[0]*161 for _ in range(251)]
    for y in range(250):
        for x in range(160):
            prefix[y+1][x+1] = prefix[y][x+1]+prefix[y+1][x]-prefix[y][x]+(not free[y][x])
    candidates = []
    for w,h in [(ww,wh),(wh,ww)]:
        nx,ny = math.ceil(w/STEP),math.ceil(h/STEP)
        for y in range(251-ny):
            for x in range(161-nx):
                occupied = prefix[y+ny][x+nx]-prefix[y][x+nx]-prefix[y+ny][x]+prefix[y][x]
                if not occupied:candidates.append([x*STEP,y*STEP,w,h])
    result = dict(status='CONSERVATIVE SPACE SCREEN ONLY - NO CAD CHANGES',source_sha256=hashes,
                  grid_mm=STEP,removed_for_space_screen=['Main J8','Main J10','Main J8 FFC exit reservation','Wheel J9','Wheel J11'],
                  retained_main_component_count=len(main_parts),retained_wheel_component_count=len(wheel_parts),
                  main_inside_grid_area_mm2=inside_count*STEP*STEP,
                  main_free_grid_area_mm2=sum(sum(r) for r in free)*STEP*STEP,
                  largest_free_rectangle=largest,wheel_group_courtyard_bounds_mm=wheel_box,
                  wheel_group_rectangle_mm=[round(ww,3),round(wh,3)],
                  unobstructed_group_rectangle_candidates=len(candidates),
                  limitations=['Courtyard bounding rectangles, 0.5 mm grid, rotations 0 and 90 degrees only.',
                               'Empty-area totals are not routing, thermal or mechanical acceptance.',
                               'No candidate means the full wheel bounding envelope cannot be reserved with current Main placement; interleaving/replacement remains possible.',
                               'Main buffers and all destination-rail protections are retained pending circuit review.',
                               'Mounts and mechanism dimensions remain provisional.'])
    OUT.mkdir(exist_ok=True)
    (OUT/'combined-placement-screen.json').write_text(json.dumps(result,indent=2)+'\n')
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="950" viewBox="-8 -12 160 145">',
         '<rect x="-8" y="-12" width="160" height="145" fill="white"/>',
         '<g font-family="sans-serif" fill="#203040">',
         '<text x="0" y="-6" font-size="3">Main + Wheel: placement-space assessment, not a PCB layout</text>']
    chain=outline.Outline(0)
    pts=' '.join(f'{p.ToMM(chain.CPoint(i).x)},{p.ToMM(chain.CPoint(i).y)}' for i in range(chain.PointCount()))
    svg.append(f'<polygon points="{pts}" fill="#f2f6f8" stroke="#203040" stroke-width=".4"/>')
    for r,b in main_parts.items():
        svg.append(f'<rect x="{b[0]}" y="{b[1]}" width="{b[2]-b[0]}" height="{b[3]-b[1]}" fill="#9bb8d1" stroke="#426582" stroke-width=".1"><title>{html.escape(r)}</title></rect>')
    for z in reservations:
        for oi in range(z.Outline().OutlineCount()):
            c=z.Outline().Outline(oi)
            pts=' '.join(f'{p.ToMM(c.CPoint(i).x)},{p.ToMM(c.CPoint(i).y)}' for i in range(c.PointCount()))
            svg.append(f'<polygon points="{pts}" fill="#efb29b" fill-opacity=".65" stroke="#ba5634" stroke-width=".2"><title>{html.escape(z.GetZoneName())}</title></polygon>')
    l=largest
    svg.append(f'<rect x="{l["x_mm"]}" y="{l["y_mm"]}" width="{l["width_mm"]}" height="{l["height_mm"]}" fill="#6eaa68" fill-opacity=".4" stroke="#276222" stroke-width=".3"/>')
    for r,b in wheel_parts.items():
        svg.append(f'<rect x="{90+b[0]-wheel_box[0]}" y="{15+b[1]-wheel_box[1]}" width="{b[2]-b[0]}" height="{b[3]-b[1]}" fill="#cec0e3" stroke="#705b8e" stroke-width=".1"><title>{html.escape(r)}</title></rect>')
    svg.extend([f'<rect x="90" y="15" width="{ww}" height="{wh}" fill="none" stroke="#705b8e" stroke-width=".3"/>',
                '<text x="90" y="10" font-size="2.8">Wheel group, same scale</text>',
                f'<text x="90" y="{20+wh}" font-size="2.6">{ww:.1f} x {wh:.1f} mm envelope</text>',
                '<text x="90" y="90" font-size="2.5">Blue: existing Main courtyards</text>',
                '<text x="90" y="96" font-size="2.5">Orange: retained reservations</text>',
                '<text x="90" y="102" font-size="2.5">Green: largest free rectangle</text>',
                '<text x="90" y="113" font-size="2.5">Harness connectors removed</text>',
                '<text x="90" y="119" font-size="2.5">for this space screen only.</text>', '</g></svg>'])
    (OUT/'combined-placement-screen.svg').write_text('\n'.join(svg))
    assert hashes == {n:hashlib.sha256(f.read_bytes()).hexdigest() for n,f in paths.items()}
    print(json.dumps(result,indent=2))


if __name__ == '__main__':main()
