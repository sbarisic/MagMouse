# SPDX-License-Identifier: GPL-3.0-or-later
"""Recompute saved waveform measurements and verify evidence/source hashes."""
import hashlib
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=HERE/'results'
WORK=ROOT/'build/power-validation'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def edges(t,v,rise):
    on=v>2
    return t[np.flatnonzero((on[1:] & ~on[:-1]) if rise else (~on[1:] & on[:-1]))+1]*1000


def main():
    report=json.loads((OUT/'validation.json').read_text())
    inputs=json.loads((OUT/'inputs.json').read_text())
    for f,h in inputs['source_sha256'].items():assert sha(ROOT/f)==h,f
    models=json.loads((OUT/'models.json').read_text())
    for name in ('tps3808','tps25947'):
        assert sha(WORK/'models'/(name+'.zip'))==models[name]['archive_sha256']
        assert sha(WORK/'models'/(name+'-original.lib'))==models[name]['library_sha256']
    assert sha(WORK/'models/tps3808-ngspice.lib')==models['tps3808']['adapted_sha256']
    assert sha(Path(models['engine']['path']))==models['engine']['sha256']
    artifacts=json.loads((OUT/'local-artifacts.json').read_text())
    for f,h in artifacts.items():assert sha(ROOT/f)==h,f
    assert report['gate_combinations']==256 and len(report['heartbeat_cases'])==18
    assert len(report['supervisor'])==9 and len(report['startup'])==8
    assert len(report['behavioral_recovery'])==8
    checked=0
    for row in report['supervisor']:
        for run in row['runs']:
            f=WORK/f"supervisor-{row['case']}-{run['max_step_us']:g}us.npz"
            with np.load(f) as d:
                t=d['time'];v=d['v(enabled)']
                for rise,key in [(True,'rise_ms'),(False,'fall_ms')]:
                    assert np.allclose(edges(t,v,rise),run[key],atol=1e-9)
                if row['case']=='no_permission':assert not np.any(v>2)
                if row['case'].startswith('recovery_without'):assert not np.any(v[t>.09]>2)
            checked+=1
    for row in report['startup']:
        for run in row['runs']:
            with np.load(WORK/f"startup-{row['case']}-{run['max_step_us']:g}us.npz") as d:
                assert abs(float((-d['i(vusb)']).max())-run['peak_USB_A'])<1e-9
                assert abs(float(d['v(pwr)'][-1])-run['final_PWR_5V_V'])<1e-9
            checked+=1
    discrepancies=[];excluded=[]
    for row in report['coupled_supply_supervisor']:
        if not row['accepted_as_hardware_prediction']:excluded.append(row['case'])
        for run in row['runs']:
            with np.load(WORK/f"coupled-{row['case']}-{run['max_step_us']:g}us.npz") as d:
                assert np.allclose(edges(d['time'],d['v(enabled)'],True),run['enable_rises_ms'],atol=1e-9)
            checked+=1
        if not row['numerically_converged'] or row['datasheet_recovery_contract_met'] is False:
            discrepancies.append(row['case'])
            assert row['accepted_as_hardware_prediction'] is False
    with np.load(WORK/'supervisor-abrupt_droop-1us.npz') as d:
        mask=(d['v(rail)']<4.5)&(d['v(enabled)']>2)
        below=float(np.trapezoid(mask.astype(float),d['time'])*1e6)
    summary={'status':'Evidence consistent; hardware acceptance remains UNVERIFIED',
             'production_sources_unchanged':True,'waveform_runs_recomputed':checked,
             'supplier_model_cases_excluded_from_hardware_prediction':excluded,
             'unresolved_supplier_model_recovery_discrepancies':discrepancies,
             'abrupt_droop_enabled_below_4V5_duration_us':below,
             'all_expected_fault_controls_detected':True,
             'nSLEEP_powered_off_leakage':'UNVERIFIED; no applicable leakage model',
             'actual_ROM_boot_and_USB_startup_current':'UNVERIFIED; prescribed loads only'}
    summary['study_code_sha256']={f.name:sha(f) for f in HERE.glob('*.py')}
    faults={x['case']:x for x in report['startup']}
    assert faults['missing_R35_fault_control']['runs'][-1]['final_PWR_5V_V']<.1
    assert faults['default_overload_control_600mA']['runs'][-1]['final_PWR_5V_V']<4.4
    (OUT/'review.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
