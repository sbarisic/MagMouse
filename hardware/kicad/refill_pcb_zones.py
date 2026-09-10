# SPDX-License-Identifier: GPL-3.0-or-later
"""Refill saved copper using the board's own KiCad project and custom rules.

Run with KiCad Python, then run native DRC and saved-copper checks. Loading a
scratch PCB without its matching project can silently use default netclasses.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

import pcbnew as pcb


def assignments(board):
    items = list(board.GetTracks())
    items += [pad for fp in board.GetFootprints() for pad in fp.Pads()]
    return {item.m_Uuid.AsString(): item.GetNetname() for item in items}


def refill(path):
    path = Path(path).resolve()
    project = path.with_suffix('.kicad_pro')
    rules = path.with_suffix('.kicad_dru')
    if not project.is_file() or not rules.is_file():
        raise ValueError('Refill requires the matching .kicad_pro and .kicad_dru beside the PCB')
    project_bytes = project.read_bytes()
    rule_bytes = rules.read_bytes()
    settings = json.loads(project_bytes)['board']['design_settings']['rules']
    board = pcb.LoadBoard(str(path))
    loaded = board.GetDesignSettings()
    for key, value in [('min_clearance', loaded.m_MinClearance),
                       ('min_track_width', loaded.m_TrackMinWidth)]:
        if abs(pcb.ToMM(value) - settings[key]) > .000001:
            raise ValueError('KiCad did not load the project rule: ' + key)
    before = assignments(board)
    source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    board.BuildConnectivity()
    if assignments(board) != before:
        raise ValueError('Connectivity changed a copper or pad net; repair shorts before refilling')
    unconnected = board.GetConnectivity().GetUnconnectedCount(False)
    pcb.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    if assignments(board) != before:
        raise ValueError('Zone filling changed a copper or pad net; board was not saved')
    try:
        with tempfile.TemporaryDirectory(prefix='magmouse-fill-') as folder:
            staged = Path(folder) / path.name
            pcb.SaveBoard(str(staged), board)
            # Keep the replacement on the destination filesystem for atomicity.
            with tempfile.NamedTemporaryFile(dir=path.parent, suffix='.fill', delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(staged.read_bytes())
            try:
                if hashlib.sha256(path.read_bytes()).hexdigest() != source_hash:
                    raise ValueError('PCB changed during refill; refusing to replace the newer file')
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
    finally:
        project.write_bytes(project_bytes)
        rules.write_bytes(rule_bytes)
    return {'source_sha256': source_hash,
            'board_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'project_sha256': hashlib.sha256(project_bytes).hexdigest(),
            'custom_rules_sha256': hashlib.sha256(rule_bytes).hexdigest(),
            'native_unconnected_before': unconnected,
            'native_unconnected_after': board.GetConnectivity().GetUnconnectedCount(False),
            'pad_and_track_net_assignments_preserved': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, default=Path(__file__).with_name('MagMouse.kicad_pcb'))
    args = parser.parse_args()
    print(json.dumps(refill(args.board), indent=2))


if __name__ == '__main__':
    main()
