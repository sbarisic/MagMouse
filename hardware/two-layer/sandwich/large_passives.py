"""Guarded 0603/0805 to 1206 migration; run with KiCad Python.

Saved boards are authoritative after placement and routing repairs.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import copy,json,shutil,sys,subprocess,collections,hashlib
from pathlib import Path
import pcbnew as p
from export_quote import BOARDS,HERE,ROOT,CLI
sys.path.insert(0,str(ROOT/'hardware/modular'))
import schematic_io as s
SCRATCH=ROOT/'build/sandwich/1206'
LIB=Path(sys.executable).parents[1]/'share/kicad/footprints'
CAPS={
 '100nF':('YAGEO','CC1206KRX7R9BB104','50 V, X7R, 10%'),
 '10nF':('YAGEO','CC1206KRX7R9BB103','50 V, X7R, 10%'),
 '1nF/50V':('YAGEO','CC1206KRX7R9BB102','50 V, X7R, 10%'),
 '47nF/50V':('YAGEO','CC1206KRX7R9BB473','50 V, X7R, 10%'),
 '22pF/50V':('YAGEO','CC1206JRNPO9BN220','50 V, C0G/NP0, 5%'),
 '1uF/50V':('Samsung Electro-Mechanics','CL31B105KBHNNNE','50 V, X7R, 10%'),
 '2.2uF/10V':('Samsung Electro-Mechanics','CL31B225KAHNNNE','25 V, X7R, 10%'),
 '4.7uF/10V':('Samsung Electro-Mechanics','CL31A475KAHNNNE','25 V, X5R, 10%'),
 '10uF/25V':('Samsung Electro-Mechanics','CL31A106KAHNNNE','25 V, X5R, 10%'),
 '22uF/25V':('Samsung Electro-Mechanics','CL31A226KAHNNNE','25 V, X5R, 10%'),
}

def selection(ref,value):
 if ref.startswith('R'):
  code=value.upper().replace('.','K',1).replace('KK','K') if '.' in value and value.endswith('k') else value.upper()
  # Decimal notation puts the unit at the decimal point: 22.1k -> 22K1.
  if '.' in value:
   a,b=value[:-1].split('.');code=a+value[-1].upper()+b
  mpn='RC1206JR-070RL' if value=='0R' else 'RC1206FR-07'+code+'L'
  manufacturer='YAGEO';rating='0.25 W, 1%' if value!='0R' else 'Jumper, 2 A'
  url='https://pccomponents.com/datasheets/yageo-rc.pdf'
 else:
  manufacturer,mpn,rating=CAPS[value]
  url=('https://www.yageogroup.com/download/specsheet/'+mpn if manufacturer=='YAGEO'
       else 'https://product.samsungsem.com/mlcc/'+mpn[:-1]+'.do')
 return {'Manufacturer':manufacturer,'MPN':mpn,'LCSC':'','JLCPCB Part #':'','Supplier URL':'',
         'Sourcing Status':'1206 replacement; supplier stock and assembly availability not checked',
         'Checked':'2026-11-04','Source URL':url,'Datasheet':url,'Rating':rating}

def properties(node,values):
 for key,value in values.items():
  prop=next((q for q in s.allof(node,'property') if q[1]==key),None)
  if prop is None:
   prop=copy.deepcopy(next(q for q in s.allof(node,'property') if q[1]=='MPN'));prop[1]=key;node.append(prop)
   uid=s.get(prop,'uuid')
   if uid:uid[1]=s.ident(s.props(node)['Reference']+key+'1206')
  prop[2]=value

def migrate():
 assert not (SCRATCH/'baseline.json').exists(),'Migration already started'
 assert not (HERE/'1206-migration.json').exists(),'Saved boards are already migrated'
 SCRATCH.mkdir(parents=True,exist_ok=True)
 baseline={}
 for name,path in BOARDS.items():
  dest=SCRATCH/'original'/name;dest.mkdir(parents=True,exist_ok=True)
  for f in path.parent.glob('*.kicad_*'):shutil.copy2(f,dest/f.name)
  b=p.LoadBoard(str(path))
  baseline[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'components':{
   f.GetReference():{'value':f.GetValue(),'footprint':str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),'xy':list(p.ToMM(f.GetPosition())),
   'angle':f.GetOrientationDegrees(),'pads':sorted((q.GetNumber(),q.GetNetname()) for q in f.Pads())}
   for f in b.GetFootprints()}}
 (SCRATCH/'baseline.json').write_text(json.dumps(baseline,indent=2)+'\n')
 changes={}
 for name,path in BOARDS.items():
  tree=s.parse(path.read_text());changes[name]={}
  for f in s.allof(tree,'footprint'):
   if not any(tag in f[1] for tag in ('R_0603_','R_0805_','C_0603_','C_0805_')):continue
   props=s.props(f);ref=props['Reference'];kind='Resistor' if ref.startswith('R') else 'Capacitor'
   fp=kind+'_SMD:'+ref[0]+'_1206_3216Metric';library,item=fp.split(':')
   lib=s.parse((LIB/(library+'.pretty')/(item+'.kicad_mod')).read_text())
   angle=float(s.get(f,'at')[3]) if len(s.get(f,'at'))>3 else 0
   oldpads={q[1]:q for q in s.allof(f,'pad')}
   geometry=[]
   for node in lib:
    if not isinstance(node,list) or node[0] not in ('pad','fp_line','fp_rect','fp_text','model'):continue
    node=copy.deepcopy(node)
    at=s.get(node,'at')
    if at:
     if len(at)==3:at.append(s.Atom('0'))
     at[3]=s.Atom(str(float(at[3])+angle))
    if node[0]=='pad':
     old=oldpads[node[1]]
     for key in ('uuid','net','pinfunction','pintype','zone_connect'):
      if s.get(old,key):node.append(copy.deepcopy(s.get(old,key)))
    geometry.append(node)
   f[:]=[q for q in f if not(isinstance(q,list) and (str(q[0]).startswith('fp_') or q[0] in ('pad','model')))]
   f[1]=fp;f.extend(geometry);fields=selection(ref,props['Value']);properties(f,fields)
   changes[name][ref]={'from':baseline[name]['components'][ref]['footprint'],'to':fp,'value':props['Value'],**fields}
  s.write(path,tree)
  b=p.LoadBoard(str(path));b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
  for sch in path.parent.glob('*.kicad_sch'):
   tree=s.parse(sch.read_text());changed=False
   for sym in s.allof(tree,'symbol'):
    ref=s.props(sym).get('Reference')
    if ref in changes[name]:
     c=changes[name][ref];properties(sym,{'Footprint':c['to'],**selection(ref,c['value'])});changed=True
   if changed:s.write(sch,tree)
  print(name,len(changes[name]),flush=True)
 (HERE/'1206-migration.json').write_text(json.dumps(changes,indent=2)+'\n')
 assert sum(map(len,changes.values()))==193

def check(name):
 path=BOARDS[name];out=SCRATCH/(name+'-drc.json')
 subprocess.run([str(CLI),'pcb','drc','--format','json','--schematic-parity','-o',str(out),str(path)],check=True,stdout=subprocess.DEVNULL)
 d=json.loads(out.read_text());print(name,dict(collections.Counter(v['type'] for v in d['violations'])),'unconnected',len(d['unconnected_items']),'parity',len(d.get('schematic_parity',[])),flush=True);return d

def verify():
 """Record the net/value, fixed-placement and fabrication checks for this migration."""
 from standard_vias import intersections
 from export_quote import polygons
 import math
 baseline=json.loads((SCRATCH/'baseline.json').read_text())
 migration=json.loads((HERE/'1206-migration.json').read_text());report={}
 for name,path in BOARDS.items():
  b=p.LoadBoard(str(path));before=baseline[name]['components'];after={f.GetReference():f for f in b.GetFootprints()}
  assert set(before)==set(after)
  moves=[]
  for ref,f in after.items():
   old=before[ref]
   assert f.GetValue()==old['value'],(name,ref,'value')
   assert sorted((q.GetNumber(),q.GetNetname()) for q in f.Pads())==[tuple(q) for q in old['pads']],(name,ref,'nets')
   distance=math.dist(old['xy'],p.ToMM(f.GetPosition()))
   if ref in migration[name]:
    assert '1206_3216Metric' in str(f.GetFPID().GetLibItemName()),(name,ref)
    assert f.GetFieldText('MPN')==migration[name][ref]['MPN']
    moves.append({'ref':ref,'before_mm':old['xy'],'after_mm':list(p.ToMM(f.GetPosition())),'distance_mm':distance})
   else:
    assert distance<.0002 and f.GetOrientationDegrees()==old['angle'],(name,ref,'fixed placement')
  assert not any(any(t in str(f.GetFPID().GetLibItemName()) for t in ['R_0603_','R_0805_','C_0603_','C_0805_']) for f in after.values())
  vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
  assert all(t.GetDrillValue()>=p.FromMM(.3) for t in vias)
  assert not intersections(b),name+' via in pad'
  oldboard=p.LoadBoard(str(SCRATCH/'original'/name/path.name));a=p.SHAPE_POLY_SET();c=p.SHAPE_POLY_SET()
  assert b.GetBoardPolygonOutlines(a,False) and oldboard.GetBoardPolygonOutlines(c,False)
  assert [q.wkb_hex for q in polygons(a)]==[q.wkb_hex for q in polygons(c)]
  if name=='Lower':
   def usb_trunks(board,baseline=False):
    result=[]
    for t in board.GetTracks():
     if isinstance(t,p.PCB_VIA) or t.GetNetname() not in ('USB_DP','USB_DM') or p.ToMM(t.GetWidth())<.7:continue
     points=[tuple(round(v,6) for v in p.ToMM(pt)) for pt in (t.GetStart(),t.GetEnd())]
     if baseline and t.GetNetname()=='USB_DP':
      points=[(34.4,73.85) if pt==(34.4,74.3) else pt for pt in points]
     result.append((t.GetNetname(),t.GetLayer(),round(p.ToMM(t.GetWidth()),6),tuple(sorted(points))))
    return sorted(result)
   assert usb_trunks(b)==usb_trunks(oldboard,True),'USB differential trunks changed'
  d=check(name);assert not d['violations'] and not d['unconnected_items'] and not d.get('schematic_parity')
  report[name]={'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'baseline_sha256':baseline[name]['sha256'],
   'changed_packages':len(migration[name]),'values_and_pad_nets_unchanged':True,'other_component_positions_unchanged':True,
   'outline_unchanged':True,'copper_layers':b.GetCopperLayerCount(),'via_count':len(vias),'minimum_via_drill_mm':min(p.ToMM(t.GetDrillValue()) for t in vias),
   'via_in_pad':0,'drc_findings':0,'unconnected':0,'schematic_parity_findings':0,'placements':moves}
  if name=='Lower':report[name]['usb_trunks_preserved_except_south_dp_via_offset_mm']=.45
 assert sum(q['changed_packages'] for q in report.values())==193
 (HERE/'1206-review.json').write_text(json.dumps(report,indent=2)+'\n')

def refresh_metadata(name):
 """Remove supplier links for the superseded small packages."""
 changes=json.loads((HERE/'1206-migration.json').read_text());path=BOARDS[name]
 b=p.LoadBoard(str(path))
 for f in b.GetFootprints():
  ref=f.GetReference()
  if ref not in changes[name]:continue
  f.SetField('Supplier URL','')
  changes[name][ref]['Supplier URL']=''
  changes[name][ref]['to']=str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())
 p.SaveBoard(str(path),b)
 for sch in path.parent.glob('*.kicad_sch'):
  tree=s.parse(sch.read_text());changed=False
  for sym in s.allof(tree,'symbol'):
   if s.props(sym).get('Reference') in changes[name]:properties(sym,{'Supplier URL':''});changed=True
  if changed:s.write(sch,tree)
 (HERE/'1206-migration.json').write_text(json.dumps(changes,indent=2)+'\n')

if __name__=='__main__':
 if sys.argv[1]=='migrate':migrate()
 elif sys.argv[1]=='verify':verify()
 elif sys.argv[1]=='metadata':
  for name in sys.argv[2:] or BOARDS:refresh_metadata(name)
 else:
  for name in sys.argv[2:] or BOARDS:check(name)
