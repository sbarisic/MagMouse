"""Check the requested Hall placement against the routed release sources."""
import json,hashlib
from hall_relocation import p,BOARDS,HERE,check_positions,POSITIONS,POWER_PAD
from validate_circuit_fixes import measurements
from validate_routing_cleanup import main as routing_acceptance
from review_power_ground import inspect
from kicad_output import write

def main():
    routing_acceptance()
    for name,path in BOARDS.items():check_positions(name,p.LoadBoard(str(path)))
    b=p.LoadBoard(str(BOARDS['Upper']));fs={f.GetReference():f for f in b.GetFootprints()}
    for sensor,net,adc in [('U7','HALL_L','15'),('U8','HALL_M','16'),('U9','HALL_R','1')]:
        assert next(q for q in fs[sensor].Pads() if q.GetNumber()=='4').GetNetname()==net
        assert next(q for q in fs['U10'].Pads() if q.GetNumber()==adc).GetNetname()==net
    caps=measurements(b,[('U7','1','C16','1'),('U8','1','C17','1'),('U9','1','C18','1')])
    assert all(c['pad_center_distance_mm']<=5 and c['whole_segment_sum_mm']<=5 and c['vias']==0 for c in caps)
    power={name:inspect(name,BOARDS[name]) for name in ('Lower','Upper')}
    # The moved wire feed must remain a short power path, not a board-wide detour.
    for name,start,end in [('Lower','J103.3','U2.2'),('Upper','U12.6','J104.3')]:
        path=next(x for x in power[name]['power_paths'] if x['source']==start and x['destination']==end)
        assert path['path_mohm']<30,(name,path)
    report={'placements_mm':POSITIONS,'matched_power_pad_mm':POWER_PAD,'local_bypass':caps,
        'power_paths':{n:x['power_paths'] for n,x in power.items()},
        'sources':{n:hashlib.sha256(path.read_bytes()).hexdigest() for n,path in BOARDS.items()},
        'channel_mapping_unchanged':True,'hardware_validated':False,
        'physical_followup':'Align the moving magnets with the revised sensor centres; check travel, polarity and calibrated endpoints.'}
    write(HERE/'hall-placement-review.json',json.dumps(report,indent=2)+'\n')
    print('Hall placement, channel mapping, local bypass and power-path checks passed.',flush=True)

if __name__=='__main__':main()
