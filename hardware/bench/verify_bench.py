"""Run native and electrical checks against the current bench source snapshot."""
import json
import os
import uuid
from pathlib import Path
import subprocess
import sys
from build_panel import HERE, ROOT, SOURCES, sha, save_json, atomic_text

CLI=Path(sys.executable).with_name('kicad-cli.exe')
DEST=HERE/'package/evidence'
OUT=ROOT/'build/verification-staging'/str(uuid.uuid4())


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    DEST.mkdir(parents=True,exist_ok=True)
    initial={n:sha(path) for n,path in SOURCES.items()}
    checks=[]
    jobs=[('main-analog','hardware/modular/verify_main_analog.py',['--require-reviewed']),
          ('main-routing','hardware/modular/verify_main_routing.py',['--require-reviewed']),
          ('main-usb','hardware/kicad/verify_usb_layout.py',[]),
          ('main-power','hardware/modular/verify_main_power.py',[]),
          ('main-controls','hardware/modular/verify_main_controls.py',[])]
    for name,path in {**SOURCES,'Panel':HERE/'Panel.kicad_pcb'}.items():
        report=OUT/(name+'-drc.json')
        command=[str(CLI),'pcb','drc','--format','json','--output',str(report)]
        if name!='Panel':command+=['--schematic-parity']
        command+=[str(path)]
        result=subprocess.run(command,capture_output=True,text=True)
        atomic_text(OUT/(name+'-drc.log'),result.stdout+result.stderr)
        assert result.returncode==0,(name,result.stderr)
        data=json.loads(report.read_text())
        for key in ('violations','unconnected_items','schematic_parity'):
            assert not data.get(key), (name,key,len(data[key]))
        checks.append(name+' native DRC/connectivity'+('/parity' if name!='Panel' else ''))
    for name,script,extra in jobs:
        command=[sys.executable,str(ROOT/script),'--board',str(SOURCES['Main']),
                 '--output',str(OUT/(name+'.json')),*extra]
        result=subprocess.run(command,capture_output=True,text=True)
        atomic_text(OUT/(name+'.log'),result.stdout+result.stderr)
        assert result.returncode==0,(name,result.stdout,result.stderr)
        checks.append(name)
    wheel=subprocess.run([sys.executable,str(ROOT/'hardware/modular/verify_wheel_routing.py'),
        '--board',str(SOURCES['Wheel']),'--output',str(OUT/'wheel-routing.json')],capture_output=True,text=True)
    atomic_text(OUT/'wheel-routing.log',wheel.stdout+wheel.stderr)
    assert wheel.returncode==0,('wheel-routing',wheel.stdout,wheel.stderr)
    checks.append('wheel-routing')
    for name,path in SOURCES.items():
        result=subprocess.run([sys.executable,str(HERE/'repair_copper_joins.py'),str(path),
            '--output',str(OUT/(name+'-copper-entries.json'))],capture_output=True,text=True)
        atomic_text(OUT/(name+'-copper-entries.log'),result.stdout+result.stderr)
        assert result.returncode==0,(name,'Copper entry audit',result.stdout,result.stderr)
        checks.append(name+' all-layer track/pad/via entries')
    result=subprocess.run([sys.executable,str(HERE/'contact_review.py'),'--output',str(OUT/'contact-inventory.json')],capture_output=True,text=True)
    atomic_text(OUT/'contact-inventory.log',result.stdout+result.stderr)
    assert result.returncode==0,('Local zone/element review',result.stdout,result.stderr)
    checks.append('All boards local zone entries and per-layer element inventory')
    assert initial=={n:sha(path) for n,path in SOURCES.items()},'Sources changed during verification'
    save_json(OUT/'acceptance.json',dict(cad_checks='PASS',checks=checks,source_sha256=initial,
        panel_sha256=sha(HERE/'Panel.kicad_pcb'),manufacturing_ready=False,
        limits='Geometric/electrical CAD screening only. Open supplier, bench mechanical, assembly and CAM gates remain in README.'))
    for report in OUT.iterdir():os.replace(report,DEST/report.name)
    print('Passed',len(checks),'native/electrical checks; manufacturing release remains blocked by open gates')


if __name__=='__main__':main()
