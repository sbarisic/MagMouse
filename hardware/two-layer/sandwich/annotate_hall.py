"""Add review callouts to native panel SVGs without changing PCB or fabrication data."""
import sys,re,json,hashlib
from route_main import HERE,ROOT,p
sys.path.insert(0,str(ROOT/'build/two-layer/python'))
sys.path.insert(0,str(ROOT/'hardware/common'))
import resvg_py
from kicad_output import write
folder=HERE/'panel'
manifest=json.loads((folder/'render-manifest.json').read_text())
assert hashlib.sha256((folder/'Panel.kicad_pcb').read_bytes()).hexdigest()==manifest['source_sha256']
source=(folder/'Panel-top.svg').read_text()
assert hashlib.sha256((folder/'Panel-top.svg').read_bytes()).hexdigest()==manifest['views']['top']['svg_sha256']
b=p.LoadBoard(str(folder/'Panel.kicad_pcb'));fs={f.GetReference():f for f in b.GetFootprints()}
points=[(ref,label,*p.ToMM(fs['U_'+ref].GetPosition())) for ref,label in [('U7','LEFT'),('U8','MIDDLE'),('U9','RIGHT')]]
for detail in (False,True):
 overlay=['<g font-family="Arial, sans-serif" text-anchor="middle">']
 for ref,label,x,y in points:
  radius=1.65 if detail else 2.1
  ty=25.8 if detail else 3.6
  end=y+radius if detail else y-radius
  overlay += [f'<circle cx="{x}" cy="{y}" r="{radius}" fill="none" stroke="#101822" stroke-width=".65"/>',
   f'<circle cx="{x}" cy="{y}" r="{radius}" fill="none" stroke="#00eeff" stroke-width=".25"/>',
   f'<path d="M{x},{end} L{x},{ty-1.35 if detail else ty+.65}" fill="none" stroke="#00eeff" stroke-width=".16"/>',
   f'<rect x="{x-6.4}" y="{ty-1.7}" width="12.8" height="2.4" rx=".45" fill="#101822"/>',
   f'<text x="{x}" y="{ty}" fill="#00eeff" font-size="1.45" font-weight="bold">{ref} · {label}</text>']
 overlay.append('</g>')
 svg=source.replace('</svg>','\n'.join(overlay)+'\n</svg>')
 dims=('1400','431','94 12 52 16') if detail else ('4200','2012','0 0 237.9980 113.9952')
 svg=re.sub(r'width="[\d.]+mm" height="[\d.]+mm" viewBox="[^"]+"',f'width="{dims[0]}" height="{dims[1]}" viewBox="{dims[2]}"',svg,count=1)
 stem='Panel-hall-detail' if detail else 'Panel-top-hall-locations'
 write(folder/(stem+'.svg'),svg)
 write(folder/(stem+'.png'),resvg_py.svg_to_bytes(svg_string=svg,background='#101822'))
 print(stem,points)
