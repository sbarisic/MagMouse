"""Soldered interface invariants, including negative-testable fill exclusion."""
import json,math
import pcbnew as p
from build_panel import SOURCES,HERE,ROOT,sha,save_json
from wire_interfaces import INTERFACES,SPECS,pads,footprint_name
from review_details import harness_rows


def verify(boards):
    count=0
    for name,b in boards.items():
        fs={f.GetReference():f for f in b.GetFootprints()}
        for ref,kind in INTERFACES[name].items():
            f=fs[ref];qq={q.GetNumber():q for q in f.Pads()}
            expected=pads(kind)
            assert set(qq)=={row[0] for row in expected},(name,ref,'missing wire pad')
            assert f.GetFPID().GetLibNickname()=='MagMouseModular' and f.GetFPID().GetLibItemName()==footprint_name(kind),(name,ref,'footprint')
            for key in ['MPN','Manufacturer','LCSC']:
                field=f.GetField(key);assert not field or not field.GetText(),(name,ref,'obsolete purchasing identity',key)
            for number,x,y,drill,size in expected:
                q=qq[number];count+=1
                assert q.GetAttribute()==p.PAD_ATTRIB_PTH,(name,ref,number,'not plated through-hole')
                assert all(abs(p.ToMM(v)-size)<1e-5 for v in q.GetSize()),(name,ref,number,'pad size')
                assert all(abs(p.ToMM(v)-drill)<1e-5 for v in q.GetDrillSize()),(name,ref,number,'drill')
                assert not q.IsOnLayer(p.F_Paste) and not q.IsOnLayer(p.B_Paste),(name,ref,number,'unintended paste')
                assert q.IsOnLayer(p.F_Mask) and q.IsOnLayer(p.B_Mask),(name,ref,number,'masked wire land')
                for other,xx,yy,_,_ in expected:
                    actual=p.ToMM((q.GetPosition()-qq[other].GetPosition()).EuclideanNorm())
                    assert abs(actual-math.hypot(x-xx,y-yy))<2e-5,(name,ref,'pitch')
    rows=harness_rows(boards)
    ribbon=[r for r in rows if r['Harness']=='Soldered ribbon']
    assert len(ribbon)==30 and sum(r['Signal']=='GND' for r in ribbon)==15,'Missing ribbon ground conductors'
    encoder=[r for r in rows if r['Harness']=='Encoder']
    assert len(encoder)==8 and sum(r['Signal']=='GND' for r in encoder)==3,'Missing encoder ground conductors'
    assert count==sum(len(pads(k)) for refs in INTERFACES.values() for k in refs.values())
    return dict(terminations=sum(map(len,INTERFACES.values())),plated_wire_holes=count,
                conductors=len(rows),ribbon_ground_conductors=15,encoder_ground_conductors=3)


def verify_fill(board,rows):
    vias={t.m_Uuid.AsString():t for t in board.GetTracks() if isinstance(t,p.PCB_VIA)}
    assert len(rows)==len(vias) and {r['UUID'] for r in rows}==set(vias),'Fill inventory includes a component hole or omits a via'
    for row in rows:
        via=vias[row['UUID']]
        for field,value in [('KiCad X mm',p.ToMM(via.GetPosition().x)),('KiCad Y mm',p.ToMM(via.GetPosition().y)),('Drill mm',p.ToMM(via.GetDrillValue()))]:
            assert abs(float(row[field])-value)<1e-5,'Fill coordinate or drill differs from actual via'


def verify_fixture_alignment(report=None):
    if report is None:report=json.loads((ROOT/'mechanical/bench/generated/assembly-clearance.json').read_text())
    assert report['board_source_sha256']=={n:sha(path) for n,path in SOURCES.items()},'Fixture source snapshot is stale'
    manifest=json.loads((HERE/'panel-manifest.json').read_text());expected=[]
    origins={'Main':(25,20),'Wheel':(60.5,160)}
    for tab in manifest['tabs']:
        name=tab['board']
        if name not in origins:continue
        translation=manifest['units'][name]['translation_mm'];origin=origins[name]
        expected.append([tab['center'][i]-translation[i]+origin[i] for i in [0,1]])
    actual=[[r['x'],r['y']] for r in report['saddles']]
    assert len(actual)==len(expected) and all(any(math.dist(a,e)<1e-5 for a in actual) for e in expected),'Fixture saddle differs from reviewed support site'


if __name__=='__main__':
    result=verify({n:p.LoadBoard(str(path)) for n,path in SOURCES.items()})
    result['source_sha256']={n:sha(path) for n,path in SOURCES.items()}
    save_json(HERE/'package/evidence/wire-interfaces.json',result)
    print(json.dumps(result,indent=2))
