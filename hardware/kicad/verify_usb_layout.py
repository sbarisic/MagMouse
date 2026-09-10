# SPDX-License-Identifier: GPL-3.0-or-later
"""Audit saved USB copper and its filled In1 reference using KiCad's Python.

This checks layout geometry and connectivity, not measured impedance or USB
electrical compliance. Run native DRC and schematic parity alongside this audit.
"""

import argparse
import hashlib
import heapq
import json
import math
import re
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[2]
USB_NETS = {'USB_DP', 'USB_DM', 'MCU_USB_DP', 'MCU_USB_DM'}
WIDTH_MM = 0.1466
GAP_MM = 0.1501
REFERENCE_MARGIN_MM = 0.327  # Three times the selected 0.109 mm L1-L2 dielectric.



def verify_stackup(source):
    """Validate saved dielectric/copper dimensions used by the 90-ohm selection."""
    match = re.search(r'^\t\t\(stackup\b.*?^\t\t\)\n', source, re.M | re.S)
    if not match:
        return ['USB stackup: missing explicit saved stackup']
    layers = {}
    for layer in re.finditer(r'^\t\t\t\(layer "([^"]+)"(.*?)^\t\t\t\)', match[0], re.M | re.S):
        thickness = re.search(r'\(thickness ([0-9.]+)\)', layer[2])
        if thickness:
            layers[layer[1]] = float(thickness[1])
    expected = {'F.Cu': 0.035, 'dielectric 1': 0.109, 'In1.Cu': 0.030,
                'dielectric 2': 1.230, 'In2.Cu': 0.030, 'dielectric 3': 0.109, 'B.Cu': 0.035}
    return [f'USB stackup: {name} differs from the selected {value} mm JLC041611-2116 dimension'
            for name, value in expected.items() if abs(layers.get(name, -1) - value) > 0.000001]


def xy(point):
    return tuple(pcb.ToMM(point))


def segment_distance(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    t = max(0, min(1, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length2)) if length2 else 0
    return math.hypot(point[0] - a[0] - t * dx, point[1] - a[1] - t * dy)



def copper_path_length(lines, start_pad, end_pad):
    """Shortest centerline length, with zero-length connectivity inside lands."""
    points = {xy(t.GetStart()) for t in lines} | {xy(t.GetEnd()) for t in lines}
    graph = {point: [] for point in points}
    for track in lines:
        a, b = xy(track.GetStart()), xy(track.GetEnd())
        on_line = sorted((point for point in points if segment_distance(point, a, b) < 0.000002),
                         key=lambda point: math.dist(a, point))
        for left, right in zip(on_line, on_line[1:]):
            length = math.dist(left, right)
            graph[left].append((right, length))
            graph[right].append((left, length))
    for name, pad in [('start', start_pad), ('end', end_pad)]:
        graph[name] = []
        for point in points:
            if pad.HitTest(pcb.VECTOR2I(pcb.FromMM(point[0]), pcb.FromMM(point[1]))):
                graph[name].append((point, 0))
                graph[point].append((name, 0))
    queue = [(0, 0, 'start')]
    costs = {'start': 0}
    serial = 0
    while queue:
        distance, _, node = heapq.heappop(queue)
        if distance != costs[node]:
            continue
        if node == 'end':
            return distance
        for other, length in graph[node]:
            candidate = distance + length
            if candidate < costs.get(other, math.inf):
                costs[other] = candidate
                serial += 1
                heapq.heappush(queue, (candidate, serial, other))
    return math.inf


def verify(board):
    # Retain the input USB objects: KiCad can propagate a different net onto
    # malformed copper while rebuilding connectivity. Do not lose those objects.
    original_usb = {t.m_Uuid.AsString(): t for t in board.GetTracks()
                    if t.GetNetname() in USB_NETS}
    board.BuildConnectivity()
    conn = board.GetConnectivity()
    pad_entries = [(f.GetReference(), p) for f in board.GetFootprints()
                   for p in f.Pads() if p.GetNumber()]
    pads = {(ref, p.GetNumber()): p for ref, p in pad_entries}
    errors = []

    def reached(pad):
        return {i.m_Uuid.AsString() for i in conn.GetConnectedItems(pad)} | {pad.m_Uuid.AsString()}

    def connected(net, keys):
        if any(k not in pads for k in keys):
            errors.append(f'{net}: missing expected pad')
            return
        ids = reached(pads[keys[0]])
        for key in keys:
            p = pads[key]
            if p.GetNetname() != net or p.m_Uuid.AsString() not in ids:
                errors.append(f'{net}: {keys[0]} does not reach {key} through the expected copper')

    connected('USB_DP', [('J1', 'A6'), ('J1', 'B6'), ('U1', '1'), ('R6', '2')])
    connected('USB_DM', [('J1', 'A7'), ('J1', 'B7'), ('U1', '2'), ('R5', '2')])
    connected('MCU_USB_DP', [('R6', '1'), ('U3', '24')])
    connected('MCU_USB_DM', [('R5', '1'), ('U3', '23')])
    tracks = [t for t in board.GetTracks()
              if t.GetNetname() in USB_NETS or t.m_Uuid.AsString() in original_usb]
    lines = [t for t in tracks if not isinstance(t, pcb.PCB_VIA)]
    if any(isinstance(t, pcb.PCB_VIA) or t.GetLayer() != pcb.F_Cu for t in tracks):
        errors.append('USB: all data copper must remain on F.Cu without signal vias')
    if any(abs(pcb.ToMM(t.GetWidth()) - WIDTH_MM) > 0.000002 for t in lines):
        errors.append('USB: track width differs from the selected 0.1466 mm geometry')

    # Use the saved fill, not a fresh fill which could hide stale/unfilled output.
    # Boolean subtraction checks the complete swept area, including holes and
    # narrow notches, rather than sampling a few points along the centerline.
    ground = pcb.SHAPE_POLY_SET()
    ground_zone_ids = set()
    for zone in board.Zones():
        if zone.GetIsRuleArea() or zone.GetNetname() != 'GND' or zone.GetLayer() != pcb.In1_Cu:
            continue
        filled = zone.GetFilledPolysList(pcb.In1_Cu)
        if filled.OutlineCount():
            ground.BooleanAdd(filled)
            ground_zone_ids.add(zone.m_Uuid.AsString())
    if not ground.OutlineCount():
        errors.append('USB reference: no saved filled In1 GND copper')
    missing_area = 0.0
    uncovered = []
    for t in lines:
        sweep = pcb.SHAPE_POLY_SET()
        t.TransformShapeToPolygon(sweep, pcb.F_Cu, pcb.FromMM(REFERENCE_MARGIN_MM),
                                  pcb.FromMM(0.001), pcb.ERROR_OUTSIDE)
        sweep.BooleanSubtract(ground)
        area = abs(sweep.Area()) / 1e12
        if area > 0.00001:
            missing_area += area
            uncovered.append(t.m_Uuid.AsString())
    if uncovered:
        errors.append(f'USB reference: {len(uncovered)} segments lack continuous In1 ground across the required margin')

    for ref, pad in pad_entries:
        if (ref == 'U1' and pad.GetNumber() == '3') or (ref == 'J1' and pad.GetNetname() == 'GND'):
            if not reached(pad) & ground_zone_ids:
                errors.append(f'ESD grounding: {ref}.{pad.GetNumber()} does not reach the filled In1 ground plane')
    esd = pads.get(('U1', '3'))
    esd_vias = []
    if esd:
        ids = reached(esd)
        esd_vias = [t for t in board.GetTracks() if isinstance(t, pcb.PCB_VIA)
                    and t.GetNetname() == 'GND' and t.m_Uuid.AsString() in ids
                    and esd.HitTest(t.GetPosition())]
    if not esd_vias:
        errors.append('ESD grounding: missing direct filled/capped via in the U1 ground land')

    # Check local series-resistor placement, independent of board origin.
    termination_distances = {}
    for ref, pin in [('R6', '24'), ('R5', '23')]:
        if (ref, '1') in pads and ('U3', pin) in pads:
            distance = math.dist(xy(pads[ref, '1'].GetPosition()), xy(pads['U3', pin].GetPosition()))
            termination_distances[ref] = round(distance, 4)
            if distance > 3:
                errors.append(f'{ref}: series termination is more than 3 mm from its ESP32 USB pad')

    segments = {n: [(xy(t.GetStart()), xy(t.GetEnd())) for t in lines if t.GetNetname() == n]
                for n in USB_NETS}
    lengths = {n: round(sum(math.dist(a, b) for a, b in segs), 6) for n, segs in segments.items()}
    coupled = total = 0.0
    for n, other in [('USB_DP', 'USB_DM'), ('USB_DM', 'USB_DP')]:
        for a, b in segments[n]:
            length = math.dist(a, b)
            samples = max(1, math.ceil(length / 0.1))
            for k in range(samples):
                t = (k + 0.5) / samples
                pt = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
                distance = min((segment_distance(pt, c, d) for c, d in segments[other]), default=math.inf)
                total += length / samples
                if abs(distance - (WIDTH_MM + GAP_MM)) <= 0.01:
                    coupled += length / samples
    fraction = coupled / total if total else 0
    if fraction < 0.85:
        errors.append('USB geometry: less than 85% of connector-side copper has the selected pair spacing')

    # Evaluate both reversible connector contact paths. The main coupled run
    # alone does not include skew introduced by connector and resistor fanouts.
    path_lengths = {}
    skews = {}
    for orientation in ['A', 'B']:
        pair = {}
        for sign, contact, esd_pin, resistor, mcu_pin in [
                ('P', '6', '1', 'R6', '24'), ('M', '7', '2', 'R5', '23')]:
            keys = [('J1', orientation + contact), ('U1', esd_pin),
                    (resistor, '2'), (resistor, '1'), ('U3', mcu_pin)]
            if any(key not in pads for key in keys):
                errors.append('USB path: missing expected endpoint')
                continue
            source, esd_pad, before, after, mcu = [pads[key] for key in keys]
            front = [t for t in lines if t.GetNetname() == 'USB_D' + sign]
            tail = [t for t in lines if t.GetNetname() == 'MCU_USB_D' + sign]
            direct = copper_path_length(front, source, before)
            through_esd = (copper_path_length(front, source, esd_pad) +
                           copper_path_length(front, esd_pad, before))
            if not math.isfinite(direct) or not math.isfinite(through_esd):
                errors.append(f'USB path: {orientation} D{sign} lacks a continuous route through ESD')
            elif through_esd - direct > 0.2:
                errors.append(f'USB path: {orientation} D{sign} ESD is on a branch longer than 0.2 mm')
            pair[sign] = direct + copper_path_length(tail, after, mcu)
        path_lengths[orientation] = {key: round(value, 6) if math.isfinite(value) else None
                                     for key, value in pair.items()}
        skew = abs(pair.get('P', math.inf) - pair.get('M', math.inf))
        skews[orientation] = round(skew, 6) if math.isfinite(skew) else None
        if not math.isfinite(skew) or skew > 2.5:
            errors.append(f'USB path: {orientation} contact path exceeds the 2.5 mm layout skew budget')

    return {'scope': 'Saved USB continuity, 90-ohm design geometry, filled In1 reference and ESD grounding',
            'board_is_not_usb_compliance_or_impedance_acceptance': True,
            'width_mm': WIDTH_MM, 'gap_mm': GAP_MM,
            'reference_margin_beyond_trace_edge_mm': REFERENCE_MARGIN_MM,
            'uncovered_reference_area_sum_mm2': round(missing_area, 6),
            'uncovered_segment_uuids': uncovered,
            'copper_lengths_mm': lengths, 'contact_path_lengths_mm': path_lengths,
            'contact_path_skew_mm': skews, 'contact_path_skew_budget_mm': 2.5, 'coupled_copper_fraction': round(fraction, 5),
            'termination_pad_distances_mm': termination_distances,
            'u1_ground_vias_requiring_fill_and_cap': len(esd_vias),
            'native_unconnected_connections': conn.GetUnconnectedCount(False), 'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, default=ROOT / 'hardware/kicad/MagMouse.kicad_pcb')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/pcb-review/usb-layout-checks.json')
    args = parser.parse_args()
    report = verify(pcb.LoadBoard(str(args.board.resolve())))
    report['errors'].extend(verify_stackup(args.board.read_text(encoding='utf-8')))
    report['selected_stackup'] = 'JLC041611-2116, 1 oz outer/inner'
    report['board_sha256'] = hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return int(bool(report['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
