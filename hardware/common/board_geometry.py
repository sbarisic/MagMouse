# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared board identity and polygon conversion helpers."""
import pcbnew as p

def signature(board):
    return {f.GetReference(): {'value': f.GetValue(),
        'footprint': str(f.GetFPID().GetLibItemName()),
        'pads': sorted((p.GetNumber(), p.GetNetname()) for p in f.Pads())}
        for f in board.GetFootprints()}

def polygons(shape):
    from shapely.geometry import Polygon
    def ring(chain):
        return [(p.ToMM(chain.CPoint(i).x),p.ToMM(chain.CPoint(i).y)) for i in range(chain.PointCount())]
    return [Polygon(ring(shape.COutline(i)),[ring(shape.CHole(i,j)) for j in range(shape.HoleCount(i))])
            for i in range(shape.OutlineCount())]
