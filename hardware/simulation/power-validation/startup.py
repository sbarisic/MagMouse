# SPDX-License-Identifier: GPL-3.0-or-later
"""Averaged, current-limited rail study. No claim to simulate MCU boot."""
import itertools
import numpy as np


def run(engine, boards, caps, simulate, value):
    upper = boards['Upper'][0]
    usb_top = sum(value(upper[r]) for r in ('R31','R32','R33','R34'))
    usb_bottom = value(upper['R35'])
    act_top = sum(value(upper[r]) for r in ('R36','R37','R38'))
    act_bottom = value(upper['R39'])
    base = sum(value(upper[r]) for r in ('R56','R57','R58'))
    conductance = [1/base, 1/base+1/value(upper['R59']),
                   1/base+sum(1/value(upper[r]) for r in ('R59','R60','R61'))]
    limits = [3334*g for g in conductance]
    actuator_limit = 3334*(1/value(upper['R42'])+1/value(upper['R43']))
    cases = [
        ('default_boot_assumed_80mA',0,5.0,.15,.08,0,1,False),
        ('default_configured_assumed_400mA',0,5.0,.15,.40,0,1,False),
        ('default_overload_control_600mA',0,5.0,.15,.60,0,1,False),
        ('typec_1A5_logic250mA_motor500mA',1,5.0,.15,.25,.50,1,False),
        ('typec_3A_logic250mA_motor1A',2,5.0,.15,.25,1.,1,False),
        ('weak_source_logic250mA_motor500mA',1,4.75,.50,.25,.50,1,False),
        ('low_effective_capacitance',1,5.0,.15,.25,.50,.4,False),
        ('missing_R35_fault_control',0,5.0,.15,.08,0,1,True),
    ]
    results=[]; waves={}
    for name,mode,voltage,cable,logic,motor,cap_factor,missing in cases:
        runs=[]
        for dt in (4e-6,2e-6):
            # Copper figures copied from current contact-graph report and guarded below.
            # Extra 30 mOhm is an ASSUMED harness/return allowance, not measured.
            r_usb=.0283+.007600+.005779
            r_act=.0283+.046819+.035732+.036235+.030
            cp=caps['PWR_5V']['nominal_F']*cap_factor
            ca=caps['ACT_5V']['nominal_F']*cap_factor
            c3=caps['+3V3']['nominal_F']*cap_factor
            deck=f'''Averaged power startup {name}; NOT vendor eFuse or buck model
Vusb source 0 PWL(0 0 1m {voltage})
Rcable source vbus {cable}
Cinput vbus 0 {caps['VBUS_USB']['nominal_F']}
Ruvtop vbus uv {value(upper['R29'])}
Ruvbot uv 0 {value(upper['R30'])}
Vone one 0 1
Suv one uvok uv 0 UVLO
Ruvok uvok 0 1k
.model UVLO SW(Ron=1 Roff=1e9 Vt=1.145 Vh=.055)
Rovtop vbus ov {usb_top}
Rovbot ov 0 {1e12 if missing else usb_bottom}
Vramp ramp 0 PWL(0 0 1m 0 28.5m 5.5)
Busb vbus pwr I={{(v(uvok)>.5 && v(ov)<1.2) ? max(0,min({limits[mode]},(min(v(vbus),v(ramp))-v(pwr))/{r_usb})) : 0}}
Cpwr pwr 0 {cp}
Rdischarge pwr 0 100k
* Prescribed equivalent load at PWR_5V; its actual boot waveform is unknown.
Blogic pwr 0 I={{{logic}*min(1,max(0,v(pwr)/4.5))}}
* Ideal averaged 3V3 conversion, 85% efficiency during capacitor charging only.
* Continuous logic consumption is already included in Blogic above.
Bv3 v3 0 V={{min(3.3,max(0,v(pwr)-.5))}}
Vcap3 v3 cap3 0
C3 cap3 0 {c3}
Bcharge pwr 0 I={{max(0,v(v3)*i(Vcap3))/(.85*max(v(pwr),.5))}}
Vactrequest permit 0 PWL(0 0 60m 0 60.001m {3.3 if mode else 0})
Racttop pwr actuv {act_top}
Ractbottom actuv 0 {act_bottom}
Sactuv one actuvok actuv 0 UVLO
Ractuvok actuvok 0 1k
* D3's clamp is represented by permit gating; no diode leakage prediction.
Vactramp actramp 0 PWL(0 0 60m 0 87.5m 5.5)
Bact pwr act I={{(v(permit)>2 && v(actuvok)>.5 && v(pwr)<6.63) ? max(0,min({actuator_limit},(min(v(pwr),v(actramp))-v(act))/{r_act})) : 0}}
Cact act 0 {ca}
Ractbleed act 0 100k
* Constant-current-equivalent demand with resistive rolloff below 4.5 V.
* Deliberately does not remove the load on supervisor trip: adverse rail screen.
Bmotor act 0 I={{{motor}*min(1,max(0,v(act)/4.5))}}
.options method=gear reltol=0.0001 itl4=200
.save v(pwr) v(act) v(vbus) v(v3) i(vusb) @busb[i] @bact[i] @blogic[i] @bcharge[i]
.tran {dt} .15 0 {dt}
.end
'''
            names=['v(pwr)','v(act)','v(vbus)','v(v3)','i(vusb)','@busb[i]','@bact[i]','@blogic[i]','@bcharge[i]']
            d=simulate(engine,f'startup-{name}-{dt*1e6:g}us',deck,names,.15)
            t=d['time']; current=-d['i(vusb)']; final=d['v(pwr)'][-1]
            balance=np.trapezoid(d['@busb[i]']-d['@bact[i]']-d['@blogic[i]']-d['@bcharge[i]']-d['v(pwr)']/100000-d['v(pwr)']/(act_top+act_bottom),t)
            stored=cp*(final-d['v(pwr)'][0])
            err=abs(balance-stored)
            assert err<max(1e-6,.02*abs(stored)),(name,'KCL error',err,stored)
            row={'max_step_us':dt*1e6,'peak_USB_A':float(current.max()),
                 'settled_USB_A':float(np.mean(current[t>.14])),
                 'final_PWR_5V_V':float(final),'final_ACT_5V_V':float(d['v(act)'][-1]),
                 'PWR_charge_balance_error_C':float(err),
                 'U12_nominal_limit_A':limits[mode]}
            runs.append(row)
            if dt==2e-6:waves[name]=d
        assert abs(runs[0]['final_PWR_5V_V']-runs[1]['final_PWR_5V_V'])<.01
        assert abs(runs[0]['peak_USB_A']-runs[1]['peak_USB_A'])<.01
        if missing:assert runs[-1]['final_PWR_5V_V']<.1
        elif 'overload' not in name and 'weak' not in name:assert runs[-1]['final_PWR_5V_V']>4.4
        if 'overload' in name:assert runs[-1]['final_PWR_5V_V']<4.4
        results.append({'case':name,'assumptions':{'source_V':voltage,'cable_loop_ohm':cable,
                        'logic_equivalent_A':logic,'motor_equivalent_A':motor,'capacitance_factor':cap_factor},
                        'runs':runs,'qualification':'Load envelope only; actual ROM/application boot current not simulated.'})
        print('Startup',name,runs[-1],flush=True)
    return results,waves


def coupled(engine, model, boards, simulate, value, work):
    """Adverse repeated-load experiment; motor is a load step, not a motor model."""
    c=boards['Wheel'][0]; results=[]; waves={}
    base=(work/'startup-typec_3A_logic250mA_motor1A-2us.cir').read_text()
    for mode in ('held_request','request_cleared_110ms'):
        runs=[]
        for dt in (1e-6,.5e-6):
            deck=base.replace('Bmotor act 0 I={1.0*min(1,max(0,v(act)/4.5))}',
                'Bmotor act 0 I={(v(good)>2 && v(request)>2) ? min(1,max(0,v(act)/4.5)) : 0}')
            assert deck!=base,'Load replacement failed'
            req='PWL(0 3.3 .11 3.3 .110001 0)' if mode!='held_request' else '3.3'
            extra=f'''
.include "{model.resolve().as_posix()}"
Rtop act sense {value(c['R147'])}
Rbot sense 0 {value(c['R148'])}
Csense sense 0 {value(c['C102'])}
Rgood v3 good {value(c['R149'])}
Cgood good 0 50p
Xsupervisor good permit v3 sense ct TPS3808G01
Vrequest request 0 {req}
Benable enabled 0 V={{(v(good)>2 && v(request)>2 && v(permit)>2) ? 3.3 : 0}}
.save v(good) v(sense) v(enabled)
'''
            deck=deck.replace('.options method=gear reltol=0.0001 itl4=200',
                              '.options method=gear reltol=0.001 itl4=200 gmin=1e-10')
            deck=deck.replace('.tran 2e-06 .15 0 2e-06',f'.tran {dt} .20 0 {dt}')
            deck=deck.replace('.end',extra+'\n.end')
            d=simulate(engine,f'coupled-{mode}-{dt*1e6:g}us',deck,
                ['v(act)','v(pwr)','v(enabled)','v(good)','v(sense)','i(vusb)'],.20)
            t=d['time'];on=d['v(enabled)']>2
            rises=t[np.flatnonzero(on[1:] & ~on[:-1])+1]
            falls=t[np.flatnonzero(~on[1:] & on[:-1])+1]
            assert len(rises)>=1 and len(falls)>=1
            if mode!='held_request':assert not np.any(on[t>.11001]),'Run-request removal failed'
            row={'max_step_us':dt*1e6,'enable_rises_ms':(rises*1000).tolist(),
                 'enable_falls_ms':(falls*1000).tolist(),
                 'minimum_VM_while_enabled_V':float(d['v(act)'][on].min())}
            runs.append(row)
            if dt==.5e-6:waves[mode]=d
        converged=len(runs[0]['enable_rises_ms'])==len(runs[1]['enable_rises_ms'])
        if converged:converged=bool(np.max(np.abs(np.array(runs[0]['enable_rises_ms'])-runs[1]['enable_rises_ms']))<.1)
        results.append({'case':mode,'runs':runs,'recovery_observed':len(runs[-1]['enable_rises_ms'])>1,
                        'numerically_converged':converged,
                        'datasheet_recovery_contract_met':len(runs[-1]['enable_rises_ms'])>=3 if mode=='held_request' else None,
                        'accepted_as_hardware_prediction':False,
                        'finding': 'UNRESOLVED model/datasheet short-dip recovery discrepancy; absence of retries is not evidence of a physical latch. Coarse 4/2 us runs did not agree. Do not use this case to qualify automatic recovery.'})
        print('Coupled',mode,runs[-1],flush=True)
    return results,waves


def behavioral_recovery(caps):
    """Independent datasheet state law; expose retries without trusting macro-model internals."""
    results=[]; waves={}
    for mode,delay,dt in itertools.product(('held_request','request_cleared_35ms'),(20e-6,100e-6),(2e-6,1e-6)):
        pwr=5-.25*(.15+.0283+.007600+.005779); act=pwr; sensed=act
        tau=105000*10000/115000*1e-9
        good=False; low=0.; high=0.; last=False; rises=[]; falls=[]; data=[]
        for t in np.arange(0,.1000001,dt):
            request=mode=='held_request' or t<.035
            if sensed<4.6575:
                low+=dt;high=0
                if low>=delay:good=False
            else:
                low=0
                if not good:
                    high=high+dt if sensed>4.6575*1.015 else 0
                    if high>=.020:good=True
            enabled=good and request
            if enabled!=last:
                (rises if enabled else falls).append(float(t)*1000);last=enabled
            iu=max(0,min(2.555703,(5-pwr)/(.15+.0283+.007600+.005779)))
            ia=max(0,min(2.020606,(pwr-act)/(.0283+.046819+.035732+.036235+.030)))
            load=(min(1,max(0,act/4.5)) if enabled else 0)
            pwr+=dt*(iu-ia-.25)/caps['PWR_5V']['nominal_F']
            act+=dt*(ia-load)/caps['ACT_5V']['nominal_F']
            sensed+=(act-sensed)*(1-np.exp(-dt/tau))
            data.append((float(t),act,3.3 if enabled else 0))
        if mode=='held_request':assert len(rises)>=3
        else:assert len(rises)==1 and all(t<35 for t in rises)
        data=np.array(data);on=data[:,2]>2
        results.append({'case':mode,'assumed_assertion_us':delay*1e6,'step_us':dt*1e6,
                        'rise_ms':rises,'fall_ms':falls,'min_VM_while_enabled_V':float(data[on,1].min())})
        if dt==1e-6 and delay==20e-6:waves[mode]=data
    for mode in ('held_request','request_cleared_35ms'):
        for delay in (20.,100.):
            rows=[r for r in results if r['case']==mode and r['assumed_assertion_us']==delay]
            assert len(rows[0]['rise_ms'])==len(rows[1]['rise_ms'])
            assert np.max(np.abs(np.array(rows[0]['rise_ms'])-rows[1]['rise_ms']))<.05
    return results,waves
