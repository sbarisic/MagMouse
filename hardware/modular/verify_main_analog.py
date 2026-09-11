"""Audit main ADC1/button analog routing using the shared copper review screen.

This reports unresolved geometry separately from connectivity. It does not
establish ADC accuracy, settling, thermal behavior or hardware acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import pcbnew as p

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('main_analog_screen', ROOT / 'hardware/kicad/verify_analog_layout.py')
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)
screen.NETS = {'ACT_VMON', 'USB_IMON_BUF', 'USB_IMON_ADC', 'ADC_DECAP'}
screen.NETS |= {f'BTN_{x}_{kind}' for x in 'LMR' for kind in ['ISENSE', 'VREF']}
screen.NETS |= {f'HALL_{x}' for x in 'LMR'}
screen.CONTROL_LIMITS = {}
screen.SEPARATION_GUARDS = set()
screen.FILTER_NETS = {'ADC_DECAP'}
screen.COPPER_LIMITS_MM = {'ADC_DECAP': 5, 'BTN_L_VREF': 10, 'BTN_M_VREF': 25,
                         'BTN_R_VREF': 10, 'BTN_L_ISENSE': 60, 'BTN_M_ISENSE': 55,
                         'BTN_R_ISENSE': 40, 'USB_IMON_BUF': 50, 'USB_IMON_ADC': 18,
                         'ACT_VMON': 40}
shared_noisy = screen.noisy
screen.noisy = lambda net: net == 'BUCK_SW' or shared_noisy(net)


def outside_launch(track, origin, radius=1.5):
    """Keep all copper outside the bounded driver-pin launch, conservatively.

    Shrink the centerline exemption by copper radius so the full conductor must
    fit inside the launch. A via crossing its boundary is retained in full.
    """
    via = isinstance(track, p.PCB_VIA)
    width = p.ToMM(track.GetWidth(p.F_Cu) if via else track.GetWidth())
    a, b = tuple(p.ToMM(track.GetStart())), tuple(p.ToMM(track.GetEnd()))
    r = radius - width / 2
    if via:
        return [] if math.dist(a, origin) <= r else [(a, b)]
    dx, dy = b[0]-a[0], b[1]-a[1]
    x, y = a[0]-origin[0], a[1]-origin[1]
    aa = dx*dx + dy*dy
    if not aa:
        return [] if math.dist(a, origin) <= r else [(a, b)]
    bb = 2*(x*dx+y*dy); cc = x*x+y*y-r*r
    discriminant = bb*bb-4*aa*cc
    if discriminant <= 0:
        return [(a, b)]
    lo = max(0, (-bb-math.sqrt(discriminant))/(2*aa))
    hi = min(1, (-bb+math.sqrt(discriminant))/(2*aa))
    if lo >= hi:
        return [(a, b)]
    point = lambda t: (a[0]+t*dx, a[1]+t*dy)
    return [(point(l), point(h)) for l,h in [(0,lo),(hi,1)] if h-l > 1e-8]


def review_launches(board, result, pads):
    tracks = list(board.GetTracks()); pending = []; reviewed = []
    for finding in result['review_findings']:
        net = finding['net']
        if finding['kind'] != 'switching_proximity' or not net.startswith('BTN_'):
            pending.append(finding); continue
        ref = {'L':'U4','M':'U5','R':'U6'}[net.split('_')[1]]
        pin = '1' if net.endswith('ISENSE') else '4'
        origin = tuple(p.ToMM(pads[ref,pin].GetPosition())); nearest = math.inf
        for a in [t for t in tracks if t.GetNetname() == net]:
            av = isinstance(a,p.PCB_VIA); ar = p.ToMM(a.GetWidth(p.F_Cu) if av else a.GetWidth())/2
            for b in [t for t in tracks if t.GetNetname() == finding['aggressor']]:
                bv = isinstance(b,p.PCB_VIA)
                if not (av or bv or a.GetLayer() == b.GetLayer() or a.GetLayer() != p.F_Cu and b.GetLayer() != p.F_Cu):
                    continue
                br = p.ToMM(b.GetWidth(p.F_Cu) if bv else b.GetWidth())/2
                for start,end in outside_launch(a,origin):
                    vec = lambda q: p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))
                    gap = p.ToMM(p.SEG(vec(start),vec(end)).Distance(p.SEG(b.GetStart(),b.GetEnd())))-ar-br
                    nearest = min(nearest,gap)
        if nearest < .5:
            pending.append(finding)
        else:
            reviewed.append(dict(finding, driver=ref, launch_radius_mm=1.5,
                                 minimum_gap_outside_launch_mm=round(nearest,6) if math.isfinite(nearest) else None,
                                 review='Proximity is confined to the driver pin launch; no extended adjacent run outside it. Hardware noise remains unqualified.'))
    result['review_findings'] = pending
    result['reviewed_driver_pin_launches'] = reviewed


def verify(board):
    result = screen.verify(board)
    result['scope'] = 'Main ADC1, Hall, button references/current sense and power telemetry; geometry review remains separate'
    pads = {(f.GetReference(), q.GetNumber()): q for f in board.GetFootprints() for q in f.Pads() if q.GetNumber()}
    review_launches(board, result, pads)
    distance = p.ToMM((pads['C36', '1'].GetPosition() - pads['U10', '6'].GetPosition()).EuclideanNorm())
    result['actuator_monitor_cap_to_adc_mm'] = round(distance, 3)
    if distance > 5:
        result['errors'].append('ACT_VMON: filter capacitor is more than 5 mm from ADC1 input')
    result['fixed_placement_review_complete'] = not result['errors'] and not result['review_findings']
    result['review_complete'] = result['fixed_placement_review_complete'] and not result['deferred_mechanical_findings']
    result['mechanical_scope'] = 'Static copper review only. Hall/button positions remain provisional under MECHANICAL_INTERFACES.md.'
    for name in ['brake_control_total_track_length_mm', 'control_route_checks', 'control_route_limits_mm_and_vias', 'guarded_switching_separations']:
        result.pop(name, None)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-reviewed', action='store_true')
    args = parser.parse_args()
    result = verify(p.LoadBoard(str(args.board)))
    result['board_sha256'] = hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result['errors']) or args.require_reviewed and bool(result['review_findings']))
