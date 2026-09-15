# SPDX-License-Identifier: GPL-3.0-or-later
"""Run a bounded ACT_5V regeneration study using the current exported netlists."""
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from ngspice_shared import Engine

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEFAULT_DLL = Path.home() / 'AppData/Local/Programs/KiCad/10.0/bin/ngspice.dll'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def value(text):
    match = re.match(r'([\d.]+)([pnumkMR]?)', text)
    number, suffix = match.groups()
    return float(number) * {'': 1, 'R': 1, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6,
                            'm': 1e-3, 'k': 1e3, 'M': 1e6}[suffix]


def inventory():
    result = {'sources': {}, 'capacitors': [], 'brake': {}, 'pins': {}, 'bleeders': []}
    for board in ('Main', 'Wheel', 'Encoder'):
        path = ROOT / f'hardware/bench/package/{board}-netlist.xml'
        tree = ET.parse(path).getroot()
        result['sources'][str(path.relative_to(ROOT))] = sha(path)
        pins = {(n.get('ref'), n.get('pin')): net.get('name')
                for net in tree.findall('./nets/net') for n in net.findall('node')}
        for comp in tree.findall('./components/comp'):
            ref, text = comp.get('ref'), comp.findtext('value')
            nets = {pin: net for (r, pin), net in pins.items() if r == ref}
            if ref.startswith('C') and set(nets.values()) == {'ACT_5V', 'GND'}:
                result['capacitors'].append({'board': board, 'ref': ref, 'value': text, 'farads': value(text)})
            if ref.startswith('R') and set(nets.values()) == {'ACT_5V', 'GND'}:
                result['bleeders'].append({'board': board, 'ref': ref, 'ohms': value(text)})
            if board == 'Wheel' and any(p.get('name') == 'Sheetname' and p.get('value') == '13_Regeneration_Brake'
                                        for p in comp.findall('property')):
                result['brake'][ref] = text
                result['pins'][ref] = nets
    result['nominal_capacitance_F'] = sum(c['farads'] for c in result['capacitors'])
    assert result['pins']['U30'] == {'1': 'BRAKE_OUT', '2': 'GND', '3': 'BRAKE_SENSE', '4': 'BRAKE_REF', '5': 'ACT_5V'}
    assert result['pins']['Q5'] == {'1': 'BRAKE_GATE', '2': 'GND', '3': 'BRAKE_DRAIN'}
    assert result['pins']['U31']['1'] == 'BRAKE_REF' and result['pins']['U31']['2'] == 'GND'
    return result


def thresholds(inv):
    r = {k: value(v) for k, v in inv['brake'].items() if k.startswith('R')}
    top = r['R112'] + r['R113']
    bottom = r['R114']
    feedback = sum(r[x] for x in ('R115', 'R116', 'R117'))
    on = 2.5 * (1 + top / bottom + top / feedback)
    off = on / (1 + top / feedback)
    return {'ideal_on_V': on, 'ideal_off_V': off}


def circuit(inv, case, step):
    def node(net):
        return {'GND': '0', 'ACT_5V': 'load'}.get(net, net.lower())
    lines = ['MagMouse ACT_5V brake transient - isolated simulation only',
             '.options reltol=1e-5 abstol=1e-10 vntol=1e-7 method=gear', '.temp 25',
             f'Crail act 0 {case["cap"]:.12g}', 'Vload act load 0',
             f'Bup 0 act I= time < {case.get("unplug", 100)} ? max((5-v(act))/0.15,0) : 0',
             f'Iregen 0 inj PULSE(0 {case["current"]} 1m 1u 1u {case["pulse"]} {case["period"]})',
             'Vregen inj act 0']
    if case.get('threshold_ramp'):
        lines[5] = 'Bup 0 act I=((time<1m ? 5 : (time<4m ? 5+(time-1m)*1.3/3m : (time<7m ? 6.3-(time-4m)*.9/3m : 5.4)))-v(act))/0.15'
    for ref, text in inv['brake'].items():
        if ref.startswith('R') or ref in ('C66', 'C67'):
            p = inv['pins'][ref]
            factor = case.get('resistor_scale', 1) if ref in ('R121', 'R122', 'R123', 'R124') else 1
            factor *= case.get('divider_scales', {}).get(ref, 1)
            lines.append(f'{ref} {node(p["1"])} {node(p["2"])} {value(text)*factor:.12g}')
    for b in inv['bleeders']:
        lines.append(f'Rbleed_{b["board"]}_{b["ref"]} load 0 {b["ohms"]}')
    lines += [f'Xref brake_ref 0 LM4040_NA2P5 PARAMS: TOL={case.get("reference_tol",0)}',
              '* TLV1811 behavioral fallback: 0.5 mV offset, bounded transport delay, 60 ohm drive.',
              f'Bcmp cmp_src 0 V=2*v(load)*(0.5+0.5*tanh((v(brake_sense)-v(brake_ref)-{case.get("offset",.0005)})/0.0001))',
              'Rdelay cmp_src cmp_tx 1',
              f'Tdelay cmp_tx 0 cmp_rx 0 Z0=1 TD={case["delay"]:.12g}',
              'Rtermination cmp_rx 0 1',
              'Edrive cmp_drive 0 cmp_rx 0 1',
              f'Rdriver cmp_drive brake_out {case.get("driver_ohms",60)}',
              '* Q5 approximation: datasheet Rds(max) at 4.5 V; 6 nC / 4.5 V gate load.',
              f'Cgate brake_gate 0 {case.get("gate_F",1.333333333e-9)}',
              f'Sq5 brake_drain 0 brake_gate 0 qswitch',
              f'.model qswitch SW(Ron={case.get("ron", .032)} Roff=1e12 Vt={100 if case.get("disabled") else 2.5} Vh=0.05)',
              '* No TVS clamp credited; diagnostic voltages above 6.5 V are NOT hardware predictions.',
              '.save v(act) v(brake_sense) v(brake_ref) v(brake_out) v(brake_gate) v(brake_drain) i(vregen) i(vload) @bup[i]',
              f'.tran {step} {case["stop"]} 0 {step}',
              (HERE/'models/lm4040.lib').read_text(encoding='cp1252'), '.end']
    return '\n'.join(lines) + '\n'


def analyze(data, case, inv):
    t, rail, sense, ref, out, gate, drain, regen, load, upstream = data.T
    integrate = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz
    resistors = sum(1 / (value(inv['brake'][r]) * case.get('resistor_scale', 1)) for r in ('R121','R122','R123','R124'))
    brake_current = (rail-drain)*resistors
    power = (rail-drain)**2*resistors
    ein = integrate(rail*(regen+upstream),t)
    eload = integrate(rail*load,t)
    delta = .5*case['cap']*(rail[-1]**2-rail[0]**2)
    error = abs(ein-eload-delta) / max(abs(ein), abs(eload), abs(delta), 1e-9)
    trip = ref + case.get('offset', .0005)
    crossings = np.where((sense[:-1] <= trip[:-1]) & (sense[1:] > trip[1:]))[0]+1
    rising = np.where((brake_current[:-1] < .4) & (brake_current[1:] >= .4))[0]+1
    delays = [(t[rising[rising>=i][0]]-t[i])*1e6 for i in crossings if len(rising[rising>=i])]
    falls = np.where((out[:-1] >= rail[:-1]/2) & (out[1:] < rail[1:]/2))[0]+1
    ons = np.where((out[:-1] < rail[:-1]/2) & (out[1:] >= rail[1:]/2))[0]+1
    return {'peak_rail_V': float(max(rail)), 'min_rail_V': float(min(rail)),
            'max_brake_response_us': max(delays) if delays else None,
            'peak_brake_current_A': float(max(brake_current)), 'peak_resistor_bank_W': float(max(power)),
            'resistor_bank_energy_J': float(integrate(power,t)),
            'average_regeneration_W': float(integrate(rail*regen,t)/(t[-1]-t[0])),
            'energy_balance_relative_error': float(error), 'rail_energy_change_J': float(delta),
            'input_energy_J': float(ein), 'load_energy_J': float(eload),
            'observed_on_V': [float(rail[i]) for i in ons[:6]], 'observed_off_V': [float(rail[i]) for i in falls[:6]],
            'switch_on_count': len(ons), 'below_6p5V': bool(max(rail)<6.5),
            'response_within_10us': bool(delays and max(delays)<=10), 'completed_time_s': float(t[-1])}


VECTORS = ['time', 'v(act)', 'v(brake_sense)', 'v(brake_ref)', 'v(brake_out)', 'v(brake_gate)',
           'v(brake_drain)', 'i(vregen)', 'i(vload)', '@bup[i]']


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dll', type=Path, default=DEFAULT_DLL)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--only', help='Run cases whose names contain this text')
    parser.add_argument('--vendor-reproducer', action='store_true', help='Recreate the original failed TI-comparator deck without running it')
    args=parser.parse_args()
    from fetch_models import fetch
    fetch(HERE/'models', check_only=True)
    dest=HERE/'results'; dest.mkdir(exist_ok=True)
    inv=inventory()
    if args.vendor_reproducer:
        case={'cap':47e-6,'delay':.45e-6,'current':.4,'pulse':.001,'period':.1,'stop':.004}
        text=circuit(inv,case,2e-7)
        start=text.index('* TLV1811 behavioral fallback:')
        end=text.index('* Q5 approximation:')
        text=text[:start]+'Xcmp brake_sense brake_ref load 0 brake_out TLV1811\n'+text[end:]
        text=text.rsplit('.end',1)[0]+(HERE/'models/tlv1811.lib').read_text()+'\n.end\n'
        path=HERE/'model-checks/tlv1811-reproducer.cir'
        path.parent.mkdir(exist_ok=True)
        path.write_text(text,encoding='utf-8')
        print(f'Wrote local vendor-model reproducer: {path}')
        return
    (dest/'inventory.json').write_text(json.dumps(inv,indent=2)+'\n')
    engine=Engine(args.dll)
    cases=[]
    for label, cap in [('minimum',47e-6),('nominal',inv['nominal_capacitance_F'])]:
        for delay in (.45e-6,5e-6,10e-6):
            for scenario in ('pulse','repeated','unplug'):
                c={'name':f'{label}_{delay*1e6:g}us_{scenario}', 'cap':cap,'delay':delay,
                   'current':.4,'pulse':.001,'period':.006,'stop':.013}
                if scenario=='pulse': c.update(period=.1,stop=.004)
                if scenario=='unplug': c.update(unplug=.00105,period=.1,stop=.004)
                cases.append(c)
    for name, current, disabled in [('brake_disabled',.4,True),('excess_regeneration',1,False)]:
        cases.append({'name':name,'cap':47e-6,'delay':.45e-6,'current':current,'pulse':.001,
                      'period':.1,'stop':.0025,'disabled':disabled,'diagnostic':True})
    cases.append(dict(cases[6], name='resistance_stress',ron=.064,resistor_scale=1.05))
    for high in (True,False):
        scales={'R112':1.01 if high else .99, 'R113':1.01 if high else .99,
                'R114':.99 if high else 1.01, **{r:.99 if high else 1.01 for r in ('R115','R116','R117')}}
        cases.append(dict(cases[6], name='threshold_high' if high else 'threshold_low',
                          divider_scales=scales,reference_tol=1 if high else -1,offset=.004 if high else -.004,
                          driver_ohms=120,gate_F=2e-9,ron=.064,resistor_scale=1.05))
    cases.append({'name':'threshold_ramp','cap':47e-6,'delay':.45e-6,'current':0,
                  'pulse':.001,'period':.1,'stop':.008,'threshold_ramp':True})
    if args.smoke: cases=cases[:1]
    if args.only: cases=[c for c in cases if args.only in c['name']]
    report={'model_class':'TI LM4040 reference; behavioral comparator, MOSFET and lumped rail',
            'engine_sha256':sha(args.dll), 'thresholds':thresholds(inv), 'cases':[]}
    for case in cases:
        metrics=[]
        for step in ([2e-7] if args.smoke else [2e-7,1e-7]):
            name=case['name']+f'_{step*1e9:g}ns'
            text=circuit(inv,case,step)
            (dest/f'{name}.cir').write_text(text,encoding='utf-8')
            try:
                engine.run(text)
                data=np.column_stack([engine.vector(v) for v in VECTORS])
                if data[-1,0]<case['stop']*.999: raise RuntimeError('Incomplete transient')
                if not np.isfinite(data).all(): raise RuntimeError('Nonfinite results')
            finally:
                (dest/f'{name}.log').write_text('\n'.join(engine.log),encoding='utf-8')
            np.savez_compressed(dest/f'{name}.npz',data=data,columns=VECTORS)
            metrics.append(analyze(data,case,inv))
        result={'configuration':case,**metrics[-1]}
        result['peak_timestep_delta_V']=abs(metrics[-1]['peak_rail_V']-metrics[0]['peak_rail_V'])
        result['numerical_checks_pass']=result['energy_balance_relative_error']<.005 and result['peak_timestep_delta_V']<.005
        result['delay_timestep_delta_us'] = (abs(metrics[-1]['max_brake_response_us']-metrics[0]['max_brake_response_us'])
                                            if metrics[-1]['max_brake_response_us'] is not None and metrics[0]['max_brake_response_us'] is not None else None)
        result['energy_timestep_relative_delta'] = abs(metrics[-1]['resistor_bank_energy_J']-metrics[0]['resistor_bank_energy_J'])/max(metrics[-1]['resistor_bank_energy_J'],1e-9)
        result['numerical_checks_pass'] &= (result['delay_timestep_delta_us'] is None or result['delay_timestep_delta_us']<.5) and result['energy_timestep_relative_delta']<.01
        report['cases'].append(result)
        (dest/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
        print(case['name'],f"peak={result['peak_rail_V']:.4f} V",f"energy error={result['energy_balance_relative_error']:.3g}",flush=True)


if __name__=='__main__': main()
