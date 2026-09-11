"""Run native and electrical checks against the current bench source snapshot."""
import json
from pathlib import Path
import subprocess
import sys
from build_panel import HERE, ROOT, SOURCES, sha, save_json

CLI=Path(sys.executable).with_name('kicad-cli.exe')
OUT=HERE/'package/evidence'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
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
        (OUT/(name+'-drc.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        assert result.returncode==0,(name,result.stderr)
        data=json.loads(report.read_text())
        for key in ('violations','unconnected_items','schematic_parity'):
            assert not data.get(key), (name,key,len(data[key]))
        checks.append(name+' native DRC/connectivity'+('/parity' if name!='Panel' else ''))
    for name,script,extra in jobs:
        command=[sys.executable,str(ROOT/script),'--board',str(SOURCES['Main']),
                 '--output',str(OUT/(name+'.json')),*extra]
        result=subprocess.run(command,capture_output=True,text=True)
        (OUT/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        assert result.returncode==0,(name,result.stdout,result.stderr)
        checks.append(name)
    assert initial=={n:sha(path) for n,path in SOURCES.items()},'Sources changed during verification'
    save_json(OUT/'acceptance.json',dict(cad_checks='PASS',checks=checks,source_sha256=initial,
        panel_sha256=sha(HERE/'Panel.kicad_pcb'),manufacturing_ready=False,
        limits='Geometric/electrical CAD screening only. Open supplier, bench mechanical, assembly and CAM gates remain in README.'))
    print('Passed',len(checks),'native/electrical checks; manufacturing release remains blocked by open gates')


if __name__=='__main__':main()
