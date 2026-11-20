"""Measure the Lower board's USB return copper and native connector paths."""

# SPDX-License-Identifier: GPL-3.0-or-later
import math
import pcbnew as p
from copper_graph import CopperGraph, uid
from board_geometry import polygons
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

SIGNALS = {"USB_DP", "USB_DM", "MCU_USB_DP", "MCU_USB_DM"}
LAYERS = (p.F_Cu, p.B_Cu)


def mm(point):
    return tuple(p.ToMM(point))


def pathline(track):
    return LineString([mm(track.GetStart()), mm(track.GetEnd())])


def actual_ground(board, layer, holes):
    shapes = []
    for zone in board.Zones():
        if (
            zone.GetNetname() == "GND"
            and not zone.GetIsRuleArea()
            and zone.IsOnLayer(layer)
        ):
            shapes.extend(polygons(zone.GetFilledPolysList(layer)))
    for pad in board.GetPads():
        if pad.GetNetname() == "GND" and pad.IsOnLayer(layer):
            poly = p.SHAPE_POLY_SET()
            pad.TransformShapeToPolygon(poly, layer, 0, p.FromMM(0.001), p.ERROR_INSIDE)
            shapes.extend(polygons(poly))
    for item in board.GetTracks():
        if item.GetNetname() != "GND" or not item.IsOnLayer(layer):
            continue
        if isinstance(item, p.PCB_VIA):
            shapes.append(
                Point(mm(item.GetPosition())).buffer(p.ToMM(item.GetWidth(layer)) / 2)
            )
        else:
            shapes.append(pathline(item).buffer(p.ToMM(item.GetWidth()) / 2))
    return unary_union(shapes).difference(holes)


def check_usb(board):
    assert board.GetCopperLayerCount() == 2
    board.BuildConnectivity()
    holes = []
    for pad in board.GetPads():
        if pad.GetDrillSize().x:
            poly = p.SHAPE_POLY_SET()
            pad.TransformHoleToPolygon(poly, 0, p.FromMM(0.001), p.ERROR_OUTSIDE)
            holes.extend(polygons(poly))
    vias = [item for item in board.GetTracks() if isinstance(item, p.PCB_VIA)]
    holes.extend(
        Point(mm(via.GetPosition())).buffer(p.ToMM(via.GetDrillValue()) / 2)
        for via in vias
    )
    cuts = unary_union(holes)
    reference = {layer: actual_ground(board, layer, cuts) for layer in LAYERS}
    transitions = {
        name: sorted(
            (mm(via.GetPosition()) for via in vias if via.GetNetname() == name),
            key=lambda q: q[1],
        )
        for name in ("USB_DP", "USB_DM")
    }
    assert all(len(points) == 2 for points in transitions.values()), transitions
    spacings = [
        math.dist(dp, dm)
        for dp, dm in zip(transitions["USB_DP"], transitions["USB_DM"])
    ]
    assert max(spacings) <= 1.0, spacings
    for dp, dm in zip(transitions["USB_DP"], transitions["USB_DM"]):
        center = tuple((a + b) / 2 for a, b in zip(dp, dm))
        nearby_returns = sum(
            via.GetNetname() == "GND" and math.dist(mm(via.GetPosition()), center) < 2.1
            for via in vias
        )
        assert nearby_returns >= 2, (center, nearby_returns)
    antipads = unary_union(
        [
            Point(mm(via.GetPosition())).buffer(
                p.ToMM(via.GetWidth(p.F_Cu)) / 2 + 0.215
            )
            for via in vias
            if via.GetNetname() in SIGNALS
        ]
    )
    coverage = {}
    for name in sorted(SIGNALS):
        for layer, opposite in (LAYERS, LAYERS[::-1]):
            traces = [
                item
                for item in board.GetTracks()
                if not isinstance(item, p.PCB_VIA)
                and item.GetNetname() == name
                and item.IsOnLayer(layer)
            ]
            if not traces:
                continue
            centerlines = unary_union([pathline(item) for item in traces])
            copper = unary_union(
                [pathline(item).buffer(p.ToMM(item.GetWidth()) / 2) for item in traces]
            )
            missing = copper.difference(reference[opposite])
            missing_center = (
                centerlines.difference(reference[opposite]).difference(antipads).length
            )
            uncovered = missing.difference(antipads).area
            key = name + " " + board.GetLayerName(layer)
            coverage[key] = {
                "trace_mm": round(centerlines.length, 4),
                "unreferenced_centerline_outside_vias_mm": round(missing_center, 4),
                "unreferenced_area_outside_vias_mm2": round(uncovered, 6),
            }
            assert missing_center < 0.001 and uncovered < 0.001, (
                key,
                missing_center,
                uncovered,
                missing.difference(antipads).wkt[:500],
            )
    graph = CopperGraph(board)
    for key, item in graph.items.items():
        graph.cost[key] = (
            p.ToMM(item.GetLength())
            if isinstance(item, p.PCB_TRACK) and not isinstance(item, p.PCB_VIA)
            else 0
        )
    paths = {}
    for pin, r in [("A6", "R6"), ("B6", "R6"), ("A7", "R5"), ("B7", "R5")]:
        start = graph.pads["J1", pin]
        end = graph.pads[r, "2"]
        route = graph.path(uid(start), uid(end))
        assert route is not None, pin
        dist, keys = route
        changes = [
            mm(graph.items[k].GetPosition())
            for k in keys
            if isinstance(graph.items[k], p.PCB_VIA)
        ]
        assert changes == transitions[start.GetNetname()], (pin, changes)
        paths["J1." + pin + " to " + r + ".2"] = {
            "whole_track_length_mm": round(dist, 3),
            "layer_changes": len(changes),
        }
    return {
        "coverage": coverage,
        "via_coordinates_mm": transitions,
        "paired_via_spacing_mm": spacings,
        "connector_paths": paths,
    }
