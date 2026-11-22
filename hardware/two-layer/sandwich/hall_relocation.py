"""Reviewed placement delta for the user's marked Hall-sensor positions.

Run once with KiCad Python. Saved boards are authoritative; routing and all
release checks must be completed after placement. Earlier baselines stay intact.
"""
import json,shutil,hashlib,math
from integrated_encoder import p,BOARDS,HERE,ROOT
from route_main import xy
from assembly_spacing import envelope,active

WORK=ROOT/'build/sandwich/hall-relocation'
POSITIONS={'Upper':{'U7':(17.5,11,0),'U8':(35.5,12.25,180),'U9':(54.25,11.75,0),
    'C16':(12.85,13.75,-90),'C17':(36.85,16.25,0),'C18':(50.75,12.5,-90),'C88':(31.8,4,0)}}
POWER_PAD=(43,2)

def check_positions(name,board):
    fs={f.GetReference():f for f in board.GetFootprints()}
    for ref,(x,y,angle) in POSITIONS.get(name,{}).items():
        assert math.dist(p.ToMM(fs[ref].GetPosition()),(x,y))<.000002,(name,ref)
        assert fs[ref].GetOrientationDegrees()==angle,(name,ref,'rotation')
    if name in ('Lower','Upper'):
        ref='J103' if name=='Lower' else 'J104'
        pad=next(q for q in fs[ref].Pads() if q.GetNumber()=='3')
        assert math.dist(p.ToMM(pad.GetPosition()),POWER_PAD)<.000002,(name,ref)
        assert pad.GetNetname()=='PWR_5V'

def previous_pad_fingerprint(name,board,fingerprint):
    """Undo only the enumerated placement delta in memory for historical checks."""
    check_positions(name,board)
    record=json.loads((HERE/'hall-relocation.json').read_text())['boards'][name]
    fs={f.GetReference():f for f in board.GetFootprints()}
    def put(which):
        def exact(x,y):return p.VECTOR2I(round(x*1e6),round(y*1e6))
        for ref,move in record['placements'].items():
            x,y,angle=move[which];fs[ref].SetPosition(exact(x,y));fs[ref].SetOrientationDegrees(angle)
        for label,move in record['pads'].items():
            ref,pin=label.split('.');q=next(q for q in fs[ref].Pads() if q.GetNumber()==pin);q.SetPosition(exact(*move[which]))
    try:
        put('before');return fingerprint(board)
    finally:put('after')

def record_routing_delta():
    """Freeze the reviewed routing changes without replacing earlier baselines."""
    from validate_routing_cleanup import snapshot_data,via_data,digest,sha
    from routing_corners import corners,staircases
    from review_trace_loops import review
    from usb_return import check_usb
    report={}
    for name,path in BOARDS.items():
        oldpath=WORK/name/path.name
        assert sha(oldpath)==json.loads((HERE/'hall-relocation.json').read_text())['boards'][name]['before_sha256']
        oldboard=p.LoadBoard(str(oldpath));board=p.LoadBoard(str(path));check_positions(name,board)
        old=snapshot_data(oldboard,oldpath);new=snapshot_data(board,path)
        assert not corners(board) and not staircases(board)
        assert not [x for x in review(board) if x['net']!='GND']
        assert previous_pad_fingerprint(name,board,__import__('validate_routing_cleanup').pad_fingerprint)==old['pads_sha256']
        if name=='Lower':check_usb(board)
        if name=='Wheel':assert sha(path)==sha(oldpath)
        removed={k:v for k,v in old['vias'].items() if new['vias'].get(k)!=v}
        added={k:v for k,v in new['vias'].items() if old['vias'].get(k)!=v}
        via_changes=[dict(uuid=t.m_Uuid.AsString(),data=via_data(t)) for t in board.GetTracks() if isinstance(t,p.PCB_VIA) and t.m_Uuid.AsString() in added]
        assert all(v['data'][2]>=.45 and v['data'][3]>=.3 for v in via_changes)
        report[name]={'before_sha256':sha(oldpath),'source_sha256':sha(path),'removed_vias':removed,'added_vias':added,
            'new_via_geometry':via_changes,'widths_iu':new['widths_iu'],'pads_before_sha256':old['pads_sha256'],
            'sharp_bends':0,'staircases':0,'non_ground_loops':0}
    from kicad_output import write
    write(HERE/'hall-routing-review.json',json.dumps(report,indent=2)+'\n')

def apply():
    WORK.mkdir(parents=True,exist_ok=True)
    assert not (HERE/'hall-relocation.json').exists(),'Placement already applied; do not replay.'
    report={'reason':'Hall sensor centres placed inside the three user-marked regions on Upper.',
        'coordinates':'Individual-board millimetres; component side, same orientation as the panel top view.',
        'boards':{},'power_pad_note':'Move J103/J104 pad 3 together to free the middle Hall location; pin number/net unchanged.'}
    for name,path in BOARDS.items():
        shutil.copytree(path.parent,WORK/name)
        b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()}
        record={'before_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'placements':{},'pads':{}}
        for ref,(x,y,angle) in POSITIONS.get(name,{}).items():
            f=fs[ref];record['placements'][ref]={'before':[*p.ToMM(f.GetPosition()),f.GetOrientationDegrees()],'after':[x,y,angle]}
            f.SetPosition(xy(x,y));f.SetOrientationDegrees(angle)
        if name in ('Lower','Upper'):
            ref='J103' if name=='Lower' else 'J104';q=next(q for q in fs[ref].Pads() if q.GetNumber()=='3')
            record['pads'][ref+'.3']={'before':list(p.ToMM(q.GetPosition())),'after':list(POWER_PAD),'net':q.GetNetname()}
            q.SetPosition(xy(*POWER_PAD))
        if name in ('Lower','Upper'):
            b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
        report['boards'][name]=record
    (HERE/'hall-relocation.json').write_text(json.dumps(report,indent=2)+'\n')
    # The two connectors share this copper-only footprint. Preserve its ID and
    # pin numbering so schematic parity and future footprint updates agree.
    import schematic_io as s
    lib=HERE/'MagMouseSandwich.pretty/Wire_Stack_Power_5.kicad_mod';tree=s.parse(lib.read_text())
    for pad in s.allof(tree,'pad'):
        if pad[1]=='3':
            at=next(q for q in pad if isinstance(q,list) and q[0]=='at');at[1:3]=[s.Atom('43'),s.Atom('.75')]
    s.write(lib,tree)

if __name__=='__main__':apply()
