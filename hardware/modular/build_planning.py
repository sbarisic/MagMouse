"""Inventory the proposed split and generate outline-only KiCad planning files.

Uses exported KiCad XML netlists, not hand-entered component counts. Does not
modify either source project, move copper or produce manufacturing files.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import uuid
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_netlist(path):
    root = ET.parse(path).getroot()
    components = {c.get("ref"): c for c in root.findall("./components/comp")}
    nets = {n.get("name"): [(p.get("ref"), p.get("pin")) for p in n.findall("node")]
            for n in root.findall("./nets/net")}
    return components, nets


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def natural(ref):
    match = re.fullmatch(r"([A-Za-z]+)(\d+)", ref)
    return (match[1], int(match[2])) if match else (ref, 0)


def inventory(config, main_path, encoder_path):
    components, nets = read_netlist(main_path)
    encoder, _ = read_netlist(encoder_path)
    wheel = {ref for ref, c in components.items()
             if c.find("sheetpath").get("names") in config["wheel_sheets"]}
    require(wheel, "No wheel sheet components found")
    extra = set(config["wheel_extra_refs"])
    require(extra <= components.keys(), f"Missing wheel refs: {extra - components.keys()}")
    wheel |= extra
    # A test point follows an exclusively wheel-owned electrical net. Shared
    # command test points stay on main; local wheel access will be added later.
    for nodes in nets.values():
        fixed = {ref for ref, _ in nodes if not ref.startswith("TP")}
        if fixed and fixed <= wheel:
            wheel |= {ref for ref, _ in nodes if ref.startswith("TP")}
    main = set(components) - wheel
    require(set(config["must_remain_main"]) <= main, "Main buffer/bias ownership changed")
    require(set(encoder) == set(config["encoder"]["refs"]), "Encoder inventory changed")
    require(not (set(encoder) & components.keys()), "Duplicate main/encoder references")
    boundary = {name: nodes for name, nodes in nets.items()
                if any(r in wheel for r, _ in nodes) and any(r in main for r, _ in nodes)}
    h = config["signal_harness"]
    signal_pins = {str(p): h["non_ground_pins"].get(str(p), h["remaining_pins"])
                   for p in range(1, h["contact_count"] + 1)}
    require(all(1 <= int(p) <= h["contact_count"] for p in h["non_ground_pins"]),
            "Signal pin outside connector")
    require(len(set(h["non_ground_pins"].values())) == len(h["non_ground_pins"]),
            "Duplicate non-ground signal")
    transported = set(signal_pins.values()) | set(config["power_harness"]["pins"].values())
    require(transported == set(boundary),
            f"Harness mismatch: missing {set(boundary) - transported}; extra {transported - set(boundary)}")
    # No phase, current-sense, reference or brake-control node may be carried
    # over this harness. Its allowed nets are explicitly enumerated in the plan.
    require(not any(re.search(r"(?:SO[ABC]|ISENSE|VREF|BRAKE_|PHASE)", n) for n in boundary),
            "Sensitive or high-current local net crosses partition")
    ownership = {"main": sorted(main, key=natural), "wheel": sorted(wheel, key=natural),
                 "encoder": sorted(encoder, key=natural)}
    return {
        "status": "PLANNED ownership; no schematic split or PCB connectivity acceptance",
        "source_netlist_sha256": {"main": sha(main_path), "encoder": sha(encoder_path)},
        "source_board_sha256": sha(ROOT / "hardware/kicad/MagMouse.kicad_pcb"),
        "component_counts_including_testpoints": {k: len(v) for k, v in ownership.items()},
        "ownership": ownership,
        "boundary_net_count": len(boundary),
        "boundary": {name: {"main": [f"{r}.{p}" for r, p in nodes if r in main],
                            "wheel": [f"{r}.{p}" for r, p in nodes if r in wheel]}
                     for name, nodes in sorted(boundary.items())},
        "signal_pins": signal_pins,
        "checks": ["Every original component has exactly one owner",
                   "All boundary nets are present in the logical harness",
                   "Encoder references are disjoint and complete",
                   "No phase, current-sense, reference or brake-control boundary net"]
    }


def root_sections(text):
    """Read complete direct children while respecting quoted strings/escapes."""
    depth, quoted, escaped, start = 0, False, False, None
    for i, c in enumerate(text):
        if quoted:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
        elif c == '"':
            quoted = True
        elif c == "(":
            if depth == 1:
                start = i
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 1 and start is not None:
                yield text[start:i + 1]
                start = None
    require(depth == 0 and not quoted, "Malformed source PCB")


def outline():
    # The three dimensions are user-specified; curvature and transitions are
    # draft assumptions. Sampled cubic segments are a polygon, not final tooling.
    curves = [((62, 0), (66, 0), (68, 14), (72, 30)),
              ((72, 30), (78, 48), (80, 52), (80, 65)),
              ((80, 65), (80, 70), (80, 82), (80, 90)),
              ((80, 90), (80, 111), (65, 125), (40, 125))]
    right = []
    for curve in curves:
        for i in range(13):
            if right and i == 0:
                continue
            t = i / 12
            a = [(1-t)**3, 3*(1-t)**2*t, 3*(1-t)*t*t, t**3]
            right.append(tuple(round(sum(w*p[d] for w, p in zip(a, curve)), 5)
                               for d in (0, 1)))
    return [(80-x, y) for x, y in reversed(right)][1:] + right


def rectangle(w, h):
    return [(0, 0), (w, 0), (w, h), (0, h)]


def uid(value):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "magmouse-modular-plan/" + value))


def pcb_text(header, name, polygons, note):
    items = list(header)
    for shape, (points, origin, layer) in polygons.items():
        for i, (a, b) in enumerate(zip(points, points[1:] + points[:1])):
            ax, ay = a[0]+origin[0], a[1]+origin[1]
            bx, by = b[0]+origin[0], b[1]+origin[1]
            require(math.dist((ax, ay), (bx, by)) > 0.00001, "Zero-length outline edge")
            items.append(f'(gr_line (start {ax:g} {ay:g}) (end {bx:g} {by:g}) '
                         f'(stroke (width 0.1) (type default)) (layer "{layer}") '
                         f'(uuid "{uid(name+shape+str(i))}"))')
    items.append(f'(gr_text {json.dumps(note)} (at 10 -8) (layer "Dwgs.User") '
                 f'(uuid "{uid(name+"note")}") '
                 '(effects (font (size 1.2 1.2) (thickness 0.2)) (justify left)))')
    return '(kicad_pcb\n' + '\n'.join(items) + '\n)\n'


def generate_geometry(config, output, counts):
    geom = config["geometry_mm"]
    require(geom["main"] == {"width": 80, "length": 125, "front_width": 44},
            "Update the contour construction for changed main dimensions")
    main = outline()
    shapes = {"Main-envelope": main,
              "Wheel-envelope": rectangle(geom["wheel"]["width"], geom["wheel"]["length"]),
              "Encoder-envelope": rectangle(geom["encoder"]["width"], geom["encoder"]["length"])}
    require((min(x for x,y in main), max(x for x,y in main),
             min(y for x,y in main), max(y for x,y in main)) == (0,80,0,125), "Wrong main bounds")
    require(main[-1] == (40,125), "Main contour endpoint changed")
    source = (ROOT / "hardware/kicad/MagMouse.kicad_pcb").read_text(encoding="utf-8")
    keys = {"version", "generator", "generator_version", "general", "paper", "layers", "setup"}
    header = [s for s in root_sections(source) if re.match(r"\(([^\s()]+)", s)[1] in keys]
    require(len(header) == len(keys), "Missing or duplicate source PCB header section")
    for name, points in shapes.items():
        (output / (name + ".kicad_pcb")).write_text(pcb_text(header, name,
            {name: (points, (0,0), "Edge.Cuts")},
            "PLANNING ENVELOPE ONLY - no components, copper or fabrication release"), encoding="utf-8")
    panel = geom["panel"]
    positions = [panel["main_origin"], panel["wheel_origin"], panel["encoder_origin"]]
    boxes = []
    for points, pos in zip(shapes.values(), positions):
        box = (min(x for x,y in points)+pos[0], min(y for x,y in points)+pos[1],
               max(x for x,y in points)+pos[0], max(y for x,y in points)+pos[1])
        require(box[0] >= panel["rail"] and box[1] >= panel["rail"] and
                box[2] <= panel["width"]-panel["rail"] and
                box[3] <= panel["length"]-panel["rail"], "Unit violates panel rail reservation")
        boxes.append(box)
    for i, a in enumerate(boxes):
        for b in boxes[i+1:]:
            require(max(b[0]-a[2], a[0]-b[2], b[1]-a[3], a[1]-b[3]) >= panel["minimum_gap"],
                    "Unit envelopes violate minimum gap")
    # A diagram, deliberately on a user drawing layer. It has no routed slots,
    # breakaway drill pattern or manufacturable panel outline on Edge.Cuts.
    polygons = {"frame": (rectangle(panel["width"], panel["length"]), (0,0), "Dwgs.User")}
    polygons.update({name: (points, pos, "Dwgs.User")
                     for (name, points), pos in zip(shapes.items(), positions)})
    (output / "Panel-nesting-study.kicad_pcb").write_text(pcb_text(header, "panel", polygons,
        "NESTING STUDY ONLY - 147 x 135 mm - slots, tabs and tooling not designed"), encoding="utf-8")
    def svgpoints(points, origin):
        return " ".join(f"{x+origin[0]:g},{y+origin[1]:g}" for x,y in points)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-10 -18 168 179" width="840" height="895">',
           '<rect x="-10" y="-18" width="168" height="179" fill="#f6f8fc"/>',
           '<g font-family="Arial,sans-serif" fill="#172735">',
           '<text x="0" y="-11" font-size="4.3">MagMouse: one panel, three detachable boards</text>',
           '<text x="0" y="-5" font-size="3">PLANNING ONLY • 5 sets • Croatia 43000</text>',
           '<rect width="147" height="135" fill="#e3e8ee" stroke="#6b7785" stroke-width="0.5"/>',
           '<rect x="5" y="5" width="137" height="125" fill="none" stroke="#8b96a3" stroke-width="0.3" stroke-dasharray="1 1"/>']
    for (name, pts), pos, color in zip(shapes.items(), positions, ["#c6e2ce", "#f5d4ad", "#c3d6f1"]):
        svg.append(f'<polygon points="{svgpoints(pts,pos)}" fill="{color}" stroke="#263b45" stroke-width="0.5"/>')
    for x,y,label,size in [(45,48,"MAIN",5),(45,55,"80 max x 125 mm",3.5),
                            (45,62,"44 mm front edge",3),(45,72,f'{counts["main"]} existing footprints',3),
                            (114.5,25,"WHEEL",4),(114.5,32,"55 x 60 mm draft",3),
                            (114.5,41,f'{counts["wheel"]} existing footprints',2.8),
                            (114.5,49,"DRV + ADC2 + brake",2.8),
                            (111,74,"ENCODER",3),(116,80,"14 x 18 mm",2.7),
                            (73.5,142,"147 x 135 mm provisional assembly envelope",3.3)]:
        svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{size}">{label}</text>')
    svg += ['<text x="0" y="150" font-size="2.8">5 mm outer rails and 2 mm minimum inter-board gap reserved.</text>',
            '<text x="0" y="155" font-size="2.8">Grey area: support-web study. Tabs/slots, mounts and parts still need placement.</text>',
            '</g></svg>']
    (output / "panel-concept.svg").write_text('\n'.join(svg), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-netlist", type=Path, required=True)
    parser.add_argument("--encoder-netlist", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=HERE / "planning")
    args = parser.parse_args()
    config = json.loads((HERE / "partition-plan.json").read_text())
    report = inventory(config, args.main_netlist, args.encoder_netlist)
    args.output.mkdir(parents=True, exist_ok=True)
    generate_geometry(config, args.output, report["component_counts_including_testpoints"])
    (args.output / "partition-report.json").write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({"components": report["component_counts_including_testpoints"],
                      "boundary_nets": report["boundary_net_count"],
                      "status": "Planning checks passed; electrical/manufacturing acceptance not assessed"}))


if __name__ == "__main__":
    main()
