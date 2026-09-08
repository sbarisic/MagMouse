# SPDX-License-Identifier: GPL-3.0-or-later
"""Export PCB placement views and native DRC; never change the editable board."""

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kicad-cli', help='Path to KiCad 10 kicad-cli executable')
    parser.add_argument('--require-routed', action='store_true',
                        help='Also fail when there are unconnected items')
    args = parser.parse_args()
    cli = args.kicad_cli or shutil.which('kicad-cli')
    if not cli:
        for base in [Path(os.environ.get('LOCALAPPDATA', '.')) / 'Programs',
                     Path(os.environ.get('ProgramFiles', '.'))]:
            candidate = base / 'KiCad/10.0/bin/kicad-cli.exe'
            if candidate.is_file():
                cli = str(candidate)
                break
    if not cli:
        parser.error('KiCad CLI not found; supply --kicad-cli PATH')

    project = Path(__file__).resolve().parent
    board = project / 'MagMouse.kicad_pcb'
    out = project.parents[1] / 'build/pcb-review'
    out.mkdir(parents=True, exist_ok=True)
    commands = [
        ['pcb', 'drc', '--format', 'json', '--schematic-parity',
         '--output', str(out / 'drc.json'), str(board)],
    ]
    for side in ['F', 'B']:
        commands.append([
            'pcb', 'export', 'svg', '--mode-single', '--page-size-mode', '2',
            '--exclude-drawing-sheet', '--layers',
            f'{side}.Cu,{side}.Fab,{side}.Silkscreen,Edge.Cuts,Dwgs.User',
            '--output', str(out / f'placement-{side}.svg'), str(board),
        ])
    # Board-area crops omit the intentionally off-board wheel staging area.
    commands.append([
        'pcb', 'export', 'svg', '--mode-single', '--page-size-mode', '1',
        '--exclude-drawing-sheet', '--layers', 'F.Cu,F.Fab,F.Silkscreen,Edge.Cuts,Dwgs.User',
        '--output', str(out / 'placement-with-staging.svg'), str(board),
    ])
    for command in commands:
        subprocess.run([cli, *command], check=True)

    report = json.loads((out / 'drc.json').read_text(encoding='utf-8'))
    violations = report['violations']
    parity = report['schematic_parity']
    unconnected = report['unconnected_items']
    summary = {
        'status': 'PLACEMENT REVIEW ONLY - NOT FABRICATION APPROVAL',
        'kicad_version': report['kicad_version'],
        'board_sha256': hashlib.sha256(board.read_bytes()).hexdigest(),
        'physical_drc_violations': len(violations),
        'physical_drc_types': dict(Counter(v['type'] for v in violations)),
        'schematic_parity_issues': len(parity),
        'unconnected_items': len(unconnected),
        'ignored_checks': report.get('ignored_checks', []),
        'placement_checks_pass': not violations and not parity,
        'routing_complete': not unconnected,
        'placement_scope': 'Original motherboard placement plus off-board wheel staging; enclosure fit is unverified',
    }
    (out / 'review-status.json').write_text(
        json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))
    print(f'PCB review exports: {out}')
    return 2 if violations or parity or (args.require_routed and unconnected) else 0


if __name__ == '__main__':
    raise SystemExit(main())
