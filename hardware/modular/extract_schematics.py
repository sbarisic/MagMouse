"""Create independent main/wheel draft schematics from the retained baseline.

Write to an empty staging directory. The result is promoted after exported
netlists pass verify_split.py; never regenerate over manually edited projects.
"""
import argparse
import copy
import json
from pathlib import Path

from schematic_io import (Atom, add_component, allof, get, ident, library_symbol,
                          parse, pin_positions, props, text, write)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CAD = ROOT / "hardware/kicad"


def rewrite_instances(node, project, oldroot, newroot):
    if not isinstance(node, list):
        return
    if node and node[0] == "project":
        node[1] = project
    if node and node[0] == "path" and len(node) > 1:
        node[1] = node[1].replace(oldroot, newroot)
    for child in node:
        if isinstance(child, list):
            rewrite_instances(child, project, oldroot, newroot)


def filter_sheet(sheet, owned):
    """Remove only excluded instances and their isolated labelled wire stubs.

    Fail if a removed wire group reaches a retained component; joined circuits
    need deliberate redrawing, not automatic wire deletion.
    """
    libs = {s[1]: s for s in allof(get(sheet, "lib_symbols"), "symbol")}
    remove, lost, kept = [], set(), set()
    for c in allof(sheet, "symbol"):
        ref = props(c)["Reference"]
        points = set(pin_positions(c, libs[get(c, "lib_id")[1]]).values())
        if ref in owned or ref.startswith("#"):
            kept |= points
        else:
            remove.append(c)
            lost |= points
    progress = True
    while progress:
        progress = False
        for wire in allof(sheet, "wire"):
            if wire in remove:
                continue
            pts = {tuple(round(float(v),4) for v in p[1:]) for p in get(wire,"pts")[1:]}
            if pts & lost:
                if pts & kept:
                    raise ValueError("Excluded wire reaches retained symbol; redraw manually")
                lost |= pts
                remove.append(wire)
                progress = True
    for key in ("global_label", "label", "junction", "no_connect"):
        for item in allof(sheet, key):
            if tuple(round(float(v),4) for v in get(item,"at")[1:3]) in lost:
                remove.append(item)
    for item in remove:
        sheet.remove(item)
    used = {get(c,"lib_id")[1] for c in allof(sheet,"symbol")}
    get(sheet,"lib_symbols")[:] = [Atom("lib_symbols"), *(s for k,s in libs.items() if k in used)]
    return sheet


def sourcing(mpn, lcsc, maker, footprint, datasheet=""):
    return {"MPN": mpn, "LCSC": lcsc, "JLCPCB Part #": lcsc,
            "Manufacturer": maker, "Footprint": footprint, "Datasheet": datasheet,
            "Checked": "2026-09-10", "Supplier URL": "https://jlcpcb.com/partdetail/"+lcsc,
            "Sourcing Status": "Catalog identity checked; stock and assembly quote not reserved"}


def interface(base, name, rootid, config):
    sheetname = "18_Wheel_Harness"
    sheetid = ident(name+sheetname)
    sheet = parse(f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{ident(name+"interface-file")}") '
                  '(paper "A3") (title_block (title "Modular wheel harness - circuit draft") '
                  '(date "2026-09-10") (rev "0.1 DRAFT")) (lib_symbols) (embedded_fonts no))')
    path = "/" + rootid + "/" + sheetid
    wheel = name == "Wheel"
    h = config["signal_harness"]
    pinmap = {str(p): h["non_ground_pins"].get(str(p), "GND") for p in range(1,31)}
    if wheel:
        pinmap = {str(h["wheel_pin_for_main_pin"][p]): net for p,net in pinmap.items()}
    connector = library_symbol(base, "Connector_Generic:Conn_01x30")
    fields = sourcing(h["header_mpn"], h["header_lcsc"], "Hirose", h["footprint"], h["datasheet"])
    add_component(sheet, connector, "J9" if wheel else "J8", "WHEEL_SIGNAL_30P", (91.44,101.6),
                  pinmap, name, path, fields)
    power = config["power_harness"]
    add_component(sheet, library_symbol(base,"Connector_Generic:Conn_01x02"), "J11" if wheel else "J10",
                  "WHEEL_POWER_2P", (198.12,55.88), power["pins"], name, path,
                  sourcing(power["candidate_header_mpn"], power["candidate_lcsc"], "JST",
                           power["footprint"], "https://www.jst-mfg.com/product/pdf/eng/ePA-F.pdf"))
    resistors = ([("R137","10k","WHEEL_RUN_REQ"),("R138","10k","WHEEL_PWM_A"),
                  ("R139","10k","WHEEL_PWM_B"),("R140","10k","WHEEL_PWM_C"),
                  ("R144","33k","CS_DRV8316"),("R145","33k","CS_ADC2")]
                 if wheel else [("R141","33k","DRV_FAULT_LOCAL_N"),
                                ("R142","33k","DRV_MISO_LOCAL"),("R143","33k","ADC2_MISO_LOCAL")])
    parts = {"10k": ("0603WAF1002T5E","C25804"), "33k": ("0603WAF3302T5E","C4216"),
             "100k": ("0603WAF1003T5E","C25803")}
    for i,(ref,value,net) in enumerate(resistors):
        mpn,lcsc = parts[value]
        add_component(sheet, library_symbol(base,"Device:R"), ref, value,
                      (205.74+60.96*(i%3),101.6+50.8*(i//3)), {"1":net,"2":"GND"}, name,path,
                      sourcing(mpn,lcsc,"UNI-ROYAL","Resistor_SMD:R_0603_1608Metric"))
    if wheel:
        for i,net in enumerate(["GND","+3V3","ACT_5V"]):
            add_component(sheet,library_symbol(base,"power:PWR_FLAG"),f"#FLG_W{i+1}","PWR_FLAG",
                          (190.5+50.8*i,210.82),{"1":net},name,path,{"Footprint":""},board=False)
    text(sheet,"MAIN J8 pin N to WHEEL J9 pin (31-N); MAIN odd / WHEEL even contacts GND.\nSame-side-contact FFC; component sides up, headers facing each other; no twist.\nPOWER J10/J11: 1 ACT_5V, 2 GND. Disconnect survival outside prototype scope.",20,22,name+"interface-title")
    text(sheet,("U22 raw RUN/PWM inputs default low locally. R77 remains on main.\nCS inputs default low only when disconnected; clocks also low and RUN disabled.\nR88 is 4.7k in this project to support the main-side fault pulldown.\nNo power is carried across breakaway tabs. Do not hot plug."
                if wheel else "Unplugged wheel fault return defaults LOW through R141.\nMISO inputs have local idle bias; select signals retain main-side pullups.\nEncoder stays on main J6 directly to J7; it does not cross this harness.\nNo power is carried across breakaway tabs. Do not hot plug."),20,238,name+"interface-notes")
    return sheetname, sheetid, sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--kicad-share",type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("Output must be empty; do not overwrite independently edited schematics")
    plan = json.loads((HERE/"partition-plan.json").read_text())
    report = json.loads((HERE/"planning/partition-report.json").read_text())
    source = parse((CAD/"MagMouse.kicad_sch").read_text(encoding="utf-8"))
    oldroot = get(source,"uuid")[1]
    for name in ("Main","Wheel"):
        out = args.output/name.lower()
        out.mkdir(parents=True)
        rootid = ident(name+"root")
        owned = set(report["ownership"][name.lower()])
        root = parse(f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{rootid}") '
                     f'(paper "A3") (title_block (title "MagMouse modular {name}") '
                     '(date "2026-09-10") (rev "0.1 DRAFT")) (lib_symbols) '
                     '(sheet_instances (path "/" (page "1"))) (embedded_fonts no))')
        text(root,f"MagMouse modular {name} - independent schematic draft\nNOT FOR FABRICATION - copper migration and harness validation incomplete",20,18,name+"title")
        children=[]
        for child in allof(source,"sheet"):
            filename = props(child)["Sheetfile"]
            tree = parse((CAD/filename).read_text(encoding="utf-8"))
            if not any(props(c)["Reference"] in owned for c in allof(tree,"symbol")):
                continue
            original_refs={props(c)["Reference"] for c in allof(tree,"symbol")}
            filter_sheet(tree,owned)
            rewrite_instances(tree,name,oldroot,rootid)
            if not original_refs <= owned:
                tree[:]=[n for n in tree if not (isinstance(n,list) and n[0]=="text")]
                text(tree,f"{filename[:-10]} - {name} owned components only\nSee 18_Wheel_Harness for connector/bias additions; see INTERFACE_REVIEW.md for limits.",20,18,name+filename+"title")
            # Explicit reviewed value change, preserving R88 connectivity/identity.
            if name=="Wheel":
                for c in allof(tree,"symbol"):
                    if props(c)["Reference"] in ("R84","R88"):
                        value,mpn,lcsc = (("10k","0603WAF1002T5E","C25804") if props(c)["Reference"]=="R84"
                                          else ("4.7k","0603WAF4701T5E","C23162"))
                        updates={"Value":value,**sourcing(mpn,lcsc,"UNI-ROYAL",
                                  "Resistor_SMD:R_0603_1608Metric")}
                        for p in allof(c,"property"):
                            if p[1] in updates:p[2]=updates[p[1]]
            write(out/filename,tree)
            children.append((props(child)["Sheetname"],get(child,"uuid")[1],filename))
        sheetname,sheetid,tree=interface(args.kicad_share,name,rootid,plan)
        write(out/(sheetname+".kicad_sch"),tree)
        children.append((sheetname,sheetid,sheetname+".kicad_sch"))
        for i,(title,sid,filename) in enumerate(children):
            x,y=20+132*(i//8),50+25*(i%8)
            root.append(parse(f'(sheet (at {x} {y}) (size 112 17) (stroke (width 0.254) (type default)) '
                              f'(fill (color 0 0 0 0)) (uuid "{sid}") '
                              f'(property "Sheetname" "{title}" (at {x} {y-1.27} 0) (effects (font (size 1 1)) (justify left bottom))) '
                              f'(property "Sheetfile" "{filename}" (at {x} {y+18.27} 0) (effects (font (size 1 1)) (justify left top))) '
                              f'(instances (project "{name}" (path "/{rootid}" (page "{i+2}")))))'))
        write(out/(name+".kicad_sch"),root)
        project=copy.deepcopy(json.loads((CAD/"MagMouse.kicad_pro").read_text()))
        project["meta"]["filename"]=name+".kicad_pro"
        project["text_variables"]={"STATUS":"MODULAR DRAFT - NOT FOR FABRICATION"}
        (out/(name+".kicad_pro")).write_text(json.dumps(project,indent=2)+"\n")
        (out/"sym-lib-table").write_text('(sym_lib_table (version 7) (lib (name "MagMouse") (type "KiCad") (uri "${KIPRJMOD}/../../kicad/MagMouse.kicad_sym") (options "") (descr "Shared symbols")))\n')
        (out/"fp-lib-table").write_text('(fp_lib_table (version 7) (lib (name "MagMouse") (type "KiCad") (uri "${KIPRJMOD}/../../kicad/MagMouse.pretty") (options "") (descr "Shared footprints")) (lib (name "MagMouseModular") (type "KiCad") (uri "${KIPRJMOD}/../MagMouseModular.pretty") (options "") (descr "Modular connectors")))\n')
        print(f"{name}: {len(owned)} retained source refs, {len(children)} subsheets")


if __name__=="__main__":
    main()
