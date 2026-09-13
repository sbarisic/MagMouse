"""Conservatively simplify routed polylines, with native DRC rollback.

Run with KiCad Python. USB pairs, vias, pads, widths and branch vertices stay
fixed. The input is copied to build/trace-cleanup before any source is saved.
Each proposed shortcut deviates by at most 50 um from the old centerline.
Native DRC and the existing electrical acceptance scripts remain authoritative.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import shutil
import subprocess
import sys
import pcbnew as p

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'build/bench-python'))
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

USB = {'USB_DP', 'USB_DM', 'MCU_USB_DP', 'MCU_USB_DM'}
TOL = .05

def point(v):
    # Imported grid routes contain one-nanometre truncation differences.
    # Canonicalize graph vertices to 10 nm; this is far below CAD clearance
    # precision and does not move any pad, via or component.
    return (round(v.x/10)*10, round(v.y/10)*10)
def mm(q): return (q[0]/1e6, q[1]/1e6)
def uid(q): return q.m_Uuid.AsString()

def finish_main_local_runs(board):
    """Reviewed pad-to-exit repair for the user's circled CC_OUT1 run."""
    items=[t for t in board.GetTracks() if type(t)==p.PCB_TRACK and t.GetNetname()=='CC_OUT1'
        and t.GetLayer()==p.F_Cu and all(56.3<=v.x/1e6<=57.4 and 31.4<=v.y/1e6<=34.55
        for v in (t.GetStart(),t.GetEnd()))]
    removed=0
    if items:
        assert {t.GetWidth() for t in items}=={150000}
        net=items[0].GetNetCode()
        for t in items:board.Remove(t)
        t=p.PCB_TRACK(board);t.SetStart(p.VECTOR2I(56325000,31100000));t.SetEnd(p.VECTOR2I(57350000,34500000))
        t.SetWidth(150000);t.SetLayer(p.F_Cu);t.SetNetCode(net);board.Add(t)
        removed=len(items)-1
    # A zero-length stub inside a larger existing via triggers an unstable
    # native crossing report after panel translation. Its copper is redundant.
    zeros=[]
    for t in board.GetTracks():
        if type(t)!=p.PCB_TRACK or t.GetLength()!=0:continue
        if any(isinstance(v,p.PCB_VIA) and v.GetNetCode()==t.GetNetCode() and v.IsOnLayer(t.GetLayer())
            and point(v.GetPosition())==point(t.GetStart()) and v.GetWidth(t.GetLayer())>=t.GetWidth()
            for v in board.GetTracks()):zeros.append(t)
    for t in zeros:board.Remove(t)
    return {'local_run_segment_reduction':removed,'redundant_zero_length_tracks':len(zeros)}

def candidates(board, protected=USB):
    tracks = [t for t in board.GetTracks() if type(t) == p.PCB_TRACK]
    # Degree is counted across widths, so a width transition is never removed.
    at = defaultdict(list)
    for t in tracks:
        for q in (t.GetStart(), t.GetEnd()):
            at[(t.GetNetCode(), t.GetLayer(), point(q))].append(t)
    anchors = defaultdict(list)
    for f in board.GetFootprints():
        for q in f.Pads():
            for layer in board.GetEnabledLayers().CuStack():
                if q.IsOnLayer(layer): anchors[(q.GetNetCode(), layer)].append(q.GetBoundingBox())
    for t in board.GetTracks():
        if type(t) != p.PCB_TRACK:
            for layer in board.GetEnabledLayers().CuStack():
                if t.IsOnLayer(layer): anchors[(t.GetNetCode(), layer)].append(t.GetBoundingBox())
    # Some imported runs have separated centerlines but overlapping round
    # copper caps. Join only mutually nearest, forward-facing loose endpoints
    # of the same net/layer/width whose end caps genuinely overlap.
    loose=defaultdict(list)
    for (net,layer,q),near in at.items():
        if len(near)==1 and not any(r.Contains(p.VECTOR2I(*q)) for r in anchors[(net,layer)]):
            loose[(net,layer,near[0].GetWidth())].append((q,near[0]))
    gap_links={}
    for (net,layer,width),ends in loose.items():
        shapes=[Point(mm(q)) for q,t in ends];tree=STRtree(shapes);nearest={}
        for i,(q,t) in enumerate(ends):
            far=point(t.GetEnd()) if q==point(t.GetStart()) else point(t.GetStart())
            opts=[]
            for j in tree.query(shapes[i].buffer(width/1e6*.999)):
                j=int(j);r,u=ends[j]
                if i==j or uid(t)==uid(u):continue
                other=point(u.GetEnd()) if r==point(u.GetStart()) else point(u.GetStart())
                dx,dy=r[0]-q[0],r[1]-q[1]
                if dx*(q[0]-far[0])+dy*(q[1]-far[1])<=0:continue
                if -dx*(r[0]-other[0])-dy*(r[1]-other[1])<=0:continue
                dist=dx*dx+dy*dy
                if 0<dist<(width*.999)**2:opts.append((dist,j))
            if opts:nearest[i]=min(opts)[1]
        for i,j in nearest.items():
            if nearest.get(j)==i:gap_links[(uid(ends[i][1]),ends[i][0])]=ends[j][1]
    def next_track(t, q):
        near = at[(t.GetNetCode(), t.GetLayer(), q)]
        if len(near) == 1:return gap_links.get((uid(t),q))
        if len(near) != 2: return None
        if any(r.Contains(p.VECTOR2I(*q)) for r in anchors[(t.GetNetCode(),t.GetLayer())]): return None
        other = next(s for s in near if uid(s) != uid(t))
        return other if other.GetWidth() == t.GetWidth() else None
    visited = set(); result = []
    for start in tracks:
        if uid(start) in visited or start.GetNetname() in protected: continue
        chain = [start]; points = [point(start.GetStart()),point(start.GetEnd())]
        visited.add(uid(start))
        for reverse in (False, True):
            if reverse: chain.reverse(); points.reverse()
            while True:
                nxt = next_track(chain[-1], points[-1])
                if nxt is None or uid(nxt) in visited: break
                ends=[point(nxt.GetStart()),point(nxt.GetEnd())]
                ends.sort(key=lambda v:(v[0]-points[-1][0])**2+(v[1]-points[-1][1])**2)
                if ends[0]!=points[-1]:points.append(ends[0])
                end=ends[1]
                chain.append(nxt); points.append(end); visited.add(uid(nxt))
        if len(chain)<2 or points[0]==points[-1]: continue
        old = LineString([mm(q) for q in points])
        new = old.simplify(TOL, preserve_topology=False)
        coords = [(round(x*1e6),round(y*1e6)) for x,y in new.coords]
        if len(coords)>=len(points): continue
        # Shapely's simplification preserves endpoints; explicitly enforce both
        # directions of the corridor bound and reject longer replacement paths.
        if old.hausdorff_distance(new)>TOL+1e-9 or new.length>old.length+1e-9: continue
        # Keep each shortcut independently reversible. A clearance conflict at
        # one end of a long routed net must not restore its unrelated staircases.
        positions={q:i for i,q in enumerate(points)}
        for a,b in zip(coords,coords[1:]):
            lo,hi=positions[a],positions[b]
            subset=[t for t in chain if lo<=positions[point(t.GetStart())]<=hi and lo<=positions[point(t.GetEnd())]<=hi]
            if len(subset)>=2:result.append((subset,[a,b]))
    return result

def run(source):
    work = ROOT/'build/trace-cleanup'/source.stem
    work.mkdir(parents=True,exist_ok=True)
    backup = work/source.name
    if backup.exists() and backup.read_bytes()!=source.read_bytes():
        raise RuntimeError(f'Backup already exists and differs: {backup}; retain it and choose a fresh run directory')
    if not backup.exists(): shutil.copy2(source,backup)
    board = p.LoadBoard(str(source)); original = list(board.GetTracks())
    changes = []; lookup = {}
    protected=USB | ({'VBUS_USB','ACT_5V','CS_PAW'} if source.stem=='Main' else set())
    for chain, coords in candidates(board, protected):
        new = []
        for a,b in zip(coords,coords[1:]):
            t=p.PCB_TRACK(board);t.SetStart(p.VECTOR2I(*a));t.SetEnd(p.VECTOR2I(*b))
            t.SetWidth(chain[0].GetWidth());t.SetLayer(chain[0].GetLayer());t.SetNetCode(chain[0].GetNetCode())
            board.Add(t);new.append(t)
        for t in chain: board.Remove(t)
        index=len(changes)
        for t in new:lookup[uid(t)]=index
        changes.append(dict(old=chain,new=new,active=True))
    # Iterate from the clean baseline: any shortcut implicated in a native
    # clearance/connectivity issue is restored, without changing DRC limits.
    for iteration in range(12):
        board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones());board.BuildConnectivity()
        p.SaveBoard(str(source),board)
        report=work/f'drc-{iteration}.json'
        proc=subprocess.run([str(Path(sys.executable).with_name('kicad-cli.exe')),'pcb','drc','--schematic-parity','--format','json','-o',str(report),str(source)],capture_output=True,text=True)
        if proc.returncode: raise RuntimeError(proc.stdout+proc.stderr)
        data=json.loads(report.read_text());issues=sum((data.get(k,[]) for k in ('violations','unconnected_items','schematic_parity')),[])
        if not issues:break
        revert={lookup[item['uuid']] for issue in issues for item in issue.get('items',[]) if item.get('uuid') in lookup and changes[lookup[item['uuid']]]['active']}
        # A pre-existing near-touch junction may be reported on the untouched
        # stub instead of the new line. Restore nearby changes on that net.
        old_by_id={uid(t):t for t in original}
        for issue in issues:
            for item in issue.get('items',[]):
                old=old_by_id.get(item.get('uuid'))
                if old is None: continue
                for i,c in enumerate(changes):
                    if not c['active'] or c['old'][0].GetNetCode()!=old.GetNetCode() or c['old'][0].GetLayer()!=old.GetLayer():continue
                    a=LineString([mm(point(old.GetStart())),mm(point(old.GetEnd()))])
                    if any(a.distance(LineString([mm(point(t.GetStart())),mm(point(t.GetEnd()))]))<.2 for t in c['old']):revert.add(i)
        if not revert:
            shutil.copy2(backup,source)
            raise RuntimeError(f'{source.stem}: unattributed DRC issue; source restored, inspect {report}')
        for index in revert:
            change=changes[index]
            for t in change['new']:board.Remove(t)
            for t in change['old']:board.Add(t)
            change['active']=False
        print(source.stem,'DRC rollback',iteration,len(revert),flush=True)
    else:
        shutil.copy2(backup,source);raise RuntimeError('DRC did not converge; source restored')
    local={}
    if source.stem=='Main':
        local=finish_main_local_runs(board)
        board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones());p.SaveBoard(str(source),board)
        report=work/'drc-local.json'
        proc=subprocess.run([str(Path(sys.executable).with_name('kicad-cli.exe')),'pcb','drc','--schematic-parity','--format','json','-o',str(report),str(source)],capture_output=True,text=True)
        assert proc.returncode==0,proc.stderr
        data=json.loads(report.read_text())
        assert not any(data.get(k) for k in ('violations','unconnected_items','schematic_parity')),'Local cleanup failed native DRC'
    accepted=[c for c in changes if c['active']]
    result=dict(board=source.stem,tolerance_mm=TOL,candidates=len(changes),accepted_chains=len(accepted),
        old_segments=sum(len(c['old']) for c in accepted),new_segments=sum(len(c['new']) for c in accepted),
        protected_nets=sorted(protected),local_cleanup=local,native_drc='PASS',before_tracks_and_vias=len(original),after_tracks_and_vias=len(list(board.GetTracks())))
    (work/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('board',type=Path);args=ap.parse_args()
    source=args.board.resolve();before=source.read_bytes()
    try:run(source)
    except BaseException:
        source.write_bytes(before)
        raise
