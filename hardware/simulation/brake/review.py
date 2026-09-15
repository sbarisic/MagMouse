# SPDX-License-Identifier: GPL-3.0-or-later
"""Validate saved numerical results and render the review report without rerunning SPICE."""
import csv
import json
import subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from run import HERE, ROOT, sha, inventory, analyze, circuit


def main():
    dest=HERE/'results'
    report=json.loads((dest/'summary.json').read_text())
    cases=report['cases']
    inv=inventory()
    # Recompute all reported measurements from saved raw waveforms, independently of stored metrics.
    for c in cases:
        config=c['configuration']; name=config['name']
        for step in (2e-7,1e-7):
            assert (dest/f'{name}_{step*1e9:g}ns.cir').read_text(encoding='utf-8')==circuit(inv,config,step), 'Stale circuit/model inputs'
        coarse=analyze(np.load(dest/f'{name}_200ns.npz')['data'],config,inv)
        fine=analyze(np.load(dest/f'{name}_100ns.npz')['data'],config,inv)
        c.update(fine)
        c['peak_timestep_delta_V']=abs(fine['peak_rail_V']-coarse['peak_rail_V'])
        c['delay_timestep_delta_us']=(abs(fine['max_brake_response_us']-coarse['max_brake_response_us'])
                                      if fine['max_brake_response_us'] is not None and coarse['max_brake_response_us'] is not None else None)
        c['energy_timestep_relative_delta']=abs(fine['resistor_bank_energy_J']-coarse['resistor_bank_energy_J'])/max(fine['resistor_bank_energy_J'],1e-9)
        c['numerical_checks_pass']=(c['energy_balance_relative_error']<.005 and c['peak_timestep_delta_V']<.005
                                  and (c['delay_timestep_delta_us'] is None or c['delay_timestep_delta_us']<.5)
                                  and c['energy_timestep_relative_delta']<.01)
    (dest/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    assert len(cases)==24, f'Incomplete case suite: {len(cases)}'
    assert inventory()==json.loads((dest/'inventory.json').read_text()), 'Stale input netlists'
    ordinary=[c for c in cases if not c['configuration'].get('diagnostic') and not c['configuration'].get('threshold_ramp')]
    assert all(c['numerical_checks_pass'] for c in cases), 'Numerical convergence/balance failure'
    assert all(c['below_6p5V'] for c in ordinary), 'Rail-voltage target failed'
    assert all(c['average_regeneration_W']<=.5 for c in cases if c['configuration']['name'].endswith('repeated'))
    controls=[c for c in cases if c['configuration'].get('diagnostic')]
    assert all(not c['below_6p5V'] for c in controls), 'Diagnostic controls did not expose missing/insufficient brake'
    ramp=next(c for c in cases if c['configuration'].get('threshold_ramp'))
    assert ramp['observed_on_V'] and ramp['observed_off_V'], 'Missing threshold transitions'
    assert abs(ramp['observed_on_V'][0]-report['thresholds']['ideal_on_V'])<.02
    assert abs(ramp['observed_off_V'][0]-report['thresholds']['ideal_off_V'])<.02
    # Changes are confined to this simulation directory. Compare exact bytes with saved commit.
    preserved={}
    for path in [ROOT/'hardware/modular/main/Main.kicad_pcb', ROOT/'hardware/modular/wheel/Wheel.kicad_pcb',
                 ROOT/'hardware/encoder/Encoder.kicad_pcb', ROOT/'hardware/bench/Panel.kicad_pcb',
                 ROOT/'hardware/bench/submissions/2026-09-12-jlc-cam/CAM-review-attachments.zip']:
        if not path.exists():
            if 'encoder' in str(path).lower():
                path=ROOT/'hardware/kicad/encoder/Encoder.kicad_pcb'
        relative=path.relative_to(ROOT).as_posix()
        old=subprocess.check_output(['git','show',f'145d2be:{relative}'],cwd=ROOT)
        assert old==path.read_bytes(), f'Production file changed: {relative}'
        preserved[relative]=sha(path)
    sources={'TLV1811':{'url':'https://www.ti.com/lit/zip/snom762','file':'models/tlv1811.lib','use':'Original convergence attempt only; not used in accepted sweep'},
             'LM4040':{'url':'https://www.ti.com/lit/zip/snom526','file':'models/lm4040.lib','use':'Unmodified TI reference subcircuit; native psa compatibility'},
             'AO3400A':{'url':'https://www.aosmd.com/products/mosfets/low-voltage-mosfets-12v-30v/ao3400a','use':'No manufacturer model located; Rds and gate-load approximation'}}
    for entry in sources.values():
        if 'file' in entry: entry['sha256']=sha(HERE/entry['file'])
    failures=[c['configuration']['name'] for c in ordinary if not c['response_within_10us']]
    (dest/'validation.json').write_text(json.dumps({'numerical_checks':'PASS','rail_target':'PASS',
        'response_target':'FAIL in delay-stress cases' if failures else 'PASS',
        'response_failures':failures,'production_files_unchanged':preserved,'model_sources':sources},indent=2)+'\n')
    fields=['name','peak_rail_V','max_brake_response_us','peak_brake_current_A','peak_resistor_bank_W',
            'resistor_bank_energy_J','average_regeneration_W','energy_balance_relative_error',
            'peak_timestep_delta_V','energy_timestep_relative_delta','below_6p5V','response_within_10us']
    with (dest/'metrics.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader()
        for c in cases: writer.writerow({key:c['configuration']['name'] if key=='name' else c[key] for key in fields})

    plt.rcParams.update({'font.size':10, 'axes.grid':True,'grid.alpha':.2})
    fig,axes=plt.subplots(2,2,figsize=(13,8),layout='constrained')
    def wave(name): return np.load(dest/f'{name}_100ns.npz')['data']
    for name,label in [('minimum_10us_repeated','47 uF, 10 us delay'),('nominal_10us_repeated','210.7 uF, 10 us delay')]:
        d=wave(name); axes[0,0].plot(d[:,0]*1e3,d[:,1],label=label)
    axes[0,0].axhline(6.5,color='red',ls='--',label='6.5 V target')
    axes[0,0].set(title='Repeated regeneration, 0.4 A pulses',xlabel='Time (ms)',ylabel='ACT_5V (V)',ylim=(4.8,6.65)); axes[0,0].legend()
    for name,label in [('minimum_0.45us_pulse','0.45 us delay'),('minimum_10us_pulse','10 us delay'),('threshold_high','High-threshold / gate-load stress')]:
        d=wave(name); axes[0,1].plot(d[:,0]*1e3,d[:,1],label=label)
    axes[0,1].set(title='First brake event, 47 uF',xlabel='Time (ms)',ylabel='ACT_5V (V)',xlim=(1.08,1.24),ylim=(5.6,6.4));axes[0,1].legend(fontsize=8)
    for name,label in [('brake_disabled','Brake disabled'),('excess_regeneration','1 A excess regeneration')]:
        d=wave(name); axes[1,0].plot(d[:,0]*1e3,d[:,1],label=label)
    axes[1,0].axhline(6.5,color='red',ls='--');axes[1,0].set(title='Diagnostic controls — TVS omitted',xlabel='Time (ms)',ylabel='Unclamped model voltage (V)');axes[1,0].legend()
    d=wave('threshold_ramp');axes[1,1].plot(d[:,0]*1e3,d[:,1],label='Rail')
    axes[1,1].plot(d[:,0]*1e3,d[:,4],label='Brake output')
    axes[1,1].axhline(report['thresholds']['ideal_on_V'],color='gray',ls='--')
    axes[1,1].axhline(report['thresholds']['ideal_off_V'],color='gray',ls=':')
    axes[1,1].set(title='Slow rail sweep: hysteresis',xlabel='Time (ms)',ylabel='Voltage (V)');axes[1,1].legend()
    fig.suptitle('MagMouse brake simulation — behavioral comparator/MOSFET, TI reference model',fontsize=14)
    fig.savefig(dest/'waveforms.png',dpi=170);fig.savefig(dest/'waveforms.svg');plt.close(fig)
    peak=max(c['peak_rail_V'] for c in ordinary)
    rows=['# ACT_5V brake simulation results','',
          f'24 cases, each run with 200 ns and 100 ns maximum timesteps. All numerical checks pass. Peak rail across the intended-current cases and selected tolerance stresses: **{peak:.4f} V**, below 6.5 V.', '',
          '**The 10 us response target is not met in every delay-stress case.** The swept delay is comparator transport delay; gate charging and the current measurement criterion add time. Response starts at the comparator input crossing its offset-adjusted threshold and ends at 0.4 A brake current. It excludes sensing-filter delay before that crossing. This is not a claim that the actual comparator takes 10 us.', '',
          f'Ideal thresholds from netlist resistors: {report["thresholds"]["ideal_on_V"]:.6f} V on / {report["thresholds"]["ideal_off_V"]:.6f} V off. Slow-ramp simulation: {ramp["observed_on_V"][0]:.6f} V / {ramp["observed_off_V"][0]:.6f} V.', '',
          '| Case | Peak V | Response us | Bank peak W | Bank energy mJ | Rail target |',
          '|---|---:|---:|---:|---:|---|']
    for c in cases:
        delay=c['max_brake_response_us']; response='n/a' if delay is None else f'{delay:.3f}'
        rows.append(f'| {c["configuration"]["name"]} | {c["peak_rail_V"]:.4f} | {response} | {c["peak_resistor_bank_W"]:.3f} | {c["resistor_bank_energy_J"]*1000:.3f} | {"PASS" if c["below_6p5V"] else "FAIL (diagnostic)"} |')
    rows+=['','Bank energy is integrated over the full listed scenario, not necessarily one switching pulse. Per-resistor power and energy are one quarter of the bank values for equal resistors. No resistor temperature or pulse-rating acceptance is inferred.', '',
           'Repeated pulses are 1 ms on / 6 ms period and have measured average input power below 0.5 W. The single-pulse window average can exceed 0.5 W; it is not a sustained operating point. Unplug occurs 50 us after regeneration starts, when the one-way upstream source is already blocked by the rising rail.', '',
           'The disabled/excess controls deliberately exceed the target. Because the TVS is omitted, their high voltages indicate inadequate brake absorption, not predicted hardware clamp voltages.', '',
           'See README.md for model assumptions, provenance, limitations and reproduction instructions. Production boards, panel and the submitted archive remain byte-identical to commit 145d2be.']
    (HERE/'RESULTS.md').write_text('\n'.join(rows)+'\n')
    paths=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='file-sha256.json']
    (dest/'file-sha256.json').write_text(json.dumps({p.relative_to(HERE).as_posix():sha(p) for p in sorted(paths)},indent=2)+'\n')
    print(f'PASS: {len(cases)} cases, peak {peak:.4f} V; {len(failures)} response stress failures retained.')


if __name__=='__main__': main()
