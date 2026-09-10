# SPDX-License-Identifier: GPL-3.0-or-later
"""Check analog connectivity/local filters and report geometry needing review.

Run with KiCad Python, physical DRC and the other saved-copper checkers.
Review findings are not waived by a successful connectivity check. This does
not predict ADC accuracy, crosstalk, settling or ground-potential differences.
"""

import argparse
import hashlib
import json
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[2]
NETS = {'ACT_VMON', 'USB_IMON_BUF', 'USB_IMON_ADC', 'ADC_DECAP', 'ADC2_DECAP',
        'BRAKE_REF', 'BRAKE_SENSE'}
NETS |= {'WHEEL_SO' + p for p in 'ABC'} | {'WHEEL_I_' + p for p in 'ABC'}
NETS |= {'BTN_' + p + '_' + kind for p in 'LMR' for kind in ['ISENSE', 'VREF']}
NETS |= {'HALL_' + p for p in 'LMR'}
FILTER_NETS = {'WHEEL_I_' + p for p in 'ABC'}
MECHANICAL_NETS = {'HALL_' + p for p in 'LMR'}
# Protect the control reroutes that removed wheel-sense proximity findings.
# Passing this geometric screen does not establish noise or timing acceptance.
CONTROL_LIMITS = {'BTN_R_IN2': (77, 7), 'DRV_INHC': (52, 7)}
SEPARATION_GUARDS = {('WHEEL_SO' + p, 'BTN_R_IN2') for p in 'ABC'} | {
    ('WHEEL_SOC', 'BTN_R_IN1'), ('WHEEL_SOC', 'DRV_INHC')}
# Whole-net copper regression ceilings after removing redundant branches.
# These are not settling-time, noise, brake-response or thermal acceptance.
COPPER_LIMITS_MM = {'BRAKE_OUT': 14, 'BRAKE_REF': 16, 'BRAKE_SENSE': 12,
                    'BTN_L_VREF': 5, 'BTN_M_VREF': 30, 'BTN_R_VREF': 5,
                    'BTN_L_ISENSE': 43, 'BTN_M_ISENSE': 44, 'BTN_R_ISENSE': 70,
                    'USB_IMON_BUF': 50, 'USB_IMON_ADC': 14, 'ACT_VMON': 18}
GROUND_REFS = {'U10', 'U23', 'U19', 'U7', 'U8', 'U9', 'U30', 'U31',
               'C9', 'C12', 'C15', 'C19', 'C20', 'C21', 'C33', 'C34', 'C36',
               'C56', 'C57', 'C58', 'C59', 'C60', 'C61', 'C65', 'C66', 'C67',
               'R11', 'R12', 'R17', 'R18', 'R23', 'R24', 'R68', 'R114'}


def uid(item):
    return item.m_Uuid.AsString()


def noisy(net):
    return (net in {'SW', 'WHEEL_CPH', 'WHEEL_CPL', 'WHEEL_BUCK_SW', 'BRAKE_DRAIN',
                    'BRAKE_GATE', 'BRAKE_OUT'} or net.startswith(('WHEEL_PHASE_', 'WHEEL_PWM_', 'DRV_INH'))
            or net.startswith('BTN_') and ('_COIL_' in net or net.endswith(('_IN1', '_IN2'))))


def split_findings(findings):
    """Defer only Hall geometry, never connectivity errors or other nets."""
    fixed, mechanical = [], []
    for finding in findings:
        (mechanical if finding['net'] in MECHANICAL_NETS else fixed).append(finding)
    return fixed, mechanical


def verify(board):
    board.BuildConnectivity()
    conn = board.GetConnectivity()
    entries = [(f.GetReference(), p) for f in board.GetFootprints() for p in f.Pads() if p.GetNumber()]
    pads = {(r, p.GetNumber()): p for r, p in entries}
    tracks = list(board.GetTracks())
    errors, metrics, findings, controls = [], {}, [], {}
    ground = pcb.SHAPE_POLY_SET()
    ground_ids = set()
    for zone in board.Zones():
        if zone.GetIsRuleArea() or zone.GetNetname() != 'GND' or zone.GetLayer() != pcb.In1_Cu:
            continue
        fill = zone.GetFilledPolysList(pcb.In1_Cu)
        if fill.OutlineCount():
            ground.BooleanAdd(fill)
            ground_ids.add(uid(zone))
    if not ground.OutlineCount():
        errors.append('Analog reference: no saved filled In1 ground plane')

    for net in sorted(NETS | CONTROL_LIMITS.keys()):
        nodes = [(r, p) for r, p in entries if p.GetNetname() == net]
        if len(nodes) < 2:
            errors.append(net + ': missing analog endpoints')
            continue
        reached = {uid(i) for i in conn.GetConnectedItems(nodes[0][1])} | {uid(nodes[0][1])}
        for ref, pad in nodes[1:]:
            if uid(pad) not in reached:
                errors.append(f'{net}: disconnected {ref}.{pad.GetNumber()}')
        copper = [t for t in tracks if t.GetNetname() == net]
        vias = [t for t in copper if isinstance(t, pcb.PCB_VIA)]
        lines = [t for t in copper if not isinstance(t, pcb.PCB_VIA)]
        length = sum(pcb.ToMM(t.GetLength()) for t in lines)
        if any(t.GetLayer() == pcb.In1_Cu for t in lines):
            errors.append(net + ': signal track on the ground-reference layer')
        if net in FILTER_NETS:
            if vias or any(t.GetLayer() != pcb.F_Cu for t in lines):
                errors.append(net + ': ADC input filter must remain front-only without signal vias')
            if length > 8:
                errors.append(net + ': filtered ADC copper exceeds the 8 mm project budget')

        # Report the complete union of front-track shadows. Via transitions
        # necessarily pierce In1; exclude only 0.7 mm around this net's vias.
        # This tests copper directly below traces, without an impedance margin.
        shadow = pcb.SHAPE_POLY_SET()
        for track in lines:
            if track.GetLayer() == pcb.F_Cu:
                shape = pcb.SHAPE_POLY_SET()
                track.TransformShapeToPolygon(shape, pcb.F_Cu, 0, pcb.FromMM(.001), pcb.ERROR_OUTSIDE)
                shadow.BooleanAdd(shape)
        shadow.BooleanSubtract(ground)
        for via in vias:
            shape = pcb.SHAPE_POLY_SET()
            via.TransformShapeToPolygon(shape, pcb.F_Cu, pcb.FromMM(.4), pcb.FromMM(.001), pcb.ERROR_OUTSIDE)
            shadow.BooleanSubtract(shape)
        missing = abs(shadow.Area()) / 1e12
        if missing > .00001:
            message = f'{net}: {missing:.6f} mm2 of front copper lacks an In1 ground shadow outside transitions'
            if net in FILTER_NETS or net in CONTROL_LIMITS:
                errors.append(message)
            else:
                findings.append({'kind': 'reference_shadow', 'net': net, 'detail': message})
        if length > 60 and net in NETS:
            findings.append({'kind': 'long_analog_net', 'net': net,
                             'detail': f'{length:.3f} mm total copper; review loading, settling and pickup'})
        target = controls if net in CONTROL_LIMITS else metrics
        target[net] = {'pads': len(nodes), 'total_track_length_mm': round(length, 3),
                        'signal_vias': len(vias), 'layers': sorted({board.GetLayerName(t.GetLayer()) for t in lines}),
                        'front_shadow_missing_mm2': round(missing, 6)}
        if net in CONTROL_LIMITS:
            max_length, max_vias = CONTROL_LIMITS[net]
            if length > max_length or len(vias) > max_vias:
                errors.append(f'{net}: control route exceeds {max_length} mm / {max_vias} via regression budget')

    ground_count = 0
    for ref, pad in entries:
        if ref in GROUND_REFS and pad.GetNetname() == 'GND':
            ground_count += 1
            if not {uid(t) for t in conn.GetConnectedItems(pad)} & ground_ids:
                errors.append(f'{ref}.{pad.GetNumber()}: analog ground does not reach saved In1 fill')

    # Same-side proximity and In2/B projections have no intervening ground
    # plane. F versus In2/B is shielded by In1 where the reference remains intact.
    # Include vias on every layer. This is a review screen, not a crosstalk model;
    # fine-pitch launches are deliberately reported rather than silently waived.
    def description(t):
        via = isinstance(t, pcb.PCB_VIA)
        a, b = pcb.ToMM(t.GetStart()), pcb.ToMM(t.GetEnd())
        return {'item': t, 'seg': pcb.SEG(t.GetStart(), t.GetEnd()), 'net': t.GetNetname(),
                'via': via, 'layer': t.GetLayer(),
                'radius': pcb.ToMM(t.GetWidth(pcb.F_Cu) if via else t.GetWidth()) / 2,
                'box': (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))}
    analog = [description(t) for t in tracks if t.GetNetname() in NETS]
    aggressors = [description(t) for t in tracks if noisy(t.GetNetname())]
    pairs = {}
    for a in analog:
        for b in aggressors:
            if not (a['via'] or b['via'] or a['layer'] == b['layer'] or
                    a['layer'] != pcb.F_Cu and b['layer'] != pcb.F_Cu):
                continue
            margin = a['radius'] + b['radius'] + .5
            aa, bb = a['box'], b['box']
            if aa[0] > bb[2] + margin or bb[0] > aa[2] + margin or aa[1] > bb[3] + margin or bb[1] > aa[3] + margin:
                continue
            gap = pcb.ToMM(a['seg'].Distance(b['seg'])) - a['radius'] - b['radius']
            key = a['net'], b['net']
            if gap < .5 and (key not in pairs or gap < pairs[key]['edge_gap_mm']):
                pairs[key] = {'kind': 'switching_proximity', 'net': a['net'], 'aggressor': b['net'],
                              'edge_gap_mm': round(gap, 6), 'analog_uuid': uid(a['item']),
                              'aggressor_uuid': uid(b['item']),
                              'analog_start_mm': list(pcb.ToMM(a['item'].GetStart())),
                              'layers': [board.GetLayerName(a['layer']), board.GetLayerName(b['layer'])]}
    findings.extend(pairs[k] for k in sorted(pairs))
    for net, aggressor in sorted(SEPARATION_GUARDS):
        if (net, aggressor) in pairs:
            errors.append(f'{net}/{aggressor}: guarded switching separation below 0.5 mm')
    findings, mechanical = split_findings(findings)
    brake_lengths = {net: round(sum(pcb.ToMM(t.GetLength()) for t in tracks
                     if t.GetNetname() == net and not isinstance(t, pcb.PCB_VIA)), 3)
                     for net in ['BRAKE_GATE', 'BRAKE_OUT', 'BRAKE_REF']}
    for net, limit in COPPER_LIMITS_MM.items():
        if net not in metrics and net not in brake_lengths:
            continue  # Missing endpoints are already errors above.
        length = (metrics[net]['total_track_length_mm'] if net in metrics else brake_lengths[net])
        if length > limit:
            errors.append(f'{net}: total copper {length:.3f} mm exceeds the {limit} mm regression ceiling')
    return {'scope': 'Analog continuity, ADC2 local filters and saved-ground connections; geometry review screen',
            'analog_nets': metrics, 'checked_ground_pads': ground_count,
            'control_route_checks': controls,
            'control_route_limits_mm_and_vias': CONTROL_LIMITS,
            'guarded_switching_separations': [
                {'net': net, 'aggressor': aggressor, 'screen_clearance_mm': .5,
                 'passed': (net, aggressor) not in pairs}
                for net, aggressor in sorted(SEPARATION_GUARDS)],
            'review_findings': findings,
            'deferred_mechanical_findings': mechanical,
            'mechanical_deferral_reason': 'Hall placement awaits paddle/magnet CAD. Geometry only; '
            'Hall continuity and all hard checks remain mandatory.',
            'fixed_placement_review_complete': not errors and not findings,
            'review_complete': not errors and not findings and not mechanical,
            'brake_control_total_track_length_mm': brake_lengths,
            'whole_net_copper_regression_limits_mm': COPPER_LIMITS_MM,
            'limitations': 'Proximity uses a 0.5 mm project screening distance, includes pin launches, '
            'and does not predict coupling. Front shadows exclude own-via transitions; internal/back '
            'return paths and ground voltage drops need whole-board review. Supply routing and '
            'source/ADC settling still need review and hardware measurements.',
            'native_unconnected_connections': conn.GetUnconnectedCount(False), 'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, default=ROOT / 'hardware/kicad/MagMouse.kicad_pcb')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/pcb-review/analog-layout-checks.json')
    parser.add_argument('--require-reviewed', action='store_true',
                        help='Also fail on unresolved non-mechanical geometry; Hall geometry stays explicitly deferred')
    args = parser.parse_args()
    report = verify(pcb.LoadBoard(str(args.board.resolve())))
    report['board_sha256'] = hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return int(bool(report['errors']) or (args.require_reviewed and bool(report['review_findings'])))


if __name__ == '__main__':
    raise SystemExit(main())
