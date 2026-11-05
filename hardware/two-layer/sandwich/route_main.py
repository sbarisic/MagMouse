"""Route independent Main boards through checked Specctra sessions.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import argparse,json,sys,subprocess,collections,re,math
import pcbnew as p
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SCRATCH=ROOT/'build/sandwich/main-routing'
CLI=Path(sys.executable).with_name('kicad-cli.exe')
sys.path.insert(0,str(ROOT/'hardware/common'))
from board_geometry import signature

def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def track(board,net,points,width=.15,layer=p.F_Cu):
    for a,b in zip(points,points[1:]):
        if a==b:continue
        t=p.PCB_TRACK(board);t.SetNet(board.FindNet(net));t.SetLayer(layer)
        t.SetStart(xy(*a));t.SetEnd(xy(*b));t.SetWidth(p.FromMM(width));board.Add(t)
def via(board,net,point,size=.6,drill=.3):
    v=p.PCB_VIA(board);v.SetNet(board.FindNet(net));v.SetPosition(xy(*point))
    v.SetWidth(p.FromMM(size));v.SetDrill(p.FromMM(drill));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);board.Add(v)
def check(name):
    folder=HERE/name.lower();path=folder/(name+'.kicad_pcb')
    subprocess.run([str(CLI),'pcb','drc','--format','json','--schematic-parity','-o',str(folder/(name+'-drc.json')),str(path)],check=True)
    d=json.loads((folder/(name+'-drc.json')).read_text())
    print(name,dict(collections.Counter(v['type'] for v in d['violations'])),'unconnected',len(d['unconnected_items']),'parity',len(d.get('schematic_parity',[])),flush=True)
    return d
def ground(board):
    if any(not z.GetIsRuleArea() for z in board.Zones()):return
    for layer in (p.F_Cu,p.B_Cu):
        z=p.ZONE(board);z.SetLayer(layer);z.SetNet(board.FindNet('GND'))
        z.SetZoneName('GND '+board.GetLayerName(layer));z.SetLocalClearance(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(p.FromMM(.2));z.SetThermalReliefSpokeWidth(p.FromMM(.25));z.SetMinThickness(p.FromMM(.15))
        z.Outline().NewOutline()
        for a,b in ((-1,-1),(71,-1),(71,101),(-1,101)):z.Outline().Append(p.FromMM(a),p.FromMM(b))
        board.Add(z)
def prepare(name):
    folder=HERE/name.lower();path=folder/(name+'.kicad_pcb')
    board=p.LoadBoard(str(path));assert not list(board.GetTracks()),'Prepare only unrouted input'
    project=json.loads(path.with_suffix('.kicad_pro').read_text())
    settings=project['net_settings']
    settings['netclass_patterns']=[n for n in settings['netclass_patterns'] if not n['pattern'].startswith('BTN_')]
    default=next(c for c in settings['classes'] if c['name']=='Default')
    groundclass=dict(default);groundclass['name']='Ground';groundclass['priority']=3
    settings['classes'].append(groundclass);settings['netclass_patterns'].append({'netclass':'Ground','pattern':'GND'})
    # Short regulator/optical rails need the same current-carrying width as power.
    for net in ('BUCK_SW','OPT_3V3','OPT_1V9','MA735_3V3','RGB_5V'):
        settings['netclass_patterns'].append({'netclass':'Power','pattern':net})
    path.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
    ground(board)
    for item in board.GetDrawings():
        if isinstance(item,p.PCB_TEXT):item.SetText(item.GetText().replace('UNROUTED','ROUTING PROTOTYPE'))
    p.SaveBoard(str(path),board)
    export(name)
def export(name):
    SCRATCH.mkdir(parents=True,exist_ok=True)
    path=HERE/name.lower()/(name+'.kicad_pcb');board=p.LoadBoard(str(path))
    assert p.ExportSpecctraDSN(board,str(SCRATCH/(name+'.dsn')))
    # Specctra uses a single width for a net; preserve pre-routed USB trunks and
    # permit the connector/ESD fanout to use narrow escapes.
    dsn=SCRATCH/(name+'.dsn');text=dsn.read_text()
    # Native KiCad pours are restored after import; omitting them here allows
    # full two-layer signal routing instead of treating unfilled plane outlines
    # as pre-existing copper. Ground is filled and stitched by finish_main.py.
    text='\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('(plane GND '))+'\n'
    text=re.sub(r'(\(class USB(?:\s|\n).*?)(?=\n    \(class |\n  \)\n  \(wiring)',lambda m:m[0].replace('(width 1100)','(width 150)'),text,flags=re.S)
    dsn.write_text(text)
def import_session(name):
    path=HERE/name.lower()/(name+'.kicad_pcb');board=p.LoadBoard(str(path));before=signature(board)
    placement={f.GetReference():(tuple(p.ToMM(f.GetPosition())),f.GetOrientationDegrees()) for f in board.GetFootprints()}
    assert p.ImportSpecctraSES(board,str(SCRATCH/(name+'.ses')))
    assert signature(board)==before,'Router modified component/net identity'
    for f in board.GetFootprints():
        position,angle=placement[f.GetReference()]
        assert math.dist(position,p.ToMM(f.GetPosition()))<.00015 and angle==f.GetOrientationDegrees(),'Router moved a component beyond Specctra coordinate rounding'
    for t in board.GetTracks():
        if isinstance(t,p.PCB_VIA):
            if t.GetDrillValue()<p.FromMM(.3):t.SetDrill(p.FromMM(.3))
        elif t.GetWidth()<p.FromMM(.127):t.SetWidth(p.FromMM(.127))
    board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones());p.SaveBoard(str(path),board)
    check(name)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('board',choices=['Lower','Upper']);a.add_argument('action',choices=['prepare','export','import','check']);args=a.parse_args()
    {'prepare':prepare,'export':export,'import':import_session,'check':check}[args.action](args.board)
