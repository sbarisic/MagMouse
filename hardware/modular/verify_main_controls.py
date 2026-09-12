"""Verify source controls, main actuator distribution and interlocks in copper.

Use KiCad Python, with native DRC/parity alongside this audit. This checks the
main board up to its cable headers, not cable behavior or hardware acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import pcbnew as p

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'hardware/kicad'))
from verify_high_current_layout import CopperGraph, uid, filled_area_at, verify_stackup

NETS = {
    'USB_CC1', 'USB_CC2', 'CC_OUT1', 'CC_OUT2', 'CC_OUT2_INV', 'CC_VBUS_DET',
    'SOURCE_OK', 'SOURCE_3A', 'ACT_5V', 'ACT_UV_1', 'ACT_UV_2', 'ACT_UVLO',
    'ACT_OVLO', 'ACT_DVDT', 'ACT_ILM', 'MCU_EN', 'ARM_SOURCE', 'ARM_VALID',
    'ACT_PERMIT', 'ACT_REQ', 'ACT_HEARTBEAT', 'ACT_DRIVE_EN', 'SENS_REQ',
    'HALL_EN', 'WD_CEXT', 'WD_RCEXT', 'VBUS_GATE', 'VBUS_PRESENT_N',
    'USB_FAULT_N', 'ACT_FAULT_N', 'WHEEL_RUN_REQ', 'DRV_FAULT_N', 'DRV_FAULT_LOCAL_N',
}
NETS |= {f'BTN_{button}_{suffix}' for button in 'LMR'
         for suffix in ['CMD1', 'CMD2', 'IN1', 'IN2', 'COIL_P', 'COIL_N']}
GROUND_REFS = {'J8', 'J10', 'U3', 'U4', 'U5', 'U6', 'U11', 'U12', 'U13', 'U14',
               'U15', 'U16', 'U17', 'U18', 'U19', 'U20', 'U25', 'Q1', 'Q2', 'Q3', 'D2', 'D4'}
GROUND_REFS |= {f'C{i}' for i in [4,5,6,7,8,10,11,13,14,22,24,25,26,27,28,29,30,31,32,34,35,36,37,38,39,40,53,88,89]}
GROUND_REFS |= {f'R{i}' for i in [8,9,14,15,20,21,29,30,35,38,39,41,42,43,49,50,51,52,53,54,55,58,62,63,66,68,69,70,71,77,99,101,141,142,143]}
SUPPLY_REFS = {'J8', 'U3', 'U11', 'U14', 'U15', 'U16', 'U17', 'U18', 'U19', 'U25',
               'C4', 'C5', 'C6', 'C22', 'C27', 'C28', 'C29', 'C30', 'C31', 'C32', 'C34', 'C35', 'C53',
               'R3', 'R26', 'R27', 'R46', 'R53', 'R55', 'R70', 'R71'}
POWER_PATHS = [(('U12', '6'), ('U13', '5'), 50)]
POWER_PATHS += [(('U13', '6'), (ref, '5'), 85) for ref in ['U4', 'U5', 'U6']]
POWER_PATHS += [(('U13', '6'), ('J10', '1'), 50)]
for driver, connector in [('U4', 'J2'), ('U5', 'J3'), ('U6', 'J4')]:
    POWER_PATHS += [((driver, '6'), (connector, '1'), 25), ((driver, '8'), (connector, '2'), 25)]


def verify(board):
    copper = list(board.GetTracks())
    pad_entries = [((f.GetReference(), q.GetNumber()), q) for f in board.GetFootprints() for q in f.Pads() if q.GetNumber()]
    original = {uid(q): q.GetNetname() for q in copper + [q for _, q in pad_entries]}
    board.BuildConnectivity(); conn = board.GetConnectivity(); errors = []
    if any(original[uid(q)] != q.GetNetname() for q in copper + [q for _, q in pad_entries]):
        errors.append('Native connectivity changed a copper/pad net assignment; inspect for a short')
    pads = dict(pad_entries)
    def reached(q): return {uid(i) for i in conn.GetConnectedItems(q)} | {uid(q)}
    metrics = {}
    for net in sorted(NETS):
        nodes = [(key, q) for key, q in pad_entries if q.GetNetname() == net]
        if len(nodes) < 2:
            errors.append(net + ': missing endpoints'); continue
        connected = reached(nodes[0][1])
        for key, q in nodes[1:]:
            if uid(q) not in connected: errors.append(f'{net}: disconnected {key}')
        tracks = [t for t in copper if t.GetNetname() == net]
        metrics[net] = {'pads': len(nodes), 'track_mm': round(sum(p.ToMM(t.GetLength()) for t in tracks if not isinstance(t, p.PCB_VIA)), 3),
                        'vias': sum(isinstance(t, p.PCB_VIA) for t in tracks)}
        if net in {'ACT_ILM', 'ACT_DVDT', 'WD_CEXT', 'WD_RCEXT'} and any(isinstance(t, p.PCB_VIA) or t.GetLayer() != p.F_Cu for t in tracks):
            errors.append(net + ': local loop must stay front-only without vias')
    def connected(anchor, targets, net):
        ids = reached(pads[anchor])
        for key in [anchor, *targets]:
            if pads[key].GetNetname() != net or uid(pads[key]) not in ids: errors.append(f'{net}: disconnected {key}')
    connected(('U12', '6'), [('U13', '5'), ('C89', '1'), ('R36', '1'), ('R40', '1')], 'PWR_5V')
    connected(('U12', '5'), [('R25', '1'), ('R65', '1')], 'VBUS_USB')
    power = reached(pads['U2', '6']); ground_ids = set(); ground = p.SHAPE_POLY_SET()
    for z in board.Zones():
        if z.GetLayer() == p.In1_Cu and z.GetNetname() == 'GND' and not z.GetIsRuleArea():
            ground_ids.add(uid(z)); ground.BooleanAdd(z.GetFilledPolysList(p.In1_Cu))
    if ground.OutlineCount() != 1: errors.append('In1 must have one connected saved ground outline')
    if any(t.GetLayer() == p.In1_Cu for t in copper if not isinstance(t, p.PCB_VIA)): errors.append('A track occupies In1 reference copper')
    ground_count = supply_count = 0
    for key, q in pad_entries:
        if key[0] in GROUND_REFS and q.GetNetname() == 'GND':
            ground_count += 1
            if not reached(q) & ground_ids: errors.append(f'GND: disconnected {key}')
        if key[0] in SUPPLY_REFS and q.GetNetname() == '+3V3':
            supply_count += 1
            if uid(q) not in power: errors.append(f'+3V3: disconnected {key}')
    graph = CopperGraph(board); paths = []
    for start, end, limit in POWER_PATHS:
        label = '.'.join(start) + ' -> ' + '.'.join(end)
        found = graph.path(uid(graph.pads[start]), uid(graph.pads[end]))
        if found is None:
            errors.append(label + ': missing power copper path'); continue
        resistance, route = found
        paths.append({'path': label, 'screening_milliohms': round(resistance * 1000, 3), 'budget_milliohms': limit})
        if resistance * 1000 > limit: errors.append(label + ': exceeds copper resistance regression ceiling')
    transitions = {}
    for key in [('C40', '1'), ('J10', '1'), ('J10', '2')]:
        pad = pads[key]; origin = pad.GetPosition()
        allowed = {k for k, q in graph.items.items() if q.GetNetname() == pad.GetNetname() and q.IsOnLayer(p.F_Cu)
                   and p.ToMM((q.GetPosition() - origin).EuclideanNorm()) <= 3
                   and (not isinstance(q, p.PCB_TRACK) or p.ToMM((q.GetEnd() - origin).EuclideanNorm()) <= 3)}
        vias = [t for k, t in graph.items.items() if isinstance(t, p.PCB_VIA) and k in allowed
                and p.ToMM(t.GetWidth(p.F_Cu)) >= .599 and p.ToMM(t.GetDrillValue()) >= .299
                and graph.path(uid(pad), k, allowed)]
        label = '.'.join(key)
        transitions[label] = len(vias)
        # A 1.1 mm plated wire hole has more barrel circumference than the
        # former three 0.3 mm vias. It directly joins the outer-layer lands.
        wire_barrel = (key[0]=='J10' and pad.GetAttribute()==p.PAD_ATTRIB_PTH
                       and p.ToMM(pad.GetDrillSize().x)>=1.099
                       and pad.IsOnLayer(p.F_Cu) and pad.IsOnLayer(p.B_Cu))
        if not wire_barrel and len(vias) < 3:
            errors.append(label + ': fewer than three local power-transition vias')
    spreading = {}
    for ref, front_min, back_min in [('U4', 20, 10), ('U5', 17, 10), ('U6', 35, 20)]:
        pad = pads[ref, '9']; origin = pad.GetPosition()
        allowed = {k for k, q in graph.items.items() if q.GetNetname() == 'GND' and q.IsOnLayer(p.F_Cu)
                   and p.ToMM((q.GetPosition() - origin).EuclideanNorm()) <= 2
                   and (not isinstance(q, p.PCB_TRACK) or p.ToMM((q.GetEnd() - origin).EuclideanNorm()) <= 2)}
        vias = [t for k, t in graph.items.items() if isinstance(t, p.PCB_VIA) and k in allowed and graph.path(uid(pad), k, allowed)]
        result = {'local_front_connected_vias': len(vias)}
        if len(vias) < 4: errors.append(ref + ': fewer than four local thermal vias')
        for layer, minimum in [(p.F_Cu, front_min), (p.B_Cu, back_min)]:
            name = 'ACTUATOR_' + ref + '_GND_' + board.GetLayerName(layer)
            zones = [z for z in board.Zones() if z.GetZoneName() == name and not z.GetIsRuleArea()]
            if len(zones) != 1:
                errors.append(name + ': missing ground spreader'); continue
            z = zones[0]
            if z.GetNetname() != 'GND' or z.GetLayer() != layer or z.GetPadConnection() != p.ZONE_CONNECTION_FULL:
                errors.append(name + ': incorrect layer/net or pad connection')
            area = filled_area_at(z, [origin] if layer == p.F_Cu else [v.GetPosition() for v in vias])
            result[board.GetLayerName(layer) + '_filled_mm2'] = round(area, 3)
            if area < minimum: errors.append(name + ': insufficient local ground copper')
        spreading[ref] = result
    return {'scope': 'Type-C/source controls, main actuator distribution and interlocks to cable headers',
            'nets': metrics, 'checked_ground_pads': ground_count, 'checked_supply_pads': supply_count,
            'power_paths': paths, 'power_transition_vias': transitions, 'button_ground_spreading': spreading,
            'native_unconnected': conn.GetUnconnectedCount(False),
            'limits': ['Copper resistance regression uses the shared 80 C track/barrel model; no ampacity or thermal qualification',
                       'Connectivity is not proof of USB source transitions, reset/timeout behavior or cable/SPI timing',
                       'Hall and button mechanical interfaces remain provisional; panelization is on hold'],
            'errors': errors}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); result = verify(p.LoadBoard(str(args.board)))
    result['errors'].extend(verify_stackup(args.board.read_text(encoding='utf-8')))
    result['board_sha256'] = hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2) + '\n'); print(json.dumps(result, indent=2))
    raise SystemExit(bool(result['errors']))
