"""Check source preservation, circuit identity, and fresh native KiCad DRC.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import collections
import hashlib
import json
import subprocess
import sys
import pcbnew as p
from prepare import ROOT, DEST, SOURCES, signature


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    evidence = DEST/'review'
    evidence.mkdir(exist_ok=True)
    baseline = json.loads((DEST/'baseline.json').read_text())
    cli = Path(sys.executable).with_name('kicad-cli.exe')
    report = {}
    for name, folder in SOURCES.items():
        src = folder/(name+'.kicad_pcb')
        dst = DEST/name.lower()/(name+'.kicad_pcb')
        a,b = p.LoadBoard(str(src)),p.LoadBoard(str(dst))
        invariant = signature(a)==signature(b)
        schematics = all(sha(x)==sha(dst.parent/x.name) for x in folder.glob('*.kicad_sch'))
        original_unchanged = sha(src)==baseline[name]['source_sha256']
        drc = evidence/(name+'-drc.json')
        subprocess.run([str(cli),'pcb','drc','--format','json','--schematic-parity',
                        '--output',str(drc),str(dst)],check=True)
        result = json.loads(drc.read_text())
        errors = [v for v in result['violations'] if v['severity']=='error']
        routing = collections.defaultdict(lambda: {'segments':0,'length_mm':0})
        via_count = 0
        for t in b.GetTracks():
            if isinstance(t,p.PCB_VIA):
                via_count += 1
            else:
                layer=b.GetLayerName(t.GetLayer())
                routing[layer]['segments']+=1
                routing[layer]['length_mm']+=p.ToMM(t.GetLength())
        report[name] = {'source_sha256':sha(src),'variant_sha256':sha(dst),
            'source_board_unchanged':original_unchanged,'schematics_unchanged':schematics,
            'component_and_pad_net_identity':invariant,'copper_layers':b.GetCopperLayerCount(),
            'footprints':len(list(b.GetFootprints())),'vias':via_count,'routing':dict(routing),
            'drc_findings':dict(collections.Counter(v['type'] for v in result['violations'])),
            'unconnected':len(result['unconnected_items']),
            'schematic_parity':len(result.get('schematic_parity',[])),
            'cad_pass':invariant and schematics and original_unchanged
                and b.GetCopperLayerCount()==2 and not errors
                and not result['unconnected_items'] and not result.get('schematic_parity',[])}
    (evidence/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if all(v['cad_pass'] for v in report.values()) else 1


if __name__=='__main__':
    sys.exit(main())
