"""Parameterized PETG bench parts, build123d 0.11.1. No final-shell geometry.

Run with --out build/bench-mechanics for a trial; default writes reviewed outputs.
Magnet dimensions are explicit trial defaults, not supplier acceptance.
"""
import argparse,json,hashlib
from pathlib import Path
from build123d import Box,Cylinder,Pos,Rot,Compound,export_step,export_stl,ExportSVG

HERE=Path(__file__).resolve().parent
PARAMS=dict(base_x=250,base_y=260,base_thickness=6,tile_x=125,tile_y=130,
            m3_clearance=3.4,board_thickness=1.578,under_board_minimum=5,
            magnet_diameter=5,magnet_thickness=2,magnet_fit_allowance=.3,
            lever_length=35,flexure_thickness=.8,button_travel=1.5,
            motor_bolt_circle=None,motor_hole_count=4,lens_retention_width=None,
            board_under_height=15)
SUPPORT_POSTS=[(49,15),(82,15),(20,95),(110,106),
               (69.5,155),(120.5,172),(73.5,225),(103.5,225)]

def block(x,y,z,cx=0,cy=0,cz=0):return Pos(cx,cy,cz+z/2)*Box(x,y,z)
def hole(d,h,x=0,y=0,z=0):return Pos(x,y,z+h/2)*Cylinder(d/2,h)
def slot(length,width,height,x=0,y=0,z=0):
    return block(length-width,width,height,x,y,z)+hole(width,height,x-(length-width)/2,y,z)+hole(width,height,x+(length-width)/2,y,z)


def volume(shape):
    if shape is None:return 0
    if hasattr(shape,'volume'):return shape.volume
    return sum(volume(s) for s in shape)


def validate_configuration(cfg):
    assert cfg['board_under_height']-1.5>=cfg['under_board_minimum'],'Insufficient solder-joint clearance'
    assert 0<cfg['button_travel']<5,'Stop must retain positive thickness and travel'
    assert cfg['magnet_diameter']+cfg['magnet_fit_allowance']<8,'Magnet pocket needs a retaining wall'
    assert cfg['base_x']==2*cfg['tile_x'] and cfg['base_y']==2*cfg['tile_y'],'Tile sizes must match the base'
    assert cfg['tile_x']==125 and cfg['tile_y']==130,'Changing tile size requires regenerating the datum grid'

def parts(cfg):
    parts={};m3=cfg['m3_clearance'];th=cfg['base_thickness']
    for row in range(2):
        for col in range(2):
            x0=col*125;y0=row*130
            b=block(125,130,th,62.5,65)
            # Full-depth optical window; no grid hole may cut into its frame.
            window=block(50,60,th+2,65.5-x0,92.5-y0,-1)
            b-=window
            for x in range(10,125,10):
                for y in range(10,130,10):
                    if 36<x+x0<95 and 58<y+y0<127:continue
                    if any((x+x0-px)**2+(y+y0-py)**2<36 for px,py in SUPPORT_POSTS):continue
                    b-=hole(m3,th+2,x,y,-1)
            for x,y in SUPPORT_POSTS:
                if x0<x<x0+125 and y0<y<y0+130:b-=hole(m3,th+2,x-x0,y-y0,-1)
            parts[f'base_{col}_{row}']=b
    # Join adjacent tiles with screws/washers; print bridges independently.
    for suffix,locations in [('x',[-17.5,-7.5,7.5,17.5]),('y',[-20,-10,10,20])]:
        b=block(50,12,4)
        for x in locations:b-=hole(m3,6,x,0,-1)
        parts['tile_joiner_'+suffix]=b
    # Outside-edge body; only 0.3 mm lip projects beneath PCB.
    b=block(10,8,6,-5)+block(.3,5,1,.15,0,5)
    b-=hole(m3,10,-5,0,-1);parts['edge_saddle']=b
    cap=block(10.3,8,2,-4.85);cap-=hole(m3,4,-5,0,-1)
    parts['edge_cap']=cap
    # M3 pitch is a multiple of the base grid; shim to actual insulation.
    for name,width,channel,pitch in [('ribbon',60,39,50),('encoder',32,12,20),('pair',20,4,10)]:
        base=block(width,12,4);top=block(width,12,4)-block(channel,8,1.6,0,0,-.01)
        for x in [-pitch/2,pitch/2]:
            base-=hole(m3,6,x,0,-1);top-=hole(m3,6,x,0,-1)
        parts[name+'_clamp_base']=base;parts[name+'_clamp_cap']=top
    carrier=block(32,24,4)+block(32,4,30,0,10,4)
    carrier-=block(20,6,22,0,10,8)
    for x in [-11,11]:carrier-=slot(14,m3,6,x,0,-1)
    for x in [-13,13]:
        cut=block(m3,6,10,x,10,13)
        for z in [13,23]:cut+=Pos(x,10,z)*Rot(90,0,0)*Cylinder(m3/2,6)
        carrier-=cut
    parts['encoder_carrier']=carrier
    clip=block(9.3,8,6,11.35,8)
    # Front screw flange stops at the carrier face; rear tongue stays inside
    # its open window instead of occupying the carrier arm's volume.
    clip-=block(7,5,8,13.5,10.5,-1)
    clip-=block(1,cfg['board_thickness']+.25,8,6.95,6.4+cfg['board_thickness']/2,-1)
    clip-=Pos(13,8,3)*Rot(90,0,0)*Cylinder(m3/2,10)
    parts['encoder_edge_clip']=clip
    # Slotted plate permits a separate measured motor adapter.
    plate=block(60,60,5)-hole(12,7,0,0,-1)
    for x in [-20,20]:
        for y in [-20,20]:plate-=slot(16,m3,7,x,y,-1)
    if cfg['motor_bolt_circle'] is not None:
        import math
        for i in range(cfg['motor_hole_count']):
            a=2*math.pi*i/cfg['motor_hole_count'];r=cfg['motor_bolt_circle']/2
            plate-=hole(m3,7,r*math.cos(a),r*math.sin(a),-1)
    parts['motor_plate']=plate
    # Fixed magnet pocket in a moving lever; mounting pedestal is outside PCB.
    length=cfg['lever_length'];flex=cfg['flexure_thickness'];travel=cfg['button_travel']
    lever=block(14,18,6,-7)+block(length,8,flex,length/2,0,5)
    pocket_height=cfg['magnet_thickness']+1.2
    lever+=block(9,10,pocket_height,length-4.5,0,5)
    # Magnet inserts from above and is retained with adhesive after polarity check.
    lever-=hole(cfg['magnet_diameter']+cfg['magnet_fit_allowance'],cfg['magnet_thickness']+.2,length-4.5,0,6)
    for y in [-5,5]:lever-=hole(m3,7,-7,y,-1)
    parts['button_lever']=lever
    # Separate stop: positioned below lever, travel set by shims and fixture height.
    stop=block(12,16,5-travel)-hole(m3,7,0,0,-1)
    parts['button_stop']=stop
    return parts


def assembly(parts,cfg,out):
    """Dimensioned fixture layout and assembly proxies; no unknown part fit claim."""
    from build123d import Polygon,make_face,extrude
    data=json.loads((HERE/'board-interfaces.json').read_text())
    z=cfg['base_thickness']+cfg['board_under_height'];shapes=[];boards=[]
    for row in range(2):
        for col in range(2):shapes.append(Pos(col*125,row*130,0)*parts[f'base_{col}_{row}'])
    for name,(ox,oy) in [('Main',(25,20)),('Wheel',(60.5,160))]:
        face=make_face(Polygon(*(tuple(q) for q in data[name]['outline']),align=None))
        for ring in data[name]['holes']:face-=make_face(Polygon(*(tuple(q) for q in ring),align=None))
        board=Pos(ox,oy,z)*extrude(face,amount=cfg['board_thickness'])
        assert board.is_valid and board.volume>100,'Invalid source PCB envelope'
        board.label=name+' envelope';boards.append(board);shapes.append(board)
    # Edge saddle orientation points its 0.3 mm lip toward the board.
    sites=[(49,20,90),(82,20,90),(25,95,0),(105,106,180),
           (69.5,160,90),(115.5,172,180),(73.5,220,-90),(103.5,220,-90)]
    overlaps=[]
    for x,y,a in sites:
        saddle=Pos(x,y,z-6)*Rot(0,0,a)*parts['edge_saddle']
        cap=Pos(x,y,z+cfg['board_thickness'])*Rot(0,0,a)*parts['edge_cap']
        for board in boards:
            collision=saddle.intersect(board)
            overlap=volume(collision)
            assert overlap<1e-5,('saddle intersects board volume',x,y,overlap)
        shapes.extend([saddle,cap]);overlaps.append(dict(x=x,y=y,rotation=a,board_overlap_mm3=0))
    carrier=Pos(150,60,6)*parts['encoder_carrier']
    shapes += [carrier,Pos(180,60,40)*parts['motor_plate']]
    # Illustrated metal threaded rods attach the plate slots to base grid holes.
    for x in [155,195]:
        for y in [40,80]:shapes.append(hole(3,34,x,y,6))
    # Upright encoder envelope; side clips are adjusted only after actual fit.
    encoder=block(14,cfg['board_thickness'],18,150,66.4+cfg['board_thickness']/2,14)
    shapes.append(encoder)
    for a in [0,180]:
        # Left clip is mirrored in X, not flipped through the board plane.
        clip=parts['encoder_edge_clip'] if a==0 else parts['encoder_edge_clip'].mirror(__import__('build123d').Plane.YZ)
        clip=Pos(150,60,18)*clip
        collision=clip.intersect(encoder)
        assert volume(collision)<1e-5,'Encoder clip cuts board envelope'
        assert volume(clip.intersect(carrier))<1e-5,'Encoder clip intersects carrier arm'
        shapes.append(clip)
    for y in [150,180]:
        shapes += [Pos(85,y,6)*parts['ribbon_clamp_base'],Pos(85,y,10)*parts['ribbon_clamp_cap']]
    whole=Compound(shapes);export_step(whole,out/'assembly-envelope.step')
    visible,hidden=whole.project_to_viewport((350,-440,380))
    svg=ExportSVG();svg.add_shape(visible);svg.write(out/'assembly-envelope.svg')
    clearance=cfg['board_under_height']-1.5
    assert clearance>=cfg['under_board_minimum'],'Insufficient solder-joint clearance'
    (out/'assembly-clearance.json').write_text(json.dumps(dict(
        board_underside_above_base_mm=cfg['board_under_height'],joint_protrusion_limit_mm=1.5,
        joint_to_base_clearance_mm=clearance,saddles=overlaps,
        component_height_requirement='Measure underside components; lower surface must remain at least 5 mm above base',
        unresolved=['motor adapter and shaft geometry','lens retention and optical working height','encoder clip contact and magnet gap','flexure fatigue and coil fit'],
        board_source_sha256={n:v['source_sha256'] for n,v in data.items()},
        model_scope='PCB outline envelopes and printed supports; no fabricated component-height certification'),indent=2)+'\n')
    text=['<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">',
          '<rect width="297" height="210" fill="white"/><g font-family="sans-serif" font-size="3" fill="#222">',
          '<text x="10" y="12" font-size="5">Rev-A PETG bench / assembly dimensions in mm</text>',
          '<text x="10" y="20">PCB/component envelopes are illustrative; measure parts before setting supports.</text>',
          '<rect x="12" y="35" width="125" height="130" fill="#eee" stroke="#555"/>',
          '<path d="M74.5 35V165 M12 100H137" stroke="#555"/>',
          '<text x="30" y="32">250 overall (shown at 1:2)</text>',
          '<text x="15" y="175">4 tiles: 125 × 130 × 6 each; grid 10; M3 holes Ø3.4</text>',
          '<rect x="155" y="128" width="125" height="6" fill="#bbb"/>',
          '<rect x="170" y="95" width="85" height="1.578" fill="#417648"/>',
          '<path d="M177 97V101 M215 97V101" stroke="#333"/>',
          '<text x="150" y="45">Height setup (side view, schematic)</text>',
          '<text x="150" y="57">Board underside: 15–35 above base top</text>',
          '<text x="150" y="66">Solder protrusion: less than 1.5</text>',
          '<text x="150" y="75">Lowest joint/component: ≥5 clear to base</text>',
          '<text x="150" y="84">Saddle lip: 0.3 engagement; never over parts</text>',
          '<text x="150" y="146">M3 rods, nuts and washers set saddle height.</text>',
          '<text x="150" y="156">Clamps load insulation, not solder joints.</text>',
          '<text x="150" y="166">Motor hole pattern / lens retention: measure first.</text>',
          '<path d="M12 190H112" stroke="black"/><text x="12" y="198">100 mm print calibration / print at 100%</text>',
          '<text x="145" y="198">Pending supplier/CAM approval; bench use only</text></g></svg>']
    (out/'assembly-dimensions.svg').write_text('\n'.join(text),encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=HERE/'generated');ap.add_argument('--config',type=Path)
    args=ap.parse_args();cfg=dict(PARAMS)
    if args.config:cfg.update(json.loads(args.config.read_text()))
    validate_configuration(cfg)
    out=args.out;out.mkdir(parents=True,exist_ok=True);report=[]
    generated=parts(cfg)
    for name,part in generated.items():
        assert part.is_valid and len(part.solids())==1,(name,'invalid or disconnected solid')
        dims=tuple(part.bounding_box().size)
        assert dims[0]<=180 and dims[1]<=180,(name,dims)
        export_step(part,out/(name+'.step'));export_stl(part,out/(name+'.stl'),tolerance=.05,angular_tolerance=.1)
        visible,hidden=part.project_to_viewport((180,-220,200))
        svg=ExportSVG();svg.add_layer('visible');svg.add_shape(visible,layer='visible');svg.write(out/(name+'.svg'))
        report.append(dict(name=name,dimensions_mm=dims,volume_mm3=part.volume,valid=True,solids=1))
    assembly(generated,cfg,out)
    (out/'validation.json').write_text(json.dumps(dict(parameters=cfg,parts=report,
        status='Valid printable candidates; actual support, magnet and motor fit pending',
        generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
    import csv
    rows=[]
    for row in report:
        name=row['name'];qty=1
        if name.startswith('tile_joiner'):qty=4
        elif name in ['edge_saddle','edge_cap']:qty=8
        elif name=='encoder_edge_clip':qty=2
        elif name.startswith(('ribbon_clamp','encoder_clamp')):qty=2
        elif name.startswith('pair_clamp'):qty=8
        elif name.startswith('button_'):qty=3
        rows.append(dict(Item=name,Required_quantity=qty,Purchase_quantity=qty,
            Material='PETG printed part',Solid_volume_cm3=round(qty*row['volume_mm3']/1000,3),
            Price_EUR='',Shipping_EUR='',Status='Price from selected filament and slicer usage remains pending'))
    for item,required,purchase in [('M3 threaded rod 60 mm',12,12),('M3 nuts',110,150),('M3 washers',110,150),('M3 screws 16/25 mm assortment',70,100)]:
        rows.append(dict(Item=item,Required_quantity=required,Purchase_quantity=purchase,Material='Hardware allowance; verify lengths on assembled sample',Solid_volume_cm3='',Price_EUR='',Shipping_EUR='',Status='Unquoted consumer hardware; no purchase authorised'))
    with (out/'fixture-purchasing.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print('Validated and exported',len(report),'single-solid parts')

if __name__=='__main__':main()
