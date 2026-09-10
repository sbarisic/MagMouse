# SPDX-License-Identifier: GPL-3.0-or-later
"""Screen actuator copper resistance and local ground spreading with KiCad.

This is a layout regression check, not an ampacity or thermal simulation. The
resistance model counts whole traversed tracks and full via barrels, gives no
credit for parallel copper, and excludes pads, solder, connectors and silicon.
Run physical DRC, distribution and USB reference checks alongside this checker.
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
TEMPERATURE_C = 80
RHO = .01724 * (1 + .00393 * (TEMPERATURE_C - 20))  # ohm mm^2 / metre
THICKNESS_MM = {pcb.F_Cu: .035, pcb.In2_Cu: .030, pcb.B_Cu: .035}
BOARD_MM = 1.578
PLATING_MM = .020  # Screening assumption, pending manufacturer confirmation.

# Project resistance budgets, not manufacturer current ratings. Each path must
# have a physically connected route below its budget without using a zone.
PATHS = [(('U12', '6'), ('U13', '5'), 50)]
PATHS += [(('U13', '6'), (r, '5'), 85) for r in ['U4', 'U5', 'U6']]
PATHS += [(('U13', '6'), ('U21', str(p)), 40) for p in [9, 10, 11]]
for driver, connector in [('U4', 'J2'), ('U5', 'J3'), ('U6', 'J4')]:
    PATHS += [((driver, '6'), (connector, '1'), 25),
              ((driver, '8'), (connector, '2'), 25)]
for phase, pins in enumerate([(13, 14), (16, 17), (19, 20)], 1):
    PATHS += [(('U21', str(p)), ('J5', str(phase)), 55) for p in pins]
for ref in ['R121', 'R122', 'R123', 'R124']:
    PATHS += [(('U13', '6'), (ref, '1'), 100), (('Q5', '3'), (ref, '2'), 65)]

# Minimum saved filled area connected locally to the device, in mm^2. These
# protect the reviewed geometry; they do not imply a junction temperature.
SPREADERS = {'U4': ('9', 2, 20, 10), 'U5': ('9', 2, 17, 10),
             'U6': ('9', 2, 35, 20), 'U21': ('41', 5, 30, 25),
             'Q5': ('2', 1.5, 2, 4)}
BULK_REFS = {'C8', 'C11', 'C14', 'C37', 'C38', 'C39', 'C40', 'C44', 'C45', 'C68', 'C69'}
BYPASS_REFS = {'C7', 'C10', 'C13', 'C41', 'C42', 'C43', 'C65'}


def verify_stackup(source):
    match = re.search(r'^\t\t\(stackup\b.*?^\t\t\)\n', source, re.M | re.S)
    if not match:
        return ['High-current model: missing saved stackup']
    layers = {}
    for layer in re.finditer(r'^\t\t\t\(layer "([^"]+)"(.*?)^\t\t\t\)', match[0], re.M | re.S):
        thickness = re.search(r'\(thickness ([0-9.]+)\)', layer[2])
        if thickness:
            layers[layer[1]] = float(thickness[1])
    expected = {'F.Cu': .035, 'In1.Cu': .030, 'In2.Cu': .030, 'B.Cu': .035}
    errors = [f'High-current model: {name} copper thickness differs from {value} mm'
              for name, value in expected.items() if abs(layers.get(name, -1) - value) > .000001]
    total = sum(value for name, value in layers.items() if name in expected or name.startswith('dielectric'))
    if abs(total - BOARD_MM) > .000001:
        errors.append('High-current model: saved stack thickness differs from barrel length assumption')
    return errors


def uid(item):
    return item.m_Uuid.AsString()


class CopperGraph:
    """Native direct contacts; no geometric guesses or whole-net shortcuts."""

    def __init__(self, board):
        conn = board.GetConnectivity()
        self.items = {uid(t): t for t in board.GetTracks()}
        self.pads = {}
        for footprint in board.GetFootprints():
            for pad in footprint.Pads():
                if pad.GetNumber():
                    self.items[uid(pad)] = pad
                    self.pads.setdefault((footprint.GetReference(), pad.GetNumber()), pad)
        self.adj, self.cost = {}, {}
        for key, item in self.items.items():
            contacts = list(conn.GetConnectedTracks(item)) + list(conn.GetConnectedPads(item))
            self.adj[key] = {uid(t) for t in contacts if uid(t) in self.items
                             and t.GetNetname() == item.GetNetname()}
            if isinstance(item, pcb.PCB_VIA):
                drill = pcb.ToMM(item.GetDrillValue())
                # Thin-wall barrel estimate. Count full board thickness even
                # for a transition between adjacent layers.
                self.cost[key] = RHO * BOARD_MM / 1000 / (math.pi * drill * PLATING_MM)
            elif isinstance(item, pcb.PCB_TRACK):
                thickness = THICKNESS_MM.get(item.GetLayer(), .030)
                self.cost[key] = RHO * pcb.ToMM(item.GetLength()) / 1000 / (
                    pcb.ToMM(item.GetWidth()) * thickness)
            else:
                self.cost[key] = 0

    def path(self, start, end, allowed=None):
        queue, seen = [(0, start, [])], set()
        while queue:
            cost, key, path = heapq.heappop(queue)
            if key in seen or (allowed is not None and key not in allowed):
                continue
            seen.add(key)
            path = path + [key]
            if key == end:
                return cost, path
            for neighbor in self.adj[key] - seen:
                heapq.heappush(queue, (cost + self.cost[neighbor], neighbor, path))
        return None


def filled_area_at(zone, points):
    """Sum filled polygons touched by the specified local contacts, minus holes."""
    poly = zone.GetFilledPolysList(zone.GetLayer())
    total = 0
    for index in range(poly.OutlineCount()):
        if any(poly.Contains(point, index) for point in points):
            total += abs(poly.COutline(index).Area())
            total -= sum(abs(poly.CHole(index, h).Area()) for h in range(poly.HoleCount(index)))
    return total / 1e12


def verify(board):
    board.BuildConnectivity()
    graph = CopperGraph(board)
    errors, paths, spreading = [], [], {}
    if board.GetCopperLayerCount() != 4:
        errors.append('Resistance model requires the reviewed four-layer stackup')
    for source, target, limit in PATHS:
        label = '.'.join(source) + ' -> ' + '.'.join(target)
        a, b = graph.pads.get(source), graph.pads.get(target)
        found = graph.path(uid(a), uid(b)) if a is not None and b is not None else None
        if found is None:
            errors.append(label + ': no copper path')
            continue
        resistance, route = found
        tracks = [graph.items[k] for k in route if isinstance(graph.items[k], pcb.PCB_TRACK)
                  and not isinstance(graph.items[k], pcb.PCB_VIA)]
        vias = [graph.items[k] for k in route if isinstance(graph.items[k], pcb.PCB_VIA)]
        paths.append({'path': label, 'net': a.GetNetname(),
                      'screening_milliohms': round(resistance * 1000, 3), 'budget_milliohms': limit,
                      'counted_track_length_mm': round(sum(pcb.ToMM(t.GetLength()) for t in tracks), 3),
                      'minimum_track_width_mm': min(pcb.ToMM(t.GetWidth()) for t in tracks),
                      'counted_full_barrels': len(vias), 'route_uuids': route})
        if any(t.GetLayer() == pcb.In1_Cu for t in tracks):
            errors.append(label + ': power track uses the In1 ground-reference layer')
        if resistance * 1000 > limit:
            errors.append(f'{label}: {resistance * 1000:.3f} mOhm exceeds {limit} mOhm layout budget')

    for ref, (pin, radius, front_min, back_min) in SPREADERS.items():
        pad = graph.pads.get((ref, pin))
        if pad is None:
            errors.append(f'{ref}: missing thermal/source ground pad')
            continue
        # Local front tracks/pads only: a remote connection through In1 is not
        # evidence of a short connection from the device to its thermal vias.
        origin = pad.GetPosition()
        allowed = {key for key, item in graph.items.items()
                   if item.GetNetname() == 'GND' and item.IsOnLayer(pcb.F_Cu)
                   and pcb.ToMM((item.GetPosition() - origin).EuclideanNorm()) <= radius
                   and (not isinstance(item, pcb.PCB_TRACK) or
                        pcb.ToMM((item.GetEnd() - origin).EuclideanNorm()) <= radius)}
        vias = [t for key, t in graph.items.items() if isinstance(t, pcb.PCB_VIA)
                and key in allowed and graph.path(uid(pad), key, allowed) is not None]
        minimum_vias = 1 if ref == 'Q5' else 4
        if len(vias) < minimum_vias:
            errors.append(f'{ref}: fewer than {minimum_vias} vias with a local front copper connection')
        result = {'local_front_connected_vias': len(vias)}
        for layer, minimum in [(pcb.F_Cu, front_min), (pcb.B_Cu, back_min)]:
            name = 'ACTUATOR_' + ref + '_GND_' + board.GetLayerName(layer)
            zones = [z for z in board.Zones() if z.GetZoneName() == name and not z.GetIsRuleArea()]
            if len(zones) != 1:
                errors.append(f'{name}: expected one local ground spreader')
                continue
            zone = zones[0]
            if zone.GetNetname() != 'GND' or zone.GetLayer() != layer:
                errors.append(f'{name}: incorrect ground net or layer')
                continue
            if zone.GetPadConnection() != pcb.ZONE_CONNECTION_FULL:
                errors.append(f'{name}: expected solid pad connections')
            points = [origin] if layer == pcb.F_Cu else [v.GetPosition() for v in vias]
            area = filled_area_at(zone, points)
            result[board.GetLayerName(layer) + '_local_filled_mm2'] = round(area, 3)
            if area < minimum:
                errors.append(f'{name}: {area:.3f} mm2 of local filled copper is below {minimum} mm2')
        spreading[ref] = result

    capacitors = {}
    for footprint in board.GetFootprints():
        ref = footprint.GetReference()
        nets = {p.GetNetname() for p in footprint.Pads() if p.GetNumber()}
        if ref.startswith('C') and nets == {'ACT_5V', 'GND'}:
            capacitors[ref] = footprint.GetValue()
    if set(capacitors) != BULK_REFS | BYPASS_REFS:
        errors.append('ACT capacitor inventory changed: review nominal storage/inrush/discharge estimates')
    for ref, value in capacitors.items():
        expected = '10uF/25V' if ref in BULK_REFS else '100nF'
        if value != expected:
            errors.append(f'{ref}: ACT capacitor value differs from reviewed {expected}')
    capacitance_uF = 110.7  # Only valid with the inventory/value checks above.
    return {'scope': 'Actuator feed/output trace-barrel resistance screening and local ground spreading',
            'model': {'copper_temperature_C': TEMPERATURE_C, 'outer_copper_mm': .035,
                      'inner_copper_mm': .030, 'full_barrel_length_mm': BOARD_MM,
                      'assumed_barrel_plating_mm': PLATING_MM,
                      'limitations': 'Whole traversed tracks and full barrels; no parallel credit. '
                      'Excludes pads, solder, connectors, semiconductors, plane return resistance, '
                      'inductance and thermal rise. Thickness/plating assumptions need fabrication confirmation.'},
            'current_paths': paths, 'ground_spreading': spreading,
            'actuator_capacitors': {'parts': capacitors, 'nominal_direct_capacitance_uF': capacitance_uF,
                                   'capacitor_only_inrush_mA_at_0_2V_per_ms': capacitance_uF * .2,
                                   'nominal_1k_bleed_time_constant_ms': capacitance_uF,
                                   'effective_capacitance_acceptance_uF': 47,
                                   'limitations': 'Nominal nameplate values only; excludes charge-pump/AVDD/'
                                   'buck capacitors and active loads. DC bias, tolerance and temperature '
                                   'require separate qualification.'},
            'native_unconnected_connections': board.GetConnectivity().GetUnconnectedCount(False),
            'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, default=ROOT / 'hardware/kicad/MagMouse.kicad_pcb')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/pcb-review/high-current-layout-checks.json')
    args = parser.parse_args()
    report = verify(pcb.LoadBoard(str(args.board.resolve())))
    report['errors'].extend(verify_stackup(args.board.read_text(encoding='utf-8')))
    report['board_sha256'] = hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return int(bool(report['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
