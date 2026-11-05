# SPDX-License-Identifier: GPL-3.0-or-later
"""Native-contact resistance screening, not an ampacity or thermal model.

Default assumptions are inherited from the original checker. Callers must set
path costs for their actual stackup; the current review uses 1.6 mm barrels.
"""
import heapq, math
import pcbnew as pcb
TEMPERATURE_C=80
RHO=.01724*(1+.00393*(TEMPERATURE_C-20))
THICKNESS_MM={pcb.F_Cu:.035,pcb.In2_Cu:.030,pcb.B_Cu:.035}
BOARD_MM=1.578
PLATING_MM=.020

def uid(item):
    return item.m_Uuid.AsString()

class CopperGraph:
    """Native direct contacts; no geometric guesses or whole-net shortcuts."""

    def __init__(self, board):
        conn = board.GetConnectivity()
        self.items = {uid(t): t for t in board.GetTracks()}
        self.pads = {}
        for footprint in board.GetFootprints():
            for pad in footprint.Pads():
                if pad.GetNumber():
                    self.items[uid(pad)] = pad
                    self.pads.setdefault((footprint.GetReference(), pad.GetNumber()), pad)
        self.adj, self.cost = {}, {}
        for key, item in self.items.items():
            contacts = list(conn.GetConnectedTracks(item)) + list(conn.GetConnectedPads(item))
            self.adj[key] = {uid(t) for t in contacts if uid(t) in self.items
                             and t.GetNetname() == item.GetNetname()}
            if isinstance(item, pcb.PCB_VIA):
                drill = pcb.ToMM(item.GetDrillValue())
                # Thin-wall barrel estimate. Count full board thickness even
                # for a transition between adjacent layers.
                self.cost[key] = RHO * BOARD_MM / 1000 / (math.pi * drill * PLATING_MM)
            elif isinstance(item, pcb.PCB_TRACK):
                thickness = THICKNESS_MM.get(item.GetLayer(), .030)
                self.cost[key] = RHO * pcb.ToMM(item.GetLength()) / 1000 / (
                    pcb.ToMM(item.GetWidth()) * thickness)
            else:
                self.cost[key] = 0

    def path(self, start, end, allowed=None):
        queue, seen = [(0, start, [])], set()
        while queue:
            cost, key, path = heapq.heappop(queue)
            if key in seen or (allowed is not None and key not in allowed):
                continue
            seen.add(key)
            path = path + [key]
            if key == end:
                return cost, path
            for neighbor in self.adj[key] - seen:
                heapq.heappush(queue, (cost + self.cost[neighbor], neighbor, path))
        return None
