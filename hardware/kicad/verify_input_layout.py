# SPDX-License-Identifier: GPL-3.0-or-later
"""Check the routed input-power subset with KiCad's native copper connectivity.

Run with KiCad's Python. Pair this check with physical DRC and schematic parity.
This does not establish current capacity, USB compliance or thermal acceptance.
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

    connected(('U12', '5'), [('J1', 'A4'), ('J1', 'B4'), ('C24', '1'),
                             ('D1', '1'), ('R29', '1'), ('R31', '1')], 'VBUS_USB')
    connected(('U12', '6'), [('C88', '1'), ('C1', '1'), ('U2', '2'), ('U2', '3')], 'PWR_5V')
    connected(('U12', '8'), [('C24', '2'), ('C88', '2'), ('C25', '2'), ('D1', '2'),
                             ('J1', 'A1'), ('J1', 'B1'), ('U2', '9'),
                             ('R30', '2'), ('R35', '2'), ('R58', '2'),
                             ('Q1', '2'), ('Q2', '2'), ('R62', '2'), ('R63', '2'),
                             ('U14', '2'), ('C32', '2')], 'GND')
    connected(('U12', '1'), [('R29', '2'), ('R30', '1')], 'USB_UVLO')
    connected(('U12', '2'), [('R34', '2'), ('R35', '1')], 'USB_OVLO')
    for index, net in enumerate(['USB_OV_1', 'USB_OV_2', 'USB_OV_3'], 31):
        connected((f'R{index}', '2'), [(f'R{index + 1}', '1')], net)
    connected(('U12', '7'), [('C25', '1')], 'USB_DVDT')
    connected(('U12', '4'), [('R44', '1')], 'USB_FAULT_N')
    connected(('U12', '9'), [('R56', '1'), ('R59', '1'), ('R60', '1'), ('R61', '1')], 'USB_ILM')
    connected(('R56', '2'), [('R57', '1')], 'ILM_BASE_1')
    connected(('R57', '2'), [('R58', '1')], 'ILM_BASE_2')
    connected(('R59', '2'), [('Q1', '3')], 'ILM_MED_D')
    connected(('R60', '2'), [('R61', '2'), ('Q2', '3')], 'ILM_HIGH_D')
    connected(('U14', '6'), [('Q1', '1'), ('R62', '1'), ('U16', '1'), ('U16', '9')], 'SOURCE_OK')
    connected(('U16', '8'), [('Q2', '1'), ('R63', '1')], 'SOURCE_3A')
    connected(('U14', '4'), [('U16', '10')], 'CC_OUT2_INV')
    connected(('U11', '7'), [('R26', '2'), ('U14', '1')], 'CC_OUT1')
    connected(('U11', '8'), [('R27', '2'), ('U14', '3')], 'CC_OUT2')
    connected(('U14', '5'), [('C32', '1')], '+3V3')
    connected(('J1', 'A5'), [('U20', '1'), ('U11', '1')], 'USB_CC1')
    connected(('J1', 'B5'), [('U20', '2'), ('U11', '2')], 'USB_CC2')
    connected(('U12', '5'), [('R25', '1')], 'VBUS_USB')
    connected(('R25', '2'), [('U11', '4')], 'CC_VBUS_DET')
    connected(('U2', '6'), [('U11', '12'), ('C22', '1'), ('R26', '1'), ('R27', '1'),
                            ('U14', '5'), ('C32', '1'), ('U16', '14'), ('C29', '1')], '+3V3')
    connected(('U12', '8'), [('U20', '3'), ('U11', '3'), ('U11', '10'), ('U11', '11'),
                            ('C22', '2'), ('U16', '7'), ('C29', '2')], 'GND')

    if ('C88', '1') in pads and ('U12', '6') in pads:
        distance = pcb.ToMM((pads['C88', '1'].GetPosition() -
                             pads['U12', '6'].GetPosition()).EuclideanNorm())
        if distance > 5:
            errors.append('C88 must remain within the 5 mm local output-bypass placement budget')
    if ('U12', '8') in pads:
        items = connectivity.GetConnectedItems(pads['U12', '8'])
        if not any(i.GetClass() == 'ZONE' and i.GetLayer() == pcb.In1_Cu for i in items):
            errors.append('U12 ground must reach the filled In1 reference plane')

    return {
        'scope': 'USB/U12/buck feed, local protection, Type-C detector and source-selection supply/copper; '
                 'MCU interfaces, remaining distribution, telemetry and other board routing remain open',
        'native_unconnected_connections': connectivity.GetUnconnectedCount(False),
        'errors': errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, default=ROOT / 'hardware/kicad/MagMouse.kicad_pcb')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/pcb-review/input-layout-checks.json')
    args = parser.parse_args()
    report = verify(pcb.LoadBoard(str(args.board.resolve())))
    report['board_sha256'] = hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return int(bool(report['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
