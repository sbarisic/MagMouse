"""Find same-net routed loops on each copper layer, independent of KiCad clearance DRC.

Run with KiCad Python from any directory. The audit covers straight routed tracks,
including finite-width contacts between different track endpoints. Ground pours,
pads, vias and intentional multilayer return paths are outside this planar test.
"""
# SPDX-License-Identifier: GPL-3.0-or-later
from collections import defaultdict
import json

from export_quote import BOARDS, p
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree


def review(board):
    groups = defaultdict(list)
    for track in board.GetTracks():
        if isinstance(track, p.PCB_VIA):
            continue
        if type(track) != p.PCB_TRACK:
            raise ValueError(f"Unsupported track geometry on {track.GetNetname()}")
        points = [p.ToMM(track.GetStart()), p.ToMM(track.GetEnd())]
        if points[0] != points[1]:
            layer = board.GetLayerName(track.GetLayer())
            groups[track.GetNetname(), layer].append((LineString(points), p.ToMM(track.GetWidth())))

    findings = []
    for (net, layer), segments in sorted(groups.items()):
        lines = [line for line, width in segments]
        index = STRtree(lines)
        crossings = []
        overlaps = 0
        for i, first in enumerate(lines):
            for j in index.query(first, predicate="intersects"):
                if j <= i:
                    continue
                second = lines[j]
                contact = first.intersection(second)
                if contact.geom_type == "LineString" and contact.length > 0.00001:
                    overlaps += 1
                elif contact.geom_type == "Point" and all(
                    contact.distance(Point(q)) > 0.002 for q in (*first.coords, *second.coords)
                ):
                    crossings.append([round(value, 5) for value in contact.coords[0]])

        rings = list(polygonize(unary_union(lines)))
        copper = unary_union([line.buffer(width / 2, quad_segs=16) for line, width in segments])
        holes = [Polygon(ring) for region in getattr(copper, "geoms", [copper]) for ring in region.interiors]
        copper_holes = [round(hole.area, 6) for hole in holes if hole.area > 0.0001]
        if rings or copper_holes or crossings or overlaps:
            findings.append({
                "net": net, "layer": layer,
                "centerline_loops": len(rings),
                "holes_in_track_copper_mm2": copper_holes,
                "interior_crossings_mm": crossings,
                "overlapping_segment_pairs": overlaps,
            })
    return findings


if __name__ == "__main__":
    audits = {name: review(p.LoadBoard(str(path))) for name, path in BOARDS.items()}
    print(json.dumps(audits, indent=2))
    if any(row for rows in audits.values() for row in rows if row["net"] != "GND"):
        raise SystemExit(1)
