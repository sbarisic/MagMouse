"""Check the shaped main PCB's routed input-power and local buck subset.

Run with KiCad Python and pair with fresh native DRC/schematic parity. This
checks physical copper, not source selection, board-wide power or hardware
qualification. The resistance model is shared with the earlier copper audit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import pcbnew as p

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'hardware/kicad'))
from verify_buck_layout import verify as verify_buck
from verify_high_current_layout import CopperGraph, uid, verify_stackup

LOCAL_NETS = {
    'USB_UVLO', 'USB_OVLO', 'USB_OV_1', 'USB_OV_2', 'USB_OV_3',
    'USB_DVDT', 'USB_ILM', 'ILM_BASE_1', 'ILM_BASE_2',
    'ILM_MED_D', 'ILM_HIGH_D', 'BUCK_SW',
}
GROUND_REFS = {
    'J1', 'U12', 'C24', 'C25', 'C88', 'D1', 'R30', 'R35', 'R58',
    'Q1', 'Q2', 'R62', 'R63', 'U19', 'C34', 'U2', 'C1', 'C2', 'C3', 'C23',
}
POWER_PATHS = [
    (('J1', 'A4'), ('U12', '5'), 40),
    (('J1', 'B4'), ('U12', '5'), 40),
    (('U12', '6'), ('C88', '1'), 20),
    (('U12', '6'), ('C1', '1'), 40),
    (('U12', '6'), ('U2', '2'), 45),
    (('U12', '6'), ('U2', '3'), 45),
]


def verify(board):
    items = list(board.GetTracks()) + [q for f in board.GetFootprints() for q in f.Pads()]
    original_nets = {uid(i): i.GetNetname() for i in items}
    board.BuildConnectivity()
    conn = board.GetConnectivity()
    errors = []
    if any(original_nets[uid(i)] != i.GetNetname() for i in items):
        errors.append('Native connectivity changed a copper/pad net assignment; inspect for a short')
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    pads = {(r, q.GetNumber()): q for r, f in fps.items() for q in f.Pads() if q.GetNumber()}
    tracks = list(board.GetTracks())

    def connected(anchor, targets, net):
        start = pads.get(anchor)
        reached = {uid(i) for i in conn.GetConnectedItems(start)} | {uid(start)} if start else set()
        for key in [anchor, *targets]:
            q = pads.get(key)
            if q is None or q.GetNetname() != net or uid(q) not in reached:
                errors.append(f'{net}: {anchor} must reach {key} through copper')

    connected(('U12', '5'), [('J1', 'A4'), ('J1', 'B4'), ('C24', '1'),
                             ('D1', '1'), ('R29', '1'), ('R31', '1')], 'VBUS_USB')
    connected(('U12', '6'), [('C88', '1'), ('C1', '1'), ('U2', '2'), ('U2', '3')], 'PWR_5V')
    connected(('U12', '4'), [('R44', '1')], 'USB_FAULT_N')
    connected(('U19', '1'), [('U19', '4')], 'USB_IMON_BUF')
    connected(('U2', '6'), [('U19', '5'), ('C34', '1')], '+3V3')
    local = {}
    for net in sorted(LOCAL_NETS):
        nodes = [key for key, q in pads.items() if q.GetNetname() == net]
        if len(nodes) < 2:
            errors.append(net + ': missing endpoints')
            continue
        connected(nodes[0], nodes[1:], net)
        copper = [t for t in tracks if t.GetNetname() == net]
        lines = [t for t in copper if not isinstance(t, p.PCB_VIA)]
        local[net] = {'pad_count': len(nodes),
                      'copper_length_mm': round(sum(p.ToMM(t.GetLength()) for t in lines), 6),
                      'vias': sum(isinstance(t, p.PCB_VIA) for t in copper)}
    ilm_length = local.get('USB_ILM', {}).get('copper_length_mm', float('inf'))
    if ilm_length > 25:
        errors.append('USB_ILM exceeds 25 mm total copper budget')
    ilm_origin = pads.get(('U12', '9'))
    ilm_radius = max((p.ToMM((q.GetPosition() - ilm_origin.GetPosition()).EuclideanNorm())
                      for q in pads.values() if q.GetNetname() == 'USB_ILM'), default=0) if ilm_origin else float('inf')
    if ilm_radius > 10.5:
        errors.append('USB_ILM setting/input pads exceed 10.5 mm placement radius')
    bypass_distances = {}
    for cap, pin, maximum in [('C24', '5', 5), ('C88', '6', 5)]:
        distance = p.ToMM((pads[(cap, '1')].GetPosition() - pads[('U12', pin)].GetPosition()).EuclideanNorm())
        bypass_distances[cap] = round(distance, 3)
        if distance > maximum:
            errors.append(cap + ': outside 5 mm local bypass placement budget')

    ground = p.SHAPE_POLY_SET()
    ground_ids = set()
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.GetLayer() == p.In1_Cu and z.GetNetname() == 'GND':
            ground.BooleanAdd(z.GetFilledPolysList(p.In1_Cu)); ground_ids.add(uid(z))
    if ground.OutlineCount() != 1:
        errors.append('In1 must contain one connected saved ground reference outline')
    if any(t.GetLayer() == p.In1_Cu for t in tracks if not isinstance(t, p.PCB_VIA)):
        errors.append('Routing occupies the In1 ground reference')
    checked_ground = 0
    for ref, f in fps.items():
        if ref not in GROUND_REFS:
            continue
        for q in f.Pads():
            if q.GetNetname() != 'GND':
                continue
            checked_ground += 1
            if not ground_ids & {uid(i) for i in conn.GetConnectedItems(q)}:
                errors.append(f'{ref}.{q.GetNumber()}: return does not reach saved In1 ground')

    # Match local power-transition arrays relative to their unchanged pad datums.
    arrays = {}
    specs = [('J1', 'A4', 'VBUS_USB', 0, 2.055, 2, .65),
             ('J1', 'B4', 'VBUS_USB', 0, 2.055, 2, .65),
             ('U12', '5', 'VBUS_USB', 0, -2.75, 3, 1),
             ('U12', '6', 'PWR_5V', 0, 2.45, 3, 1),
             ('C1', '1', 'PWR_5V', 0, 1.45, 3, 1.1)]
    for ref, pin, net, dx, dy, minimum, radius in specs:
        center = pads[(ref, pin)].GetPosition() + p.VECTOR2I(p.FromMM(dx), p.FromMM(dy))
        candidates = [t for t in tracks if isinstance(t, p.PCB_VIA) and t.GetNetname() == net
                      and p.ToMM((t.GetPosition() - center).EuclideanNorm()) <= radius
                      and p.ToMM(t.GetDrillValue()) >= .299
                      and p.ToMM(t.GetWidth(p.F_Cu)) >= .599]
        arrays[ref + '.' + pin] = len(candidates)
        if len(candidates) < minimum:
            errors.append(f'{ref}.{pin}: fewer than {minimum} 0.60/0.30 mm power-transition vias')

    graph = CopperGraph(board)
    paths = []
    for source, target, budget in POWER_PATHS:
        found = graph.path(uid(graph.pads[source]), uid(graph.pads[target]))
        label = '.'.join(source) + ' -> ' + '.'.join(target)
        if found is None:
            errors.append(label + ': missing track/barrel power path')
            continue
        resistance, keys = found
        copper = [graph.items[k] for k in keys if isinstance(graph.items[k], p.PCB_TRACK)]
        paths.append({'path': label, 'screening_milliohms': round(resistance * 1000, 3),
                      'budget_milliohms': budget,
                      'counted_track_mm': round(sum(p.ToMM(t.GetLength()) for t in copper if not isinstance(t, p.PCB_VIA)), 3),
                      'counted_full_barrels': sum(isinstance(t, p.PCB_VIA) for t in copper)})
        if resistance * 1000 > budget:
            errors.append(label + ': exceeds copper resistance regression budget')
    buck = verify_buck(board)
    errors.extend(buck['errors'])
    l1 = fps['L1']
    if l1.GetValue() != 'SRP4020CC-3R3M' or str(l1.GetFPID().GetLibNickname()) != 'MagMouseModular' or str(l1.GetFPID().GetLibItemName()) != 'L_Bourns_SRP4020CC':
        errors.append('Main L1 must use the reviewed Bourns SRP4020CC-3R3M and matching footprint')
    for q in l1.Pads():
        if abs(p.ToMM(q.GetSize().x)-1.5)>0.001 or abs(p.ToMM(q.GetSize().y)-2.4)>0.001:
            errors.append('L1 recommended land dimensions must be 1.5 x 2.4 mm')
    if abs(p.ToMM((pads['L1','1'].GetPosition()-pads['L1','2'].GetPosition()).EuclideanNorm())-3.7)>0.001:
        errors.append('L1 land centre spacing must be 3.7 mm')
    return {'scope': 'USB VBUS feed, U12 passive protection/ILM network, local U19 supply/feedback and buck',
            'local_nets': local, 'usb_ilm_radius_mm': round(ilm_radius, 3),
            'efuse_bypass_pad_distances_mm': bypass_distances,
            'checked_ground_pads': checked_ground, 'in1_ground_outlines': ground.OutlineCount(),
            'power_transition_vias': arrays, 'power_paths': paths,
            'buck_switch_copper_mm': buck['switch_track_length_mm'],
            'native_unconnected': conn.GetUnconnectedCount(False),
            'limits': ['Resistance screening at 80 C assumes 35/30 um outer/inner copper and 20 um barrel plating; full traversed segments/barrels, no parallel credit',
                       'Excludes component/contact/pad and ground-plane impedance, thermal rise and regulator/USB qualification',
                       'Source controls, actuator/interlock copper, ADC telemetry and board-wide logic supply have separate main-controls, main-analog and main-routing reviews',
                       'ILM length/radius are geometric limits, not proof of parasitic capacitance or noise performance',
                       'Mechanical interfaces remain provisional; panelization is on hold'],
            'errors': errors}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(p.LoadBoard(str(args.board)))
    result['errors'].extend(verify_stackup(args.board.read_text(encoding='utf-8')))
    result['board_sha256'] = hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result['errors']))
