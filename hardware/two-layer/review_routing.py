"""Inventory saved routing for layout review; not a timing or impedance model.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib
import json
from collections import defaultdict
import pcbnew as p
from prepare import DEST, SOURCES


def main():
    result = {}
    for name in SOURCES:
        path = DEST/name.lower()/(name+'.kicad_pcb')
        board = p.LoadBoard(str(path))
        nets = defaultdict(lambda: {'length_mm': 0, 'vias': 0, 'widths_mm': set(),
                                    'layers': set()})
        for track in board.GetTracks():
            net = nets[track.GetNetname()]
            if isinstance(track, p.PCB_VIA):
                net['vias'] += 1
            else:
                net['length_mm'] += p.ToMM(track.GetLength())
                net['widths_mm'].add(round(p.ToMM(track.GetWidth()), 6))
                net['layers'].add(board.GetLayerName(track.GetLayer()))
        for net in nets.values():
            net['length_mm'] = round(net['length_mm'], 4)
            net['widths_mm'] = sorted(net['widths_mm'])
            net['layers'] = sorted(net['layers'])
        result[name] = {
            'variant_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'longest_nets': sorted(nets, key=lambda n: nets[n]['length_mm'], reverse=True)[:10],
            'nets': dict(sorted(nets.items())),
        }
    output = {
        'interpretation': 'Length is total routed copper per net, including branches; '
            'it is not endpoint path length, delay, or a signal-integrity pass. '
            'Via count includes all vias on the net. Width inventory is not a current rating.',
        'boards': result,
    }
    (DEST/'review/routing.json').write_text(json.dumps(output, indent=2)+'\n')
    for name, board in result.items():
        print(name, [(net, board['nets'][net]['length_mm']) for net in board['longest_nets']])


if __name__ == '__main__':
    main()
