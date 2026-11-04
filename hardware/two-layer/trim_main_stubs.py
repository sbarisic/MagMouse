"""Repair reviewed track overruns and a redundant branch on Main.

Run with KiCad Python, then verify.py. Refuses changed input geometry and keeps
component/pad-net identity. Re-running on the repaired board is a no-op.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import pcbnew as p
from prepare import DEST, signature


def point(xy):
    return p.VECTOR2I(*(p.FromMM(v) for v in xy))


def main():
    path = DEST/'main/Main.kicad_pcb'
    board = p.LoadBoard(str(path))
    before = signature(board)
    # UUID, net, layer, endpoint, original position, reviewed junction.
    repairs = [
        ('84b4f3fb-d741-46f0-9534-78fa360e3d64', 'CC_OUT2', p.F_Cu,
         'End', (122.6, 24.65), (128.7, 30.75)),
        ('8ad6dcfc-53c2-4899-a9c3-166e6d766ed6', 'CS_ADC2', p.B_Cu,
         'End', (116.3, 64.8), (116.3, 66.55)),
        ('864abb64-d614-4b70-ab2f-d6f9e5f94a0d', 'CS_IMU', p.F_Cu,
         'Start', (88.35, 93.75), (88.35, 84.45)),
        ('d01278c2-763d-4d0e-846b-e8e02f431148', 'CS_IMU', p.F_Cu,
         'End', (90.4, 82.4), (88.35, 84.45)),
        # Join the retained left-hand PWM route to the MCU pad center.
        ('3bb235a0-dff1-4c21-a33c-419617a04bc2', 'WHEEL_PWM_A', p.F_Cu,
         'Start', (122.1, -17.15), (122.0, -17.45)),
    ]
    tracks = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    changed = 0
    for uid, net, layer, end, old, new in repairs:
        track = tracks[uid]
        assert track.GetNetname() == net and track.GetLayer() == layer, uid
        actual = getattr(track, 'Get'+end)()
        if actual == point(new):
            continue
        assert actual == point(old), f'Unexpected geometry: {uid}'
        getattr(track, 'Set'+end)(point(new))
        changed += 1
    # This branch duplicates the direct pad-to-right route and forms an acute
    # copper sliver at (128.052882, -16.213499). The direct route is retained.
    redundant = {
        'a7690e9f-fbd9-4c59-9e17-b6852620d7af':
            ((122.5, -17.099999), (122.15, -17.099999)),
        'd47b1eec-6ad5-40e5-9a64-b2381452612b':
            ((123.5, -16.149999), (122.6, -17.049999)),
        'e21b8228-4dd1-41e4-a2b5-9a3df204fe5e':
            ((128.25, -16.149999), (123.5, -16.149999)),
    }
    for uid, (start, end) in redundant.items():
        if uid not in tracks:
            continue
        track = tracks[uid]
        assert track.GetNetname() == 'WHEEL_PWM_A' and track.GetLayer() == p.F_Cu, uid
        assert track.GetStart() == point(start) and track.GetEnd() == point(end), uid
        board.Remove(track)
        track.thisown = False
        changed += 1
    if changed:
        board.BuildConnectivity()
        p.ZONE_FILLER(board).Fill(board.Zones())
        assert signature(board) == before
        p.SaveBoard(str(path), board)
    print(f'Applied {changed} Main track repairs')


if __name__ == '__main__':
    main()
