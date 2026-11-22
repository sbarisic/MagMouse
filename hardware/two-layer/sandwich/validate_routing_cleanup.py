"""Release checks for the three-board routing cleanup. Run with KiCad Python."""
import collections, hashlib, json, subprocess
from cleanup_routes import p, BOARDS, HERE, WORK, CLI, sha, SIGNALS
from routing_corners import corners, staircases
from validate_circuit_fixes import geometry
from review_trace_loops import review
from usb_return import check_usb
from hall_relocation import previous_pad_fingerprint

def digest(data):return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()

def pad_fingerprint(board):
    return digest(sorted((f.GetReference(),f.GetValue(),str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),p.ToMM(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer(),
        sorted((q.GetNumber(),q.GetNetname(),p.ToMM(q.GetPosition()),p.ToMM(q.GetSize()),p.ToMM(q.GetDrillSize()),int(q.GetShape()),q.GetOrientationDegrees()) for q in f.Pads())) for f in board.GetFootprints()))

def via_data(t):return (t.GetNetname(),p.ToMM(t.GetPosition()),p.ToMM(t.GetWidth(p.F_Cu)),p.ToMM(t.GetDrillValue()))

def wide_usb(board):
    return sorted((t.GetNetname(),board.GetLayerName(t.GetLayer()),p.ToMM(t.GetWidth()),sorted([p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())]))
        for t in board.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetNetname() in SIGNALS and p.ToMM(t.GetWidth())>=.5)

def snapshot_data(board,path):
    widths=collections.defaultdict(set)
    for t in board.GetTracks():
        if not isinstance(t,p.PCB_VIA):widths[t.GetNetname()+' '+board.GetLayerName(t.GetLayer())].add(t.GetWidth())
    return dict(source_sha256=sha(path),pads_sha256=pad_fingerprint(board),geometry_sha256=digest(geometry(board)),
        rules_sha256=digest(json.loads(path.with_suffix('.kicad_pro').read_text())['board']['design_settings']),
        vias={t.m_Uuid.AsString():digest(via_data(t)) for t in board.GetTracks() if isinstance(t,p.PCB_VIA)},
        widths_iu={k:sorted(v) for k,v in sorted(widths.items())},wide_usb=wide_usb(board),
        tracks=sum(not isinstance(t,p.PCB_VIA) for t in board.GetTracks()),
        length_mm=sum(p.ToMM(t.GetLength()) for t in board.GetTracks() if not isinstance(t,p.PCB_VIA)),
        sharp_bends=len(corners(board)),staircases=len(staircases(board)))

def check_usb_geometry(board):
    old=json.loads((HERE/'routing-cleanup-baseline.json').read_text())['Lower']
    assert json.loads(json.dumps(wide_usb(board)))==old['wide_usb'],'USB wide-pair spacing/geometry changed'
    for t in board.GetTracks():
        if isinstance(t,p.PCB_VIA) and t.GetNetname() in SIGNALS:
            assert old['vias'].get(t.m_Uuid.AsString())==digest(via_data(t)),'USB transition moved'
    return check_usb(board)

def main():
    WORK.mkdir(parents=True,exist_ok=True)
    baseline=json.loads((HERE/'routing-cleanup-baseline.json').read_text());report={}
    hall=json.loads((HERE/'hall-routing-review.json').read_text())
    for name,path in BOARDS.items():
        board=p.LoadBoard(str(path));old=baseline[name];new=snapshot_data(board,path)
        assert previous_pad_fingerprint(name,board,pad_fingerprint)==old['pads_sha256'],(name,'unapproved pad change')
        for field in ('geometry_sha256','rules_sha256'):assert new[field]==old[field],(name,field)
        delta=hall[name];assert delta['source_sha256']==sha(path),'Hall review is stale'
        expected_vias={k:v for k,v in old['vias'].items() if k not in delta['removed_vias']}
        expected_vias.update(delta['added_vias'])
        assert all(new['vias'].get(k)==v for k,v in expected_vias.items()),name+' unapproved via change'
        assert not (set(delta['removed_vias']) & set(new['vias'])),name+' removed via restored'
        extra=[via_data(t) for t in board.GetTracks() if isinstance(t,p.PCB_VIA) and t.m_Uuid.AsString() not in old['vias']]
        unexpected=[via_data(t) for t in board.GetTracks() if isinstance(t,p.PCB_VIA) and t.m_Uuid.AsString() not in expected_vias]
        assert all(n=='GND' and abs(w-.45)<.000001 and abs(d-.3)<.000001 for n,xy,w,d in unexpected),unexpected
        assert new['widths_iu']==delta['widths_iu'],name+' unreviewed trace widths'
        assert not corners(board),(name,corners(board))
        assert not staircases(board),(name,staircases(board))
        assert not [r for r in review(board) if r['net']!='GND'],name+' trace topology'
        output=WORK/(name+'-release-drc.json')
        subprocess.run([str(CLI),'pcb','drc','--schematic-parity','--format','json','-o',str(output),str(path)],check=True,stdout=subprocess.DEVNULL)
        drc=json.loads(output.read_text());assert not (drc['violations']+drc['unconnected_items']+drc.get('schematic_parity',[])),(name,drc)
        report[name]=dict(source_sha256=sha(path),before_sharp_bends=old['sharp_bends'],after_sharp_bends=0,
            before_staircases=old['staircases'],after_staircases=0,before_tracks=old['tracks'],after_tracks=new['tracks'],
            before_total_trace_mm=old['length_mm'],after_total_trace_mm=new['length_mm'],added_vias_since_cleanup_baseline=extra,
            outlines_and_rules_unchanged=True,placement_and_via_changes='hall-relocation.json and hall-routing-review.json',
            trace_widths_match_hall_review=True,drc=0,unconnected=0,schematic_parity=0)
        if name=='Lower':report[name]['usb']=check_usb_geometry(board)
        print(name,old['sharp_bends'],'-> 0 sharp bends;',old['staircases'],'-> 0 staircases; DRC 0',flush=True)
    (HERE/'routing-cleanup-review.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
