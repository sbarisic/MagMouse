"""Place the long USB pair before autorouting local fanouts.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import pcbnew as p
from route_main import HERE,SCRATCH,track,via,check,export

def main():
    path=HERE/'lower/Lower.kicad_pcb';board=p.LoadBoard(str(path))
    assert not list(board.GetTracks()),'USB trunk is a one-time pre-route'
    # These two underside test pads otherwise overlap the USB trunk corridor.
    from route_main import xy
    for f in board.GetFootprints():
        if f.GetReference()=='TP28':f.SetPosition(xy(34,69.5))
        elif f.GetReference()=='TP29':f.SetPosition(xy(38,78))
    # The optical opening is avoided on its right. The narrow sections are
    # limited to the U1 and series-resistor lands; the trunk uses the inherited
    # two-layer 1.10 mm / 0.15 mm USB geometry pending fabricator stack review.
    for net,start,end,points in [
        ('USB_DP',(34.25,21.45),(34.4,74.3),[(34.25,22.5),(43,31.25),(43,65.7),(34.4,74.3)]),
        ('USB_DM',(35.6,21.45),(36.55,74.3),[(35.6,22.081),(44.25,30.731),(44.25,66.6),(36.55,74.3)])]:
        via(board,net,start);via(board,net,end)
        track(board,net,[start,points[0]],.3,p.B_Cu)
        track(board,net,points,1.1,p.B_Cu)
    track(board,'USB_DP',[(34.65,20.425),(34.65,21.05),(34.25,21.45)],.15)
    track(board,'USB_DM',[(35.35,20.425),(35.35,21.2),(35.6,21.45)],.15)
    track(board,'USB_DP',[(34.4,74.3),(34.400002,75.675)],.3)
    track(board,'USB_DM',[(36.55,74.3),(36.55,75.675)],.3)
    board.BuildConnectivity();p.SaveBoard(str(path),board)
    check('Lower');export('Lower')
if __name__=='__main__':main()
