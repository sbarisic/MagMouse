"""Create the first wheel placement from its independent exported netlist.

Run with KiCad Python. The promoted PCB becomes the editable source; do not
regenerate over later routing. Original motherboard copper is never imported.
"""
import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import pcbnew as p

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
LIB=Path('C:/Users/cartm/AppData/Local/Programs/KiCad/10.0/share/kicad/footprints')


def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--netlist',type=Path,required=True)
    a.add_argument('--output',type=Path,required=True)
    args=a.parse_args()
    if args.output.exists():raise SystemExit('Output already exists; edit the PCB instead of regenerating')
    tree=ET.parse(args.netlist)
    board=p.LoadBoard(str(HERE/'planning/Wheel-envelope.kicad_pcb'))
    for item in list(board.GetDrawings()):
        if item.GetLayer()!=p.Edge_Cuts:board.Remove(item)
    nets={};pins={}
    for n in tree.findall('./nets/net'):
        net=p.NETINFO_ITEM(board,n.get('name'));board.Add(net);nets[n.get('name')]=net
        for node in n.findall('node'):pins[node.get('ref'),node.get('pin')]=net
    positions=json.loads((HERE/'wheel-placement.json').read_text())['positions_mm_degrees']
    rootid=re.search(r'\(uuid "([^"]+)"\)',(HERE/'wheel/Wheel.kicad_sch').read_text()).group(1)
    refs={c.get('ref') for c in tree.findall('./components/comp')}
    assert refs==set(positions),(refs-set(positions),set(positions)-refs)
    for c in tree.findall('./components/comp'):
        ref=c.get('ref');lib,name=c.findtext('footprint').split(':')
        directory={'MagMouse':ROOT/'hardware/kicad/MagMouse.pretty',
                   'MagMouseModular':HERE/'MagMouseModular.pretty'}.get(lib,LIB/(lib+'.pretty'))
        fp=p.FootprintLoad(str(directory),name)
        if fp is None:raise ValueError(c.findtext('footprint'))
        board.Add(fp);fp.SetReference(ref);fp.SetValue(c.findtext('value'))
        fp.SetFPIDAsString(c.findtext('footprint'))
        fp.SetPath(p.KIID_PATH('/'+rootid+c.find('sheetpath').get('tstamps')+c.findtext('tstamps')))
        for prop in c.findall('property'):
            key,val=prop.get('name'),prop.get('value')
            if key=='Sheetname':fp.SetSheetname(val)
            if key=='Sheetfile':fp.SetSheetfile(val)
            if key=='exclude_from_bom':fp.SetExcludedFromBOM(True)
        for field in c.findall('./fields/field'):
            if field.get('name')!='Footprint':fp.SetField(field.get('name'),field.text or '')
        fp.SetField('Datasheet',c.findtext('datasheet') or '')
        if ref.startswith('TP'):fp.SetExcludedFromPosFiles(True)
        for pad in fp.Pads():
            net=pins.get((ref,pad.GetNumber()))
            if net is not None:pad.SetNet(net)
        x,y,angle=positions[ref];fp.SetPosition(xy(x,y));fp.SetOrientationDegrees(angle)
        for field in fp.GetFields():field.SetVisible(False)
        fp.Reference().SetVisible(True);fp.Reference().SetLayer(p.F_Fab)
        fp.Reference().SetTextSize(xy(.65,.65));fp.Reference().SetTextThickness(p.FromMM(.12))
        fp.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
        fp.Reference().SetPosition(xy(x,y-2.2))
    def text(value,x,y,size=.8,layer=p.Dwgs_User):
        t=p.PCB_TEXT(board);t.SetText(value);t.SetPosition(xy(x,y));t.SetTextSize(xy(size,size))
        t.SetTextThickness(p.FromMM(.12));t.SetLayer(layer);board.Add(t)
    text('WHEEL 55 x 60 mm / INITIAL PLACEMENT / UNROUTED',27.5,-5)
    text('J9 -> MAIN J8\nJ9.N = J8.(31-N) / SAME-SIDE FFC',38,-2,.65)
    text('POWER / JST PA',8,-2,.65)
    text('PHASE A / B / C',29,57,.75)
    text('MOUNTS / ENCLOSURE / CABLE BENDS PROVISIONAL',27.5,64,.75)
    text('Wheel 0.2',43,54,1,p.F_SilkS)
    text('UNROUTED',43,56,.8,p.F_SilkS)
    board.BuildConnectivity()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    project=args.output.with_suffix('.kicad_pro');original=project.read_bytes() if project.exists() else None
    p.SaveBoard(str(args.output),board)
    if original is not None:project.write_bytes(original)
    print(f'{len(refs)} footprints, {len(nets)} nets, no tracks; {args.output}')


if __name__=='__main__':main()
