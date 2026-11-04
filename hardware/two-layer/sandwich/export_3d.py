"""Export CAD/viewer models without modifying the routed PCB sources.
Run with KiCad 10 Python. SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pcbnew as p
from export_quote import BOARDS
from route_main import HERE, ROOT, CLI

OUT = HERE / '3d'
LOGS = ROOT / 'build/sandwich/3d'
LIBRARY = CLI.parent.parent / 'share/kicad/3dmodels'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(name, args):
    result = subprocess.run([str(CLI), *map(str, args)], capture_output=True, text=True)
    (LOGS / (name + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'{name}: see {LOGS / (name + ".log")}')


def main(names=None):
    OUT.mkdir(exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    sources = {**BOARDS, 'Panel': HERE / 'panel/Panel.kicad_pcb'}
    report = {}
    if names:
        unknown = set(names) - set(sources)
        if unknown:
            raise ValueError('Unknown boards: ' + ', '.join(sorted(unknown)))
        sources = {name: sources[name] for name in names}
        if (OUT / 'manifest.json').exists():
            report = json.loads((OUT / 'manifest.json').read_text())
    for name, source in sources.items():
        before = sha(source)
        board = p.LoadBoard(str(source))
        missing, absent, available = [], [], []
        for footprint in board.GetFootprints():
            if footprint.IsDNP():
                continue
            models = list(footprint.Models())
            entry = {'reference': footprint.GetReference(), 'value': footprint.GetValue()}
            if not models:
                if not footprint.IsExcludedFromBOM():
                    absent.append(entry)
                continue
            for model in models:
                filename = model.m_Filename.replace('${KICAD10_3DMODEL_DIR}', str(LIBRARY))
                filename = filename.replace('${KIPRJMOD}', str(source.parent))
                if Path(os.path.expandvars(filename)).is_file():
                    available.append(footprint.GetReference())
                else:
                    missing.append({**entry, 'model': model.m_Filename})
        common = ['--force', '--subst-models', '--no-dnp', '--include-pads',
                  '--cut-vias-in-body', '-D', 'KICAD10_3DMODEL_DIR=' + str(LIBRARY)]
        for fmt in ('step', 'glb'):
            extra = ['--include-soldermask', '--include-silkscreen'] if fmt == 'glb' else []
            run(name + '-' + fmt, ['pcb', 'export', fmt, *common, *extra,
                                   '-o', OUT / (name + '.' + fmt), source])
        # Complete mechanical substrate even when a component has no 3D body.
        run(name + '-bare-step', ['pcb', 'export', 'step', '--force', '--board-only',
                                 '--cut-vias-in-body', '-o', OUT / (name + '-bare.step'), source])
        run(name + '-render', ['pcb', 'render', '--width', '1600', '--height', '1000',
                              '--rotate', '35,0,20', '--quality', 'high', '--background',
                              'opaque', '--floor', '-o', OUT / (name + '-preview.png'), source])
        assert sha(source) == before, '3D exporter changed PCB source'
        report[name] = {
            'source': source.relative_to(ROOT).as_posix(), 'source_sha256': before,
            'configured_board_thickness_mm': p.ToMM(board.GetDesignSettings().GetBoardThickness()),
            'exported_substrate_expected_mm': p.ToMM(board.GetDesignSettings().GetBoardThickness()) - .09,
            'available_model_instances': len(available),
            'unmodeled_footprints': absent, 'missing_model_files': missing,
            'source_unchanged': True,
            'glb_contour_warning': 'Wire self-interference check failed' in (LOGS / (name + '-glb.log')).read_text(),
            'exports': {f.name: sha(f) for f in sorted(OUT.glob(name + '*')) if f.is_file()},
        }
        print(name, 'exported;', len(available), 'model instances;', len(missing), 'missing files', flush=True)
    (OUT / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main(sys.argv[1:] or None)
