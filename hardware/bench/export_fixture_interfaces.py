"""Export exact unit outlines/datums for the independently editable bench CAD."""
import pcbnew as p
from build_panel import SOURCES,ROOT,outline,sha,save_json


def generate():
    data={}
    for name,path in SOURCES.items():
        b=p.LoadBoard(str(path));poly=outline(b)
        data[name]=dict(source_sha256=sha(path),outline=list(poly.exterior.coords),
                        holes=[list(r.coords) for r in poly.interiors],
                        hall_positions={f.GetReference():[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)] for f in b.GetFootprints() if f.GetReference() in ['U7','U8','U9']})
    save_json(ROOT/'mechanical/bench/board-interfaces.json',data)


if __name__=='__main__':generate()
