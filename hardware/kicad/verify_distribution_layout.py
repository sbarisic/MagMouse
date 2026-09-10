# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify actuator distribution, current paths and interlocks on saved copper.

Run with KiCad's Python, alongside physical DRC. Connectivity and local geometry
checks do not qualify current capacity, noise, timing or thermal performance.
"""

import argparse
import hashlib
import json
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[2]
NETS = {
    'ACT_5V', 'ACT_VMON', 'ACT_UVLO', 'ACT_OVLO', 'DRV_AVDD', 'BRAKE_DRAIN', 'BRAKE_GATE',
    'BRAKE_OUT', 'BRAKE_REF', 'BRAKE_DIV_TOP', 'BRAKE_FB_1', 'BRAKE_FB_2',
    'BRAKE_SENSE', 'WHEEL_CP', 'WHEEL_CPH', 'WHEEL_CPL', 'WHEEL_BUCK_SW',
    'WHEEL_BUCK_OUT', 'WD_CEXT', 'WD_RCEXT', 'ADC_DECAP', 'ADC2_DECAP', 'ARM_SOURCE', 'ARM_VALID',
    'ACT_PERMIT', 'ACT_REQ', 'ACT_HEARTBEAT', 'ACT_DRIVE_EN', 'SENS_REQ',
    'HALL_EN', 'WHEEL_RUN_REQ', 'WHEEL_RUN_EN', 'WHEEL_DRVOFF',
    'DRV_FAULT_LOCAL_N', 'DRV_FAULT_N', 'CC_OUT1', 'CC_OUT2',
    'VBUS_GATE', 'VBUS_PRESENT_N',
    'SOURCE_OK', 'SOURCE_3A', 'CC_OUT2_INV', 'ACT_FAULT_N', 'USB_FAULT_N', 'MCU_EN',
}
for phase in 'ABC':
    NETS.update({'WHEEL_PHASE_' + phase, 'WHEEL_PWM_' + phase,
                 'DRV_INH' + phase, 'WHEEL_SO' + phase, 'WHEEL_I_' + phase})
for button in 'LMR':
    NETS.update('BTN_' + button + '_' + suffix for suffix in
                ['COIL_P', 'COIL_N', 'VREF', 'ISENSE', 'CMD1', 'CMD2', 'IN1', 'IN2'])

SUPPLY_REFS = {f'U{i}' for i in
               [3, 4, 5, 6, 7, 8, 9, 10, 15, 16, 17, 18, 21, 22, 23, 24, 25, 26, 30, 31]}
SUPPLY_REFS |= {f'C{i}' for lo, hi in [(4, 22), (27, 32), (37, 62), (65, 70)]
                for i in range(lo, hi)}
SUPPLY_REFS |= {f'R{i}' for lo, hi in [(3, 25), (46, 56), (67, 71), (81, 125)]
                for i in range(lo, hi)}
SUPPLY_REFS |= {'D2', 'D4', 'Q4', 'Q5'}


def verify(board):
    board.BuildConnectivity()
    conn = board.GetConnectivity()
    pad_entries = [((f.GetReference(), p.GetNumber()), p) for f in board.GetFootprints()
                   for p in f.Pads() if p.GetNumber()]
    pads = dict(pad_entries)
    errors, checked = [], {}

    def items(pad):
        return {i.m_Uuid.AsString() for i in conn.GetConnectedItems(pad)} | {pad.m_Uuid.AsString()}

    for net in sorted(NETS):
        pins = [(key, p) for key, p in pad_entries if p.GetNetname() == net]
        if len(pins) < 2:
            errors.append(f'{net}: expected at least two physical pads')
            continue
        reached = items(pins[0][1])
        for key, pad in pins[1:]:
            if pad.m_Uuid.AsString() not in reached:
                errors.append(f'{net}: {pins[0][0]} does not reach {key} through copper')
        checked[net] = len(pins)

    supply_anchor = pads.get(('U2', '6'))
    supply_ids = items(supply_anchor) if supply_anchor else set()
    planes = {z.m_Uuid.AsString() for z in board.Zones()
              if z.GetNetname() == 'GND' and z.GetLayer() == pcb.In1_Cu}
    if not planes:
        errors.append('Missing In1.Cu GND reference zone')
    ground_count = supply_count = 0
    for key, pad in pad_entries:
        if key[0] not in SUPPLY_REFS:
            continue
        if pad.GetNetname() == '+3V3':
            supply_count += 1
            if pad.m_Uuid.AsString() not in supply_ids:
                errors.append(f'+3V3: protected buck output does not reach {key}')
        if pad.GetNetname() == 'GND':
            ground_count += 1
            if not items(pad) & planes:
                errors.append(f'GND: {key} has no copper return to In1.Cu')

    # Keep short local timing/pump/feedback nets on the component side.
    front_only = {'WHEEL_CP', 'WHEEL_CPH', 'WHEEL_CPL', 'WHEEL_BUCK_SW',
                  'WHEEL_BUCK_OUT', 'WD_CEXT', 'WD_RCEXT', 'BRAKE_DIV_TOP',
                  'BRAKE_FB_1', 'BRAKE_FB_2', 'BRAKE_SENSE'}
    lengths = {}
    for net in sorted(front_only):
        tracks = [t for t in board.GetTracks() if t.GetNetname() == net]
        lengths[net] = round(sum(pcb.ToMM(t.GetLength()) for t in tracks
                                 if not isinstance(t, pcb.PCB_VIA)), 3)
        if any(isinstance(t, pcb.PCB_VIA) or t.GetLayer() != pcb.F_Cu for t in tracks):
            errors.append(f'{net}: local loop must stay on F.Cu without vias')

    thermal_vias = {}
    for ref, ep, radius in [('U4', '9', 2), ('U5', '9', 2), ('U6', '9', 2), ('U21', '41', 5)]:
        pad = pads.get((ref, ep))
        if pad is None:
            errors.append(f'Missing {ref} exposed ground pad')
            continue
        reached = items(pad)
        nearby = [t for t in board.GetTracks() if isinstance(t, pcb.PCB_VIA)
                  and t.GetNetname() == 'GND' and t.m_Uuid.AsString() in reached
                  and pcb.ToMM((t.GetPosition() - pad.GetPosition()).EuclideanNorm()) <= radius]
        thermal_vias[ref] = len(nearby)
        if len(nearby) < 4:
            errors.append(f'{ref}: fewer than four connected local thermal return vias')

    # U21 uses filled/capped vias inside its exposed pad. Nearby decoupling
    # returns alone do not establish the intended direct thermal connection.
    ep = pads.get(('U21', '41'))
    direct_thermal = 0
    if ep is not None:
        reached = items(ep)
        direct_thermal = sum(1 for t in board.GetTracks()
                             if isinstance(t, pcb.PCB_VIA) and t.GetNetname() == 'GND'
                             and t.m_Uuid.AsString() in reached
                             and ep.GetBoundingBox().Contains(t.GetPosition()))
    if direct_thermal < 4:
        errors.append('U21: fewer than four direct exposed-pad thermal vias')

    return {'scope': 'Actuator supply, driver/brake current paths, current sensing and interlock copper',
            'checked_net_pad_counts': checked, 'checked_supply_pads': supply_count,
            'checked_ground_pads': ground_count, 'local_front_track_lengths_mm': lengths,
            'local_ground_via_counts': thermal_vias,
            'u21_exposed_pad_vias_requiring_fill_and_cap': direct_thermal,
            'native_unconnected_connections': conn.GetUnconnectedCount(False), 'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, default=ROOT / 'hardware/kicad/MagMouse.kicad_pcb')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/pcb-review/distribution-layout-checks.json')
    args = parser.parse_args()
    report = verify(pcb.LoadBoard(str(args.board.resolve())))
    report['board_sha256'] = hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return int(bool(report['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
