"""Native 2D copper/silkscreen plots of the complete panel, plus PNG previews."""
import hashlib,json,re,sys
from route_main import HERE,ROOT,CLI
sys.path.insert(0,str(ROOT/'build/two-layer/python'))
sys.path.insert(0,str(ROOT/'hardware/common'))
import resvg_py
from kicad_output import write as write_atomic, run as run_atomic

def main():
    folder=HERE/'panel';source=folder/'Panel.kicad_pcb'
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    before=sha(source);report={'source_sha256':before,'views':{}}
    for side,layers in [('top','F.Cu,F.SilkS,Edge.Cuts'),('bottom','B.Cu,B.SilkS,Edge.Cuts')]:
        svg=folder/('Panel-'+side+'.svg')
        run_atomic(CLI,['pcb','export','svg','--mode-single','--fit-page-to-board',
            '--exclude-drawing-sheet','--layers',layers,*(['--mirror'] if side=='bottom' else []),
            '-o',str(svg),str(source)],check=True)
        text='\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n'
        write_atomic(svg,text)
        text=re.sub(r'width="([\d.]+)mm" height="([\d.]+)mm"',
            lambda m:f'width="4200" height="{round(4200*float(m[2])/float(m[1]))}"',text,count=1)
        write_atomic(svg.with_suffix('.png'),resvg_py.svg_to_bytes(svg_string=text,background='#101822'))
        report['views'][side]={'layers':layers,'mirrored':side=='bottom',
            'svg_sha256':sha(svg),'png_sha256':sha(svg.with_suffix('.png'))}
        print(svg.with_suffix('.png'))
    assert sha(source)==before,'Plot export changed the source panel'
    write_atomic(folder/'render-manifest.json',json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
