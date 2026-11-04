"""Extract independent Lower/Upper schematics and bind the placed boards.

Run once before routing. The combined main-circuit is retained as the migration
reference. SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import copy,json,sys,subprocess,xml.etree.ElementTree as ET
import pcbnew as p

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SCRATCH=ROOT/'build/sandwich/main-routing'
sys.path.insert(0,str(ROOT/'hardware/modular'))
import schematic_io as s
from extract_schematics import filter_sheet,rewrite_instances
CLI=Path(sys.executable).with_name('kicad-cli.exe')
SHARE=Path(sys.executable).parents[1]/'share/kicad'

def export(path,out):
    subprocess.run([str(CLI),'sch','export','netlist','--format','kicadxml','-o',str(out),str(path)],check=True)
    tree=ET.parse(out).getroot()
    comps={c.get('ref'):c for c in tree.findall('./components/comp')}
    pins={(n.get('ref'),n.get('pin')):net.get('name') for net in tree.findall('./nets/net') for n in net.findall('node')}
    return comps,pins

def main():
    SCRATCH.mkdir(parents=True,exist_ok=True)
    source=HERE/'main-circuit'
    before,before_pins=export(source/'Main.kicad_sch',SCRATCH/'Main.xml')
    plan=json.loads((HERE/'partition.json').read_text())
    original=s.parse((source/'Main.kicad_sch').read_text(encoding='utf-8'))
    oldroot=s.get(original,'uuid')[1]
    results={}
    for name in ('Lower','Upper'):
        dest=HERE/name.lower();pcbpath=dest/(name+'.kicad_pcb')
        assert not (dest/(name+'.kicad_sch')).exists(),'Already split; edit independent projects instead'
        board=p.LoadBoard(str(pcbpath));assert not list(board.GetTracks()),'Do not rebuild over routing'
        (SCRATCH/(name+'-placement.kicad_pcb')).write_bytes(pcbpath.read_bytes())
        owned={ref for ref,owner in plan['component_ownership'].items() if owner==name}
        rootid=s.ident(name+'stack-root');root=copy.deepcopy(original)
        s.get(root,'uuid')[1]=rootid
        root[:]=[n for n in root if not isinstance(n,list) or n[0] not in ('sheet','text')]
        s.get(s.get(root,'title_block'),'title')[1]='MagMouse '+name+' Main - two layers'
        s.get(s.get(root,'title_block'),'date')[1]='2026-11-04'
        s.text(root,f'MagMouse {name} Main / 70 x 100 mm / two copper layers\nPassive plastic buttons with Hall sensing. Main stack: 19 wires / 3 shared grounds.',20,18,name+'stack-title')
        children=[]
        for child in s.allof(original,'sheet'):
            filename=s.props(child)['Sheetfile'];tree=s.parse((source/filename).read_text(encoding='utf-8'))
            refs={s.props(c)['Reference'] for c in s.allof(tree,'symbol') if not s.props(c)['Reference'].startswith('#')}
            if not refs&owned:continue
            filter_sheet(tree,owned);rewrite_instances(tree,name,oldroot,rootid)
            if not refs<=owned:
                tree[:]=[n for n in tree if not isinstance(n,list) or n[0]!='text']
                s.text(tree,f'{filename[:-10]} / {name} components\nSee 20_Stack_Harness for the inter-board wiring.',20,18,name+filename)
            for node in s.allof(tree,'symbol'):
                if s.props(node)['Reference']=='U3':
                    next(v for v in s.allof(node,'property') if v[1]=='Footprint')[2]='MagMouseSandwich:ESP32-S2-MINI-1'
            s.write(dest/filename,tree)
            children.append((s.props(child)['Sheetname'],s.get(child,'uuid')[1],filename))
        sid=s.ident(name+'stack-interface');filename='20_Stack_Harness.kicad_sch'
        tree=s.parse(f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{s.ident(name+filename)}") (paper "A3") (lib_symbols) (embedded_fonts no))')
        path='/'+rootid+'/'+sid
        plugin=p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP)
        for f in board.GetFootprints():
            ref=f.GetReference()
            if ref in owned:continue
            if ref.startswith('J'):
                power=ref in ('J103','J104');fpname='Wire_Stack_Power_5' if power else 'Wire_Stack_Signal_14'
                value='Stack power / 5 wires' if power else 'Stack signals / 14 wires'
                symbol=s.library_symbol(SHARE,'Connector_Generic:Conn_01x05' if power else 'Connector_Generic:Conn_01x14')
                loc=(195.58,60.96) if power else (81.28,91.44)
                nets={pad.GetNumber():pad.GetNetname() for pad in f.Pads()}
            else:
                fpname='MountingHole_2.2mm_M2_5mm_Envelope';value='M2 clearance / 5mm support envelope'
                symbol=s.library_symbol(SHARE,'Mechanical:MountingHole');nets={}
                loc=(60.96+40.64*(int(ref[1:])%4),180.34)
            f.SetValue(value);f.SetFPID(p.LIB_ID('MagMouseSandwich',fpname))
            clone=p.FOOTPRINT(f);clone.SetOrientationDegrees(0);clone.SetPosition(p.VECTOR2I(0,0));clone.SetReference('REF**')
            plugin.FootprintSave((HERE/'MagMouseSandwich.pretty').as_posix(),clone)
            node=s.add_component(tree,symbol,ref,value,loc,nets,name,path,{'Footprint':'MagMouseSandwich:'+fpname})
            if ref.startswith('H'):
                s.get(node,'in_bom')[1]=s.Atom('no');f.SetExcludedFromBOM(True);f.SetExcludedFromPosFiles(True)
        # Connector-fed rails are explicitly driven by the other board.
        for i,net in enumerate(('PWR_5V',) if name=='Lower' else ('VBUS_USB','+3V3','GND')):
            s.add_component(tree,s.library_symbol(SHARE,'power:PWR_FLAG'),f'#FLG_STACK{i}', 'PWR_FLAG',
                            (241.3+30.48*i,180.34),{'1':net},name,path,{'Footprint':''},board=False)
        s.text(tree,'Connect equal-numbered signal and power pads between Lower and Upper.\n19 wires total: 13 signals, 3 supply rails, 3 shared grounds.\nAll three buttons use passive plastic clicks and Hall sensing.',20,22,name+'stack-notes')
        s.write(dest/filename,tree);children.append(('20_Stack_Harness',sid,filename))
        for i,(title,sid,filename) in enumerate(children):
            x,y=20+132*(i//8),50+25*(i%8)
            root.append(s.parse(f'(sheet (at {x} {y}) (size 112 17) (stroke (width 0.254) (type default)) (fill (color 0 0 0 0)) (uuid "{sid}") '
                f'(property "Sheetname" "{title}" (at {x} {y-1.27} 0) (effects (font (size 1 1)) (justify left bottom))) '
                f'(property "Sheetfile" "{filename}" (at {x} {y+18.27} 0) (effects (font (size 1 1)) (justify left top))) '
                f'(instances (project "{name}" (path "/{rootid}" (page "{i+2}")))))'))
        s.write(dest/(name+'.kicad_sch'),root)
        project=json.loads((dest/(name+'.kicad_pro')).read_text());project['meta']['filename']=name+'.kicad_pro'
        project['text_variables']={'STATUS':'TWO-LAYER STACK / PROTOTYPE'}
        (dest/(name+'.kicad_pro')).write_text(json.dumps(project,indent=2)+'\n')
        comps,pins=export(dest/(name+'.kicad_sch'),SCRATCH/(name+'.xml'))
        for ref in owned:
            assert comps[ref].findtext('value')==before[ref].findtext('value'),ref
            assert {k:v for k,v in pins.items() if k[0]==ref}=={k:v for k,v in before_pins.items() if k[0]==ref},ref
        for f in board.GetFootprints():
            ref=f.GetReference();c=comps[ref]
            f.SetPath(p.KIID_PATH('/'+rootid+c.find('sheetpath').get('tstamps')+c.findtext('tstamps')))
            for prop in c.findall('property'):
                if prop.get('name')=='Sheetname':f.SetSheetname(prop.get('value'))
                if prop.get('name')=='Sheetfile':f.SetSheetfile(prop.get('value'))
            assert f.GetFPID().GetLibItemName()==c.findtext('footprint').split(':')[1],ref
            for pad in f.Pads():
                if pad.GetNumber():assert pad.GetNetname()==pins.get((ref,pad.GetNumber()),''),(ref,pad.GetNumber())
        p.SaveBoard(str(pcbpath),board)
        subprocess.run([str(CLI),'sch','erc','--format','json','-o',str(dest/(name+'-erc.json')),str(dest/(name+'.kicad_sch'))],check=True)
        subprocess.run([str(CLI),'pcb','drc','--format','json','--schematic-parity','-o',str(dest/(name+'-drc.json')),str(pcbpath)],check=True)
        results[name]={'retained_components':len(owned),'added_interface_and_mounts':len(comps)-len(owned),'original_pin_connections_unchanged':True}
        print(name,results[name],flush=True)
    (HERE/'split-review.json').write_text(json.dumps(results,indent=2)+'\n')

if __name__=='__main__':main()
