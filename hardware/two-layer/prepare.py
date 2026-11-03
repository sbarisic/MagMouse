"""Create isolated two-layer routing inputs. Run with KiCad 10 Python.

SPDX-License-Identifier: GPL-3.0-or-later
This explicitly rebuilds the variant; never run over manually edited outputs.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'hardware/two-layer'
SOURCES = {'Main': ROOT/'hardware/modular/main',
           'Wheel': ROOT/'hardware/modular/wheel',
           'Encoder': ROOT/'hardware/encoder'}


def signature(board):
    return {f.GetReference(): {'value': f.GetValue(),
        'footprint': str(f.GetFPID().GetLibItemName()),
        'pads': sorted((p.GetNumber(), p.GetNetname()) for p in f.Pads())}
        for f in board.GetFootprints()}


def create(name):
    source = SOURCES[name]
    folder = DEST/name.lower()
    folder.mkdir(parents=True, exist_ok=True)
    for src in source.iterdir():
        if src.suffix in ('.kicad_sch', '.kicad_pro', '.kicad_dru'):
            shutil.copyfile(src, folder/src.name)
    for table in ('sym-lib-table', 'fp-lib-table'):
        text = (source/table).read_text()
        def relocate(m):
            target = (source/m[1]).resolve()
            import os
            return '${KIPRJMOD}/'+os.path.relpath(target, folder).replace('\\','/')
        text = re.sub(r'\$\{KIPRJMOD\}/([^"\s]+)', relocate, text)
        (folder/table).write_text(text, encoding='utf-8')
    original = source/(name+'.kicad_pcb')
    board = pcb.LoadBoard(str(original))
    before = signature(board)
    removed = 0
    for track in list(board.GetTracks()):
        if not isinstance(track, pcb.PCB_VIA) and track.GetLayer() not in (pcb.F_Cu, pcb.B_Cu):
            board.Remove(track)
            track.thisown = False
            removed += 1
    for zone in list(board.Zones()):
        layers = zone.GetLayerSet()
        layers.RemoveLayer(pcb.In1_Cu)
        layers.RemoveLayer(pcb.In2_Cu)
        if len(list(layers.Seq())) == 0:
            board.Remove(zone)
            zone.thisown = False
        else:
            zone.SetLayerSetAndRemoveUnusedFills(layers)
            zone.UnFill()
    board.SetCopperLayerCount(2)
    layers = board.GetEnabledLayers()
    layers.RemoveLayer(pcb.In1_Cu)
    layers.RemoveLayer(pcb.In2_Cu)
    board.SetEnabledLayers(layers)
    board.GetDesignSettings().m_HasStackup = False
    assert signature(board) == before
    output = folder/(name+'.kicad_pcb')
    pcb.SaveBoard(str(output), board)
    # Remove stale four-layer stack entries. KiCad creates a default two-layer
    # stack on next load; impedance must be re-designed for the selected build.
    text = output.read_text()
    text = re.sub(r'^\t\t\(stackup\n.*?^\t\t\)\n', '', text, flags=re.M|re.S)
    output.write_text(text, encoding='utf-8')
    board = pcb.LoadBoard(str(output))
    board.BuildConnectivity()
    pcb.ZONE_FILLER(board).Fill(board.Zones())
    pcb.SaveBoard(str(output), board)
    scratch = ROOT/'build/two-layer'/name
    scratch.mkdir(parents=True, exist_ok=True)
    assert pcb.ExportSpecctraDSN(board, str(scratch/(name+'.dsn')))
    return {'source': str(original.relative_to(ROOT)),
            'source_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
            'components': before, 'removed_inner_segments': removed,
            'layer_count': board.GetCopperLayerCount()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--board', choices=list(SOURCES))
    args = parser.parse_args()
    evidence = DEST/'baseline.json'
    result = json.loads(evidence.read_text()) if evidence.exists() else {}
    for name in ([args.board] if args.board else SOURCES):
        result[name] = create(name)
        print(name, result[name]['removed_inner_segments'], 'internal segments to reroute', flush=True)
    evidence.write_text(json.dumps(result, indent=2)+'\n')
