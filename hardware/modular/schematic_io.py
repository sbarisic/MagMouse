"""Small KiCad S-expression helpers for the reviewed modular migration."""
import copy
import json
import math
import re
import uuid
from pathlib import Path


class Atom(str):
    pass


def parse(text):
    stack, roots = [], []
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        if token == "(":
            child = []
            (stack[-1] if stack else roots).append(child)
            stack.append(child)
        elif token == ")":
            stack.pop()
        else:
            stack[-1].append(json.loads(token) if token.startswith('"') else Atom(token))
    if stack or len(roots) != 1:
        raise ValueError("Malformed KiCad document")
    return roots[0]


def dump(item, depth=0):
    if not isinstance(item, list):
        return str(item) if isinstance(item, Atom) else json.dumps(item, ensure_ascii=False)
    if not any(isinstance(x, list) for x in item):
        return "(" + " ".join(dump(x) for x in item) + ")"
    return "(" + " ".join(dump(x) for x in item if not isinstance(x, list)) + "".join(
        "\n" + "  "*(depth+1) + dump(x, depth+1) for x in item if isinstance(x, list)) + ")"


def allof(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def get(node, key):
    return next(iter(allof(node, key)), None)


def props(node):
    return {p[1]: p[2] for p in allof(node, "property")}


def ident(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "MagMouse/modular/" + key))


def pins(symbol):
    return [p for sub in allof(symbol, "symbol") for p in allof(sub, "pin")]


def pin_positions(instance, symbol):
    x, y, angle = map(float, get(instance, "at")[1:])
    a = math.radians(angle)
    if get(instance, "mirror"):
        raise ValueError("Mirrored source symbol needs an explicit migration transform")
    return {get(p, "number")[1]:
            (round(x+float(get(p,"at")[1])*math.cos(a)-float(get(p,"at")[2])*math.sin(a), 4),
             round(y-float(get(p,"at")[1])*math.sin(a)-float(get(p,"at")[2])*math.cos(a), 4))
            for p in pins(symbol)}


def library_symbol(base, libid):
    group, name = libid.split(":")
    library = parse((Path(base) / "symbols" / (group + ".kicad_sym")).read_text(encoding="utf-8"))
    result = copy.deepcopy(next(s for s in allof(library, "symbol") if s[1] == name))
    if get(result, "extends"):
        raise ValueError(f"Resolve inherited library symbol explicitly: {libid}")
    result[1] = libid
    return result


def add_component(sheet, symbol, ref, value, xy, nets, project, path, fields, board=True):
    """Create a single-unit symbol with short, separately labelled pin stubs."""
    x, y = xy
    libid = symbol[1]
    cache = get(sheet, "lib_symbols")
    if not any(s[1] == libid for s in allof(cache, "symbol")):
        cache.append(copy.deepcopy(symbol))
    node = parse(f'(symbol (lib_id {json.dumps(libid)}) (at {x} {y} 0) (unit 1) '
                 f'(in_bom {"yes" if board else "no"}) (on_board {"yes" if board else "no"}) '
                 f'(dnp no) (uuid "{ident(project+ref)}"))')
    for i, (key, val) in enumerate({"Reference": ref, "Value": value, **fields}.items()):
        visible = key in ("Reference", "Value")
        node.append(parse(f'(property {json.dumps(key)} {json.dumps(val)} (at {x+5} {y-3+i*2.5 if visible else y} 0) '
                          + ('' if visible else '(hide yes) ') + '(effects (font (size 1 1)) (justify left)))'))
    node.append(parse(f'(instances (project "{project}" (path "{path}" (reference "{ref}") (unit 1))))'))
    sheet.append(node)
    positions = pin_positions(node, symbol)
    for p in pins(symbol):
        number = get(p, "number")[1]
        px, py = positions[number]
        direction = float(get(p, "at")[3])
        angle = math.radians(direction)
        ex, ey = round(px-5.08*math.cos(angle),4), round(py+5.08*math.sin(angle),4)
        net = nets.get(number)
        if net is None:
            sheet.append(parse(f'(no_connect (at {px} {py}) (uuid "{ident(project+ref+number+"nc")}"))'))
            continue
        sheet.append(parse(f'(wire (pts (xy {px} {py}) (xy {ex} {ey})) (stroke (width 0) (type default)) '
                           f'(uuid "{ident(project+ref+number+"wire")}"))'))
        la = int((direction+180)%360)
        justify = "right" if la in (180,270) else "left"
        sheet.append(parse(f'(global_label {json.dumps(net)} (shape bidirectional) (at {ex} {ey} {la}) '
                           f'(effects (font (size 1 1)) (justify {justify})) '
                           f'(uuid "{ident(project+ref+number+"label")}"))'))
    return node


def text(sheet, value, x, y, key):
    sheet.append(parse(f'(text {json.dumps(value)} (at {x} {y} 0) '
                       f'(effects (font (size 1.2 1.2)) (justify left top)) (uuid "{ident(key)}"))'))


def write(path, tree):
    path.write_text(dump(tree) + "\n", encoding="utf-8", newline="\n")
