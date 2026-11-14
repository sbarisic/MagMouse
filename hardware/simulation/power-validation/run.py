# SPDX-License-Identifier: GPL-3.0-or-later
"""Current-board power/interlock screening; not firmware or hardware acceptance."""
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
import zipfile
import io

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PCB = ROOT / 'hardware/two-layer/sandwich'
WORK = ROOT / 'build/power-validation'
OUT = HERE / 'results'
KICAD = Path('C:/Users/cartm/AppData/Local/Programs/KiCad/10.0/bin')
sys.path.insert(0, str(HERE.parent / 'brake'))
from ngspice_shared import Engine


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, default=lambda x:x.item()) + '\n', encoding='utf-8')


def value(text):
    m = re.match(r'([\d.]+)([kMmunpR]?)', text)
    return float(m[1]) * {'': 1, 'R': 1, 'k': 1e3, 'M': 1e6,
                         'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12}[m[2]]


def inputs():
    import xml.etree.ElementTree as ET
    boards = {}; sources = {}
    for name in ('Lower', 'Upper', 'Wheel', 'Encoder'):
        folder = PCB / name.lower() if name != 'Encoder' else ROOT / 'hardware/two-layer/encoder'
        sch = folder / (name + '.kicad_sch')
        target = WORK / (name + '.xml')
        subprocess.run([str(KICAD / 'kicad-cli.exe'), 'sch', 'export', 'netlist',
                        '--format', 'kicadxml', '-o', str(target), str(sch)], check=True,
                       capture_output=True)
        x = ET.parse(target).getroot()
        comps = {c.get('ref'): c.findtext('value') for c in x.findall('components/comp')}
        pins = {(n.get('ref'), n.get('pin')): net.get('name')
                for net in x.findall('nets/net') for n in net.findall('node')}
        boards[name] = (comps, pins)
        for f in list(folder.glob('*.kicad_sch')) + [folder / (name + '.kicad_pcb')]:
            sources[f.relative_to(ROOT).as_posix()] = sha(f)
    sources['hardware/common/MagMouse.kicad_sym'] = sha(ROOT / 'hardware/common/MagMouse.kicad_sym')
    power_file=PCB/'circuit-review/power-paths.json'
    power=json.loads(power_file.read_text())
    for board in ('Lower','Upper','Wheel'):
        assert sha(PCB/board.lower()/(board+'.kicad_pcb'))==power['boards'][board]['source_sha256']
    for board,src,dst,expected in [('Lower','J1.A9','J103.2',5.779),
            ('Upper','J104.2','U12.5',7.600),('Upper','U12.6','U13.5',46.819),
            ('Upper','U13.6','J10.1',35.732),('Wheel','J11.1','U21.9',36.235)]:
        path=next(x for x in power['boards'][board]['paths'] if x['source']==src and x['destination']==dst)
        assert abs(path['after_mohm']-expected)<.0001
    sources[power_file.relative_to(ROOT).as_posix()]=sha(power_file)
    # Explicit topology assertions bind the abstractions to the actual schematic.
    checks = {
        'Upper': {'R35': {'1': 'USB_OVLO', '2': 'GND'},
                  'D3': {'1': 'ACT_UVLO', '3': 'ACT_DRIVE_EN'},
                  'U15': {'1': 'GND', '2': 'ACT_HEARTBEAT', '3': 'ARM_VALID', '5': 'ACT_PERMIT'},
                  'Q1': {'1': 'SOURCE_OK'}, 'Q2': {'1': 'SOURCE_3A'}},
        'Wheel': {'U40': {'1': 'WHEEL_VM_OK', '2': 'GND', '3': 'ACT_DRIVE_EN',
                         '5': 'WHEEL_VM_SENSE', '6': '+3V3'},
                  'R147': {'1': 'ACT_5V', '2': 'WHEEL_VM_SENSE'},
                  'R148': {'1': 'WHEEL_VM_SENSE', '2': 'GND'},
                  'C102': {'1': 'WHEEL_VM_SENSE', '2': 'GND'},
                  'R149': {'1': '+3V3', '2': 'WHEEL_VM_OK'},
                  'U21': {'23': 'ACT_DRIVE_EN', '28': 'WHEEL_RUN_EN',
                          '30': 'WHEEL_RUN_EN', '32': 'WHEEL_RUN_EN'},
                  'Q4': {'1': 'WHEEL_RUN_EN'}}}
    for board, refs in checks.items():
        for ref, pins in refs.items():
            for pin, net in pins.items():
                assert boards[board][1][ref, pin] == net, (board, ref, pin, net)
    uc,up=boards['Upper']
    for refs,start,end in [(('R31','R32','R33','R34'),'VBUS_USB','USB_OVLO'),
                           (('R36','R37','R38'),'PWR_5V','ACT_UVLO'),
                           (('R56','R57','R58'),'USB_ILM','GND')]:
        node=start
        for ref in refs:
            assert up[ref,'1']==node
            node=up[ref,'2']
        assert node==end
    for ref,a,b in [('R29','VBUS_USB','USB_UVLO'),('R30','USB_UVLO','GND'),
                    ('R39','ACT_UVLO','GND'),('R46','+3V3','WD_RCEXT'),
                    ('C27','WD_RCEXT','WD_CEXT')]:
        assert up[ref,'1']==a and up[ref,'2']==b
    assert all(uc[r]=='TPS259470LRPWR' for r in ('U12','U13'))
    assert all(abs(value(uc[r])-10e-9)<1e-15 for r in ('C25','C26')), 'Recalculate eFuse slew'
    assert boards['Wheel'][0]['U40']=='TPS3808G01DBVR'
    assert boards['Wheel'][1]['U40', '4'].startswith('unconnected-')
    caps = {}
    for rail in ('VBUS_USB', 'PWR_5V', '+3V3', 'ACT_5V'):
        parts = []
        for board, (comps, pins) in boards.items():
            for ref, val in comps.items():
                if ref.startswith('C') and {pins.get((ref, '1')), pins.get((ref, '2'))} == {rail, 'GND'}:
                    parts.append({'board': board, 'ref': ref, 'F': value(val)})
        caps[rail] = {'nominal_F': sum(x['F'] for x in parts), 'parts': parts}
    dump(OUT / 'inputs.json', {'source_sha256': sources, 'capacitors': caps,
                              'topology_assertions': checks})
    return boards, caps, sources


def models():
    directory = WORK / 'models'; directory.mkdir(exist_ok=True)
    urls = {'tps3808': 'https://www.ti.com/lit/zip/slim038b',
            'tps25947': 'https://www.ti.com/lit/zip/slvmdj6a'}
    info = {}
    for name, url in urls.items():
        archive = directory / (name + '.zip')
        if not archive.exists():
            urllib.request.urlretrieve(url, archive)
        z = zipfile.ZipFile(io.BytesIO(archive.read_bytes()))
        member = next(n for n in z.namelist() if n.lower().endswith('.lib'))
        raw = z.read(member); lib = directory / (name + '-original.lib'); lib.write_bytes(raw)
        info[name] = {'url': url, 'archive_sha256': sha(archive), 'library_sha256': sha(lib)}
        if name == 'tps25947':
            assert b'$CDNENCSTART' in raw
            info[name]['status'] = 'Encrypted PSpice model; NOT executed by ngspice.'
        else:
            s = raw.decode('cp1252')
            s, n = re.subn(r'^\+ERROR=\{ERROR\((?:1|0\.7|0\.3)==0,"ZERO VALUED COMPONENT"\)\}\s*$', '', s, flags=re.M)
            assert n == 9  # All nine assertions test nonzero literal constants.
            s, nc = re.subn(r'(?im)^(C\S+\s+\S+\s+\S+)\s+Cbreak\s+', r'\1 ', s)
            assert nc == 10
            s, nm = re.subn(r'(?im)^\.model Cbreak CAP C=1\s*$', '', s); assert nm == 1
            adapted = directory / 'tps3808-ngspice.lib'; adapted.write_text(s, encoding='cp1252')
            info[name].update(status='TI transistor macro-model with documented syntax adaptation; not independently validated against PSpice.',
                              adapted_sha256=sha(adapted), adaptation='Remove nine always-false ERROR annotations; replace ten unity Cbreak capacitor models with plain capacitors. No component values changed.')
    info['engine'] = {'path': str(KICAD / 'ngspice.dll'), 'sha256': sha(KICAD / 'ngspice.dll')}
    dump(OUT / 'models.json', info)
    return directory / 'tps3808-ngspice.lib'


def logic(boards, supplied):
    nets = {'GND': False, '+3V3': True, **supplied}
    stages = [('Upper', 'U14', [(1, None, 6), (3, None, 4)]),
              ('Upper', 'U18', [(1, 2, 3), (4, 5, 6), (9, 10, 8), (12, 13, 11)]),
              ('Upper', 'U16', [(1, 2, 3), (4, 5, 6), (9, 10, 8), (12, 13, 11)]),
              ('Wheel', 'U22', [(1, 2, 3), (4, 5, 6), (9, 10, 8), (12, 13, 11)]),
              ('Wheel', 'U41', [(1, 2, 4)])]
    for _ in range(6):
        for board, ref, gates in stages:
            pins = boards[board][1]
            for a, b, y in gates:
                na, ny = pins[ref, str(a)], pins[ref, str(y)]
                nb = pins[ref, str(b)] if b else None
                if na in nets and (nb is None or nb in nets):
                    nets[ny] = (not nets[na]) if nb is None else (nets[na] and nets[nb])
    return nets


def gate_checks(boards):
    count = 0
    names = ('CC_OUT1', 'CC_OUT2', 'ACT_REQ', 'SENS_REQ', 'MCU_EN',
             'ACT_PERMIT', 'WHEEL_RUN_REQ', 'WHEEL_VM_OK')
    for bits in itertools.product((False, True), repeat=8):
        src = dict(zip(names, bits)); src.update(WHEEL_PWM_A=True, WHEEL_PWM_B=True, WHEEL_PWM_C=True)
        n = logic(boards, src)
        expected = not src['CC_OUT1'] and all(src[k] for k in names[2:])
        assert n['WHEEL_RUN_EN'] == expected
        assert all(n[x] == expected for x in ('DRV_INHA', 'DRV_INHB', 'DRV_INHC'))
        assert n['SOURCE_3A'] == (not src['CC_OUT1'] and not src['CC_OUT2'])
        count += 1
    return count


def heartbeat_checks(boards):
    # Event-driven retriggerable one-shot: B rising OR CLR rising with B high.
    nominal = value(boards['Upper'][0]['R46']) * value(boards['Upper'][0]['C27'])
    results = []
    for factor in (.7, 1, 1.5):  # selected stresses, NOT guaranteed timing corners
        timeout = nominal * factor
        for mode in ('healthy', 'missing', 'stuck_high', 'stuck_low', 'clear', 'rearm_high'):
            events = [(0., 'clear', True)]
            if mode in ('healthy', 'missing', 'clear'):
                stop = .080 if mode == 'healthy' else .040
                for t in np.arange(.001, stop + 1e-8, .001):
                    events += [(float(t), 'b', True), (float(t+.0002), 'b', False)]
            elif mode in ('stuck_high', 'rearm_high'):
                events += [(0.001, 'b', True)]
            if mode == 'clear': events += [(.0205, 'clear', False)]
            if mode == 'rearm_high': events += [(.005, 'clear', False), (.020, 'clear', True)]
            b = False; clear = False; expiry = -1.; edges = []; last = False
            # Poll only to record interlock output; all trigger timestamps are exact.
            events.sort(); pos = 0
            for t in np.arange(0, .100001, .00001):
                while pos < len(events) and events[pos][0] <= t + 1e-12:
                    et, typ, state = events[pos]; pos += 1
                    if typ == 'clear':
                        if state and not clear and b: expiry = et + timeout
                        clear = state
                        if not clear: expiry = -1.
                    else:
                        if state and not b and clear: expiry = et + timeout
                        b = state
                q = clear and t < expiry - 1e-12
                n = logic(boards, dict(CC_OUT1=False, CC_OUT2=True, ACT_REQ=True,
                          SENS_REQ=True, MCU_EN=True, ACT_PERMIT=q, WHEEL_RUN_REQ=True,
                          WHEEL_VM_OK=True, WHEEL_PWM_A=True, WHEEL_PWM_B=True, WHEEL_PWM_C=True))
                on = n['WHEEL_RUN_EN']
                if on != last: edges.append([round(float(t)*1e3, 5), on]); last = on
            rises = [t for t, on in edges if on]; falls = [t for t, on in edges if not on]
            if mode == 'stuck_low': assert not rises
            elif mode == 'clear': assert abs(falls[0]-20.5) < .011
            elif mode == 'rearm_high': assert len(rises) == 2 and abs(rises[1]-20) < .011
            else:
                assert len(rises) == 1 and len(falls) == 1
                last_edge = 80 if mode == 'healthy' else 40 if mode == 'missing' else 1
                assert abs(falls[0] - last_edge - timeout*1000) < .011
            results.append({'case': mode, 'assumed_timeout_ms': timeout*1000, 'edges_ms': edges})
    return results


def pwl(points):
    return 'PWL(' + ' '.join(f'{t:.10g} {v:.10g}' for t, v in points) + ')'


def edges(t, v, rising=True, level=2.):
    a = v > level
    return t[np.flatnonzero((a[1:] & ~a[:-1]) if rising else (~a[1:] & a[:-1]))+1]


def simulate(engine, name, deck, vectors, stop):
    cached=WORK/(name+'.npz'); circuit=WORK/(name+'.cir')
    if '--reuse' in sys.argv and cached.exists() and circuit.read_text()==deck:
        with np.load(cached) as a:d={v:a[v].copy() for v in ['time']+vectors}
        assert d['time'][-1]>=stop-1e-8 and all(np.all(np.isfinite(v)) for v in d.values())
        return d
    (WORK / (name+'.cir')).write_text(deck)
    engine.run(deck)
    (WORK / (name+'.log')).write_text('\n'.join(engine.log))
    d = {'time': engine.vector('time')}
    d.update({v: engine.vector(v) for v in vectors})
    assert d['time'][-1] >= stop - 1e-8, (name, 'unfinished transient')
    assert all(np.all(np.isfinite(v)) for v in d.values()), name
    np.savez_compressed(WORK / (name+'.npz'), **d)
    return d


def supervisor(engine, model, boards):
    c = boards['Wheel'][0]
    scenarios = {
        'startup': ([(0, 0), (.025, 5.05)], [(0, 0), (.001, 0), (.001001, 3.3)], None),
        'abrupt_droop': ([(0, 5.05), (.06, 5.05), (.060001, 4), (.085, 4), (.085001, 5.05)], [(0, 3.3)], None),
        'slow_droop': ([(0, 5.05), (.06, 5.05), (.08, 4.2), (.10, 4.2), (.12, 5.05)], [(0, 3.3)], None),
        'repeated_crossings': ([(0,5.05),(.06,5.05)]+[(.060001+i*.002,4.3 if i%2==0 else 5.05) for i in range(12)], [(0,3.3)], None),
        'manual_reset': ([(0,5.05)], [(0,3.3),(.06,3.3),(.060001,0),(.085,0),(.085001,3.3)], None),
        'no_permission': ([(0,0),(.025,5.05)], [(0,0)], None),
        'recovery_without_heartbeat': ([(0,5.05),(.06,5.05),(.060001,4),(.085,4),(.085001,5.05)], [(0,3.3),(.07,3.3),(.070001,0)], None),
        'recovery_without_run': ([(0,5.05),(.06,5.05),(.060001,4),(.085,4),(.085001,5.05)], [(0,3.3)], [(0,3.3),(.07,3.3),(.070001,0)]),
        'short_5us_dip': ([(0,5.05),(.06,5.05),(.0600001,4),(.0600051,4),(.0600052,5.05)], [(0,3.3)], None),
    }
    results = []; waves = {}
    for name, (rail, mr, run) in scenarios.items():
        # Actual interlock starts low while host power rises. Do not drive MR
        # high from an imaginary external source before the host rail exists.
        if mr[0] == (0,3.3):
            mr=[(0,0),(.001,0),(.001001,3.3)]+mr[1:]
        stop=.16 if name=='slow_droop' else .06 if name in ('startup','no_permission') else .13
        measured = []
        for dt in (2e-6, 1e-6):
            deck = f'''TI TPS3808G01 with actual external network: {name}
.include "{model.resolve().as_posix()}"
Vdd vdd 0 PWL(0 0 100u 3.3)
Vrail rail 0 {pwl(rail)}
Vmr mr 0 {pwl(mr)}
Vrequest request 0 {pwl(run or [(0,3.3)])}
Rtop rail sense {value(c['R147'])}
Rbottom sense 0 {value(c['R148'])}
Cs sense 0 {value(c['C102'])}
Rpull vdd reset {value(c['R149'])}
Creset reset 0 50p
Xsupervisor reset mr vdd sense ct TPS3808G01
Benable enabled 0 V={{(v(reset)>2 && v(mr)>2 && v(request)>2 && v(vdd)>2.7) ? 3.3 : 0}}
Renable enabled 0 {value(c['R150'])}
.options method=gear reltol=0.001 itl4=200 gmin=1e-10
.save v(rail) v(sense) v(reset) v(mr) v(enabled)
.tran {dt} {stop} 0 {dt}
.end
'''
            d = simulate(engine, f'supervisor-{name}-{dt*1e6:g}us', deck,
                         ['v(rail)','v(sense)','v(reset)','v(mr)','v(enabled)'], stop)
            t = d['time']; v = d['v(enabled)']; rise = edges(t,v); fall = edges(t,v,False)
            # Startup logic below 2.7 V deliberately excluded; real GPIO startup is a bench item.
            if name == 'no_permission': assert not len(rise)
            else:
                assert len(rise) >= 1
                assert rise[0] >= .013, (name,'initial recovery delay missing',rise)
                if name != 'startup':assert .013 <= rise[0] <= .029
            if name in ('abrupt_droop','slow_droop','repeated_crossings','manual_reset'):
                assert len(rise)==2 and len(fall)==1 and v[-1]>2, (name,rise,fall)
            if name.startswith('recovery_without'):
                assert len(rise)==1 and len(fall)==1 and v[-1]<.8
            delay = None
            if name == 'abrupt_droop':
                delay = float(fall[0] - .06)*1e6
            measured.append({'max_step_us':dt*1e6,'rise_ms':(rise*1e3).tolist(),
                             'fall_ms':(fall*1e3).tolist(),'dip_to_disable_us':delay})
            if dt == 1e-6: waves[name] = d
        for k in ('rise_ms','fall_ms'):
            a,b = np.array(measured[0][k]), np.array(measured[1][k])
            assert len(a)==len(b) and np.all(np.abs(a-b)<.02), (name,k,a,b)
        results.append({'case':name,'runs':measured,'timestep_check':'edge times agree within 20 us'})
        print('Supervisor',name,'passed',measured[-1],flush=True)
    return results,waves


def corners_and_bias(boards):
    c = boards['Wheel'][0]; rt=value(c['R147']); rb=value(c['R148']); cf=value(c['C102'])
    corners=[]
    for temp, a,b,ref,leak,hys in itertools.product((-40,25,85,125),(-1,1),(-1,1),(-.02,.02),(-25e-9,25e-9),(0,.03)):
        tol=.001+25e-6*abs(temp-25); top=rt*(1+a*tol); bot=rb*(1+b*tol)
        fall=.405*(1+ref)*(1+top/bot)+leak*top
        rise=fall+.405*(1+ref)*hys*(1+top/bot)
        corners.append([fall,rise])
    a=np.array(corners); minimum=float(a[:,0].min()); maximum=float(a[:,1].max())
    # Sweep selected assertion delay stresses and 1 nF +/-10% filter. Not guaranteed delays.
    dynamic=[]
    for slope,delay,cap in itertools.product((1,100,1000,10000),(20e-6,100e-6),(.9,1.1)):
        tau=(rt*rb/(rt+rb))*cf*cap
        # For a settled linear fall, filter lag = slope*tau.
        vm=minimum-slope*(tau+delay)-.008352  # reviewed shared feed error at 2 A/125 C
        dynamic.append({'slope_V_per_s':slope,'assumed_delay_us':delay*1e6,
                        'cap_factor':cap,'screened_VM_at_disable_V':vm,
                        'above_4V5':vm>=4.5})
    bias=[]
    for ref,net in [('R144','CS_DRV8316'),('R145','CS_ADC2')]:
        lower, pins=boards['Lower']; pull=[]
        for r,v in lower.items():
            if r.startswith('R') and {pins.get((r,'1')),pins.get((r,'2'))}=={net,'+3V3'}:pull.append((r,value(v)))
        assert len(pull)==1
        up=pull[0][1]; down=value(c[ref]); voltages=[]
        for v,ru,rd,leak in itertools.product((3.135,3.465),(up*.99,up*1.01),(down*.99,down*1.01),(-10e-6,10e-6)):
            voltages.append((v/ru-leak)/(1/ru+1/rd))
        bias.append({'net':net,'up_ref':pull[0][0],'down_ref':ref,
                     'nominal_V':3.3*down/(up+down),'min_V':min(voltages),
                     'margin_over_2V_V':min(voltages)-2,
                     'assumptions':'3V3 +/-5%, resistors +/-1%, aggregate input leakage +/-10 uA; leakage is selected screening allowance.'})
    assert all(x['margin_over_2V_V']>0 for x in bias)
    return {'threshold_corner_count':len(corners),'minimum_falling_V':minimum,
            'maximum_recovery_threshold_V':maximum,'filter_nominal_tau_us':rt*rb/(rt+rb)*cf*1e6,
            'droop_sensitivity':dynamic,'CS_bias':bias,
            'nSLEEP':'UNVERIFIED: no applicable transistor/powered-off leakage model located. Ground-referenced absolute maximum is not an Ioff guarantee.'}


def main():
    WORK.mkdir(parents=True,exist_ok=True); OUT.mkdir(exist_ok=True)
    boards,caps,sources=inputs(); model=models()
    count=gate_checks(boards); hb=heartbeat_checks(boards); analytic=corners_and_bias(boards)
    engine=Engine(KICAD/'ngspice.dll')
    sup,waves=supervisor(engine,model,boards)
    from startup import run as startup, coupled, behavioral_recovery
    supply,supply_waves=startup(engine,boards,caps,simulate,value)
    combined,combined_waves=coupled(engine,model,boards,simulate,value,WORK)
    recovery,recovery_waves=behavioral_recovery(caps)
    report={'status':'Simulation screening completed; bench acceptance remains UNVERIFIED',
            'gate_combinations':count,'heartbeat_cases':hb,'supervisor':sup,
            'startup':supply,'coupled_supply_supervisor':combined,
            'behavioral_recovery':recovery,'analytical':analytic}
    dump(OUT/'validation.json',report)
    fig,axes=plt.subplots(3,1,figsize=(11,9),layout='constrained')
    for ax,name in zip(axes,('startup','abrupt_droop','recovery_without_heartbeat')):
        d=waves[name];t=d['time']*1000
        ax.plot(t,d['v(rail)'],label='ACT_5V (imposed)');ax.plot(t,d['v(sense)']*11.5,label='Filtered sense, rail equivalent')
        ax.plot(t,d['v(enabled)'],label='Qualified enable');ax.axhline(4.5,color='red',ls=':',label='Driver 4.5 V minimum')
        ax.set(title=name.replace('_',' '),xlabel='Time (ms)',ylabel='Voltage (V)');ax.grid(alpha=.2)
    axes[0].legend(ncol=2);fig.suptitle('TI supervisor model + actual passive network; imposed supply waveforms')
    fig.savefig(OUT/'supervisor.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(11,7),layout='constrained')
    for name in ('default_boot_assumed_80mA','default_configured_assumed_400mA','default_overload_control_600mA'):
        d=supply_waves[name];t=d['time']*1000
        axes[0].plot(t,d['v(pwr)'],label=name);axes[1].plot(t,-d['i(vusb)'],label=name)
    axes[0].set(ylabel='Protected rail (V)',title='Averaged supply model with prescribed loads; not MCU boot simulation')
    axes[1].set(ylabel='USB input current (A)',xlabel='Time (ms)')
    axes[1].axhline(.1,color='red',ls=':',label='100 mA pre-configuration target')
    for ax in axes:ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.savefig(OUT/'startup.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(11,7),layout='constrained')
    for ax,(name,d) in zip(axes,combined_waves.items()):
        ax.plot(d['time']*1000,d['v(act)'],label='Local motor rail')
        ax.plot(d['time']*1000,d['v(enabled)'],label='Qualified motor enable')
        ax.axhline(4.6575,color='red',ls=':',label='Nominal trip threshold')
        ax.set(xlim=(95,200),xlabel='Time (ms)',ylabel='Voltage (V)',title=name.replace('_',' '))
        ax.grid(alpha=.2);ax.legend()
    fig.suptitle('UNQUALIFIED recovery discrepancy: TI model, 250 mA logic + 1 A load, 0.15 ohm cable')
    fig.savefig(OUT/'recovery.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(11,7),layout='constrained')
    for ax,(name,d) in zip(axes,recovery_waves.items()):
        ax.plot(d[:,0]*1000,d[:,1],label='Local rail');ax.plot(d[:,0]*1000,d[:,2],label='Motor enable')
        ax.axhline(4.6575,color='red',ls=':',label='Nominal trip')
        ax.set(title=name.replace('_',' '),xlabel='Time since settled rail (ms)',ylabel='Voltage (V)')
        ax.grid(alpha=.2);ax.legend()
    fig.suptitle('Behavioral recovery law, assumed 20 us assertion; potential retry behavior, not firmware execution')
    fig.savefig(OUT/'behavioral-recovery.png',dpi=150);plt.close(fig)
    dump(OUT/'local-artifacts.json',{f.relative_to(ROOT).as_posix():sha(f)
        for f in WORK.glob('*') if f.suffix in ('.cir','.npz') and f.name.startswith(('supervisor-','startup-','coupled-'))})
    assert all(sha(ROOT/f)==h for f,h in sources.items()),'Production sources changed during simulation'
    print('All source hashes preserved; compact results saved.',flush=True)


if __name__=='__main__': main()
