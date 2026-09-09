# SPDX-License-Identifier: GPL-3.0-or-later
"""Check the routed buck subcircuit using KiCad's native copper connectivity.

Run with KiCad's bundled Python (pcbnew is required). This is a local layout
check, not a full-board routing, thermal, EMI or regulator-stability assessment.
"""

import argparse
import hashlib
import json
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[2]


def verify(board):
    board.BuildConnectivity()
    connectivity = board.GetConnectivity()
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    pads = {(ref, pad.GetNumber()): pad
            for ref, footprint in footprints.items() for pad in footprint.Pads()
            if pad.GetNumber()}
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    def connected(anchor, targets, net):
        start = pads.get(anchor)
        if start is None:
            errors.append(f'Missing pad {anchor}')
            return
        check(start.GetNetname() == net, f'{anchor}: expected {net}')
        # GetConnectedPads only reports direct contacts. GetConnectedItems walks
        # the complete copper cluster, including tracks, vias and filled zones.
        items = list(connectivity.GetConnectedItems(start)) + [start]
        ids = {item.m_Uuid.AsString() for item in items}
        for target in targets:
            pad = pads.get(target)
            check(pad is not None and pad.GetNetname() == net and
                  pad.m_Uuid.AsString() in ids,
                  f'{anchor} must reach {target} through copper on {net}')

    connected(('U2', '2'), [('U2', '3'), ('C1', '1')], 'PWR_5V')
    connected(('U2', '7'), [('L1', '1')], 'BUCK_SW')
    connected(('U2', '6'), [('L1', '2'), ('C2', '1'), ('C3', '1'), ('C23', '1')], '+3V3')
    connected(('U2', '9'), [('U2', '1'), ('U2', '4'), ('U2', '5'),
                            ('C1', '2'), ('C2', '2'), ('C3', '2'), ('C23', '2')], 'GND')
    connected(('U2', '8'), [('R28', '1')], 'LOGIC_PG')

    switch_items = [t for t in board.GetTracks() if t.GetNetname() == 'BUCK_SW']
    switch_length = sum(pcb.ToMM(t.GetLength()) for t in switch_items if not isinstance(t, pcb.PCB_VIA))
    check(bool(switch_items) and all(not isinstance(t, pcb.PCB_VIA) and t.GetLayer() == pcb.F_Cu
                                   for t in switch_items),
          'BUCK_SW must stay on front copper without vias')
    check(switch_length <= 5.0, 'BUCK_SW exceeds the 5 mm local layout review budget')

    exposed_pad = pads.get(('U2', '9'))
    if exposed_pad is not None:
        items = list(connectivity.GetConnectedItems(exposed_pad))
        check(any(item.GetClass() == 'ZONE' and item.GetLayer() == pcb.In1_Cu for item in items),
              'U2 exposed-pad return must reach filled In1 ground copper')
        local_vias = [item for item in items if item.GetClass() == 'PCB_VIA' and
                      pcb.ToMM((item.GetPosition() - exposed_pad.GetPosition()).EuclideanNorm()) < 2.0]
        check(len(local_vias) >= 2, 'U2 requires at least two nearby ground vias outside its solder land')
        for via in local_vias:
            check(not exposed_pad.HitTest(via.GetPosition()),
                  'Ground via in U2 exposed solder land requires a separate assembly review')

    return {
        'scope': 'Local buck copper only; input feed, distribution, full-board routing and hardware acceptance remain open',
        'switch_track_length_mm': round(switch_length, 3),
        'native_unconnected_connections': connectivity.GetUnconnectedCount(False),
        'errors': errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, default=ROOT / 'hardware/kicad/MagMouse.kicad_pcb')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/pcb-review/buck-layout-checks.json')
    args = parser.parse_args()
    report = verify(pcb.LoadBoard(str(args.board.resolve())))
    report['board_sha256'] = hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return int(bool(report['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
