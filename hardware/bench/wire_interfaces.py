"""Rev-A soldered interconnect contract. Dimensions are millimetres."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
LIB=ROOT/'hardware/modular/MagMouseModular.pretty'
INTERFACES={'Main':{'J8':'Signal_2x15','J6':'Signal_2x04','J10':'Power_1x02',
                    'J2':'Power_1x02','J3':'Power_1x02','J4':'Power_1x02'},
            'Wheel':{'J9':'Signal_2x15','J11':'Power_1x02'},
            'Encoder':{'J7':'Signal_2x04'}}
SPECS={'Signal_2x15':(15,2,.8,1.8),'Signal_2x04':(4,2,.8,1.8),'Power_1x02':(2,1,1.1,2.2)}

def pads(kind):
    columns,rows,drill,size=SPECS[kind]
    return [(str(col*rows+row+1),(col-(columns-1)/2)*2.54,(row-(rows-1)/2)*2.54,drill,size)
            for col in range(columns) for row in range(rows)]

def footprint_name(kind):return 'Wire_'+kind+'_P2.54mm'

def generate_footprints():
    for kind in SPECS:
        name=footprint_name(kind);pp=pads(kind)
        x=max(abs(q[1])+q[4]/2 for q in pp)+.5;y=max(abs(q[2])+q[4]/2 for q in pp)+.5
        content=[f'(footprint "{name}" (version 20260206) (generator "pcbnew") (layer "F.Cu")',
            '(descr "Direct soldered wires; no connector fitted; component holes must NOT be filled")',
            '(attr through_hole)',f'(fp_text reference "REF**" (at 0 {-y-1}) (layer "F.SilkS") (effects (font (size .8 .8) (thickness .12))))',
            f'(fp_text value "{name}" (at 0 {y+1}) (layer "F.Fab") (effects (font (size .8 .8) (thickness .12))))',
            f'(fp_rect (start {-x} {-y}) (end {x} {y}) (stroke (width .05) (type default)) (fill none) (layer "F.CrtYd"))',
            f'(fp_rect (start {-x+.15} {-y+.15}) (end {x-.15} {y-.15}) (stroke (width .1) (type default)) (fill none) (layer "F.Fab"))']
        for number,px,py,drill,size in pp:
            shape='rect' if number=='1' else 'circle'
            content.append(f'(pad "{number}" thru_hole {shape} (at {px} {py}) (size {size} {size}) (drill {drill}) (layers "*.Cu" "*.Mask"))')
        content.append(')');(LIB/(name+'.kicad_mod')).write_text('\n'.join(content)+'\n')

if __name__=='__main__':generate_footprints()
