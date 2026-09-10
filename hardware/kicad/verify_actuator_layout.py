# SPDX-License-Identifier: GPL-3.0-or-later
"""Check U13's routed local protection subset using KiCad copper connectivity.

Run with KiCad's Python and alongside physical DRC. Downstream actuator loads,
interlock input wiring and hardware acceptance are outside this check.
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
    pads = {(f.GetReference(), p.GetNumber()): p
            for f in board.GetFootprints() for p in f.Pads() if p.GetNumber()}
    errors = []

    def connected(anchor, targets, net):
        start = pads.get(anchor)
        if start is None:
            errors.append(f'Missing pad {anchor}')
            return
        ids = {item.m_Uuid.AsString() for item in connectivity.GetConnectedItems(start)}
        ids.add(start.m_Uuid.AsString())
        for target in [anchor, *targets]:
            pad = pads.get(target)
            if pad is None or pad.GetNetname() != net or pad.m_Uuid.AsString() not in ids:
                errors.append(f'{anchor} must reach {target} through copper on {net}')

    connected(('U12', '6'), [('U13', '5'), ('C89', '1'), ('R36', '1'), ('R40', '1')], 'PWR_5V')
    connected(('U13', '6'), [('C40', '1')], 'ACT_5V')
    connected(('U13', '8'), [('C89', '2'), ('C40', '2'), ('C26', '2'),
                            ('R39', '2'), ('R41', '2'), ('R42', '2'), ('R43', '2')], 'GND')
    connected(('R36', '2'), [('R37', '1')], 'ACT_UV_1')
    connected(('R37', '2'), [('R38', '1')], 'ACT_UV_2')
    connected(('U13', '1'), [('R38', '2'), ('R39', '1'), ('D3', '1')], 'ACT_UVLO')
    connected(('U13', '2'), [('R40', '2'), ('R41', '1')], 'ACT_OVLO')
    connected(('U13', '7'), [('C26', '1')], 'ACT_DVDT')
    connected(('U13', '9'), [('R42', '1'), ('R43', '1')], 'ACT_ILM')
    connected(('U13', '4'), [('R45', '1')], 'ACT_FAULT_N')
    connected(('U12', '4'), [('R44', '1')], 'USB_FAULT_N')
    connected(('U16', '11'), [('D3', '3'), ('R49', '1'), ('R84', '1'),
                             ('U17', '2'), ('U17', '5'), ('U17', '10'), ('U17', '13'),
                             ('U18', '2'), ('U18', '5'), ('U22', '1'),
                             ('U21', '23'), ('TP13', '1')], 'ACT_DRIVE_EN')
    connected(('U3', '45'), [('R28', '2'), ('R44', '2'), ('R45', '2'),
                            ('R3', '2'), ('C4', '1'), ('SW1', '1'),
                            ('U18', '10'), ('TP6', '1')], 'MCU_EN')
    connected(('U2', '6'), [('R3', '1')], '+3V3')
    connected(('U13', '8'), [('R49', '2'), ('R84', '2'), ('C4', '2'), ('SW1', '2')], 'GND')

    local_distances = {}
    for ref, pin in [('C89', '5'), ('C40', '6'), ('C26', '7')]:
        if (ref, '1') not in pads or ('U13', pin) not in pads:
            continue  # Missing parts are already reported by connectivity checks.
        distance = pcb.ToMM((pads[ref, '1'].GetPosition() - pads['U13', pin].GetPosition()).EuclideanNorm())
        local_distances[ref] = round(distance, 3)
        if distance > 5:
            errors.append(f'{ref} exceeds the 5 mm local placement review budget')
    ilm = [t for t in board.GetTracks() if t.GetNetname() == 'ACT_ILM']
    if not ilm or any(isinstance(t, pcb.PCB_VIA) or t.GetLayer() != pcb.F_Cu for t in ilm):
        errors.append('ACT_ILM must remain on front copper without vias')

    return {
        'scope': 'U13 local power/protection, enable fanout and fault/reset copper; '
                 'interlock inputs and distribution checked separately by verify_distribution_layout.py; hardware acceptance remains open',
        'local_pad_distances_mm': local_distances,
        'ilm_track_length_mm': round(sum(pcb.ToMM(t.GetLength()) for t in ilm
                                          if not isinstance(t, pcb.PCB_VIA)), 3),
        'native_unconnected_connections': connectivity.GetUnconnectedCount(False),
        'errors': errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, default=ROOT / 'hardware/kicad/MagMouse.kicad_pcb')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/pcb-review/actuator-layout-checks.json')
    args = parser.parse_args()
    report = verify(pcb.LoadBoard(str(args.board.resolve())))
    report['board_sha256'] = hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return int(bool(report['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
