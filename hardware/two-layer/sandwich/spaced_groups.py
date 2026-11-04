"""Requested spacing revision, relative to the approved compact placements."""
import json
import math
from pathlib import Path

BASELINE=json.loads(Path(__file__).with_name('spacing-baseline.json').read_text())
COURTYARD_GAP_MM=.6
TARGETS={
    'Lower':{
        'U11':(43,23),'U2':(52,28),'U33':(32,25),'U34':(54,17),'D5':(28,24),
        'U36':(18,46),'U38':(18,58),'U37':(39,36),'U39':(29,34),
        'U25':(49,43),'U32':(48,70),
    },
    'Upper':{
        'U4':(19,38),'U5':(18,57),'U6':(53,41),'U10':(40,39),
        'U13':(51,59),'U14':(29,32),'U19':(29,24),
        'U15':(48,84),'U16':(19,75),'U17':(19,85),'U18':(48,75),'D2':(18,67),
    },
}
# Preserve the supply/bypass groups, including capacitors on a different sheet.
ANCHORS={
    'C1':'U2','C2':'U2','C3':'U2','C23':'U2','L1':'U2','C22':'U11',
    'C73':'U33','C74':'U33','C75':'U34','C76':'D5',
    'C77':'U38','C78':'U38','C79':'U38','C81':'U38','C82':'U36',
    'C83':'U35','C84':'U35','C85':'U35','C86':'U35','C87':'U37','C80':'U39',
    'C37':'D2','C38':'D2','C39':'D2','C40':'U13',
}


def goals(side,fps,sheets):
    baseline=BASELINE[side]
    targets={ref:position for ref,position in TARGETS[side].items() if ref in fps}
    result={ref:tuple(baseline[ref]) for ref in fps}
    anchors={}
    for ref in fps:
        if ref in targets or ref.startswith(('U','J','H','TP')):
            continue
        candidates=[a for a in fps if (a.startswith('U') or a in targets)
                    and sheets.get(a)==sheets.get(ref)]
        anchor=ANCHORS.get(ref)
        if anchor not in fps:anchor=None
        if anchor is None and candidates:
            anchor=min(candidates,key=lambda a:math.dist(baseline[ref],baseline[a]))
        if anchor is None:continue
        anchors[ref]=anchor
        ax,ay=baseline[anchor];tx,ty=targets.get(anchor,(ax,ay))
        x,y=baseline[ref]
        # Keep capacitor/inductor offsets; expand the other support components
        # within moved groups by 20%, then check their full-size geometry.
        factor=1 if ref.startswith(('C','L')) or anchor not in targets else 1.2
        result[ref]=(tx+(x-ax)*factor,ty+(y-ay)*factor)
    result.update(targets)
    return result,anchors
