"""Check split netlists against baseline pin connectivity and cable contracts.

This is circuit migration/DC screening, not power-ramp, cable-current, timing,
thermal, PCB or manufacturing acceptance. --require-reviewed keeps those open
gates explicit rather than treating a correct split as an orderable design.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bench'))
from wire_interfaces import INTERFACES,footprint_name
from local_power_checks import review as review_local_power

HERE = Path(__file__).resolve().parent


def read(path):
    root=ET.parse(path).getroot()
    comps={c.get("ref"): c for c in root.findall("./components/comp")}
    pins={(p.get("ref"),p.get("pin")): n.get("name") for n in root.findall("./nets/net")
          for p in n.findall("node")}
    return comps,pins


def verify(baseline,main_path,wheel_path):
    plan=json.loads((HERE/"partition-plan.json").read_text())
    disconnect_required=plan["prototype_scope"]["cable_disconnect_survival_required"]
    ownership=json.loads((HERE/"planning/partition-report.json").read_text())["ownership"]
    old,oldpins=read(baseline)
    boards={"main":read(main_path),"wheel":read(wheel_path)}
    errors=[]
    def check(ok,message):
        if not ok: errors.append(message)
    additions={"main":{"J8","J10","R141","R142","R143"},
               "wheel":{"J9","J11","R137","R138","R139","R140","R144","R145","C90","D6","R146"}}
    expected_edits={"R84":("10k","0603WAF1002T5E","C25804"),
                    "R88":("4.7k","0603WAF4701T5E","C23162"),
                    # Bench L1 qualification: hardware/bench/L1_REVIEW.md.
                    "L1":("SRP4020CC-3R3M","SRP4020CC-3R3M","")}
    checks=0
    for board,(comps,pins) in boards.items():
        check(set(comps)==set(ownership[board])|additions[board],f"{board}: component inventory mismatch")
        for ref in ownership[board]:
            if ref not in comps: continue
            for key,net in oldpins.items():
                if key[0]==ref:
                    checks+=1
                    check(pins.get(key)==net,f"{board} {key}: changed net {net} -> {pins.get(key)}")
            # NC pins may not acquire new connections during extraction.
            for key in pins:
                if key[0]==ref:check(key in oldpins,f"{ref}: previously unconnected pin {key[1]} connected")
            before={f.get("name"):f.text or "" for f in old[ref].findall("./fields/field")}
            after={f.get("name"):f.text or "" for f in comps[ref].findall("./fields/field")}
            edit=expected_edits.get(ref)
            wire_kind=INTERFACES[board.title()].get(ref)
            for field in ("MPN","LCSC","Footprint"):
                expected=(edit[1] if field=="MPN" else edit[2]) if edit and field!="Footprint" else before.get(field,"")
                if ref=='L1' and field=='Footprint':expected='MagMouseModular:L_Bourns_SRP4020CC'
                if wire_kind:expected='MagMouseModular:'+footprint_name(wire_kind) if field=='Footprint' else ''
                check(after.get(field,"")==expected,f"{ref}: unexpected {field} change")
            value='Soldered wires '+wire_kind if wire_kind else edit[0] if edit else old[ref].findtext("value")
            check(comps[ref].findtext("value")==value,f"{ref}: unexpected value change")
    def net(board,ref,pin):return boards[board][1].get((ref,str(pin)))
    def resistor(board,ref,a,b):
        check({net(board,ref,1),net(board,ref,2)}=={a,b},f"{board} {ref}: bias ends wrong")
    for pin in range(1,31):
        expected=plan["signal_harness"]["non_ground_pins"].get(str(pin),"GND")
        wheel_pin=plan["signal_harness"]["wheel_pin_for_main_pin"][str(pin)]
        check(wheel_pin==31-pin,"Wire mapping differs from J8.N to J9.(31-N)")
        check(net("main","J8",pin)==expected and net("wheel","J9",wheel_pin)==expected,f"Signal cable pin {pin} -> {wheel_pin}")
    for pin,expected in plan["power_harness"]["pins"].items():
        check(net("main","J10",pin)==expected and net("wheel","J11",pin)==expected,f"Power cable pin {pin}")
    for board,refs in [("main",["J8","J10"]),("wheel",["J9","J11"])]:
        for ref,h in zip(refs,[plan["signal_harness"],plan["power_harness"]]):
            c=boards[board][0].get(ref)
            if c is None:continue
            fields={f.get("name"):f.text or "" for f in c.findall("./fields/field")}
            check(fields.get("LCSC")==h.get("header_lcsc",h.get("candidate_lcsc")),f"{ref}: wrong catalog ID")
            check(c.findtext("footprint")==h["footprint"],f"{ref}: wrong footprint")
    for ref,signal in [("R137","WHEEL_RUN_REQ"),("R138","WHEEL_PWM_A"),("R139","WHEEL_PWM_B"),
                       ("R140","WHEEL_PWM_C"),("R144","CS_DRV8316"),("R145","CS_ADC2"),
                       ("R84","ACT_DRIVE_EN")]:resistor("wheel",ref,signal,"GND")
    for ref,signal in [("R141","DRV_FAULT_LOCAL_N"),("R142","DRV_MISO_LOCAL"),("R143","ADC2_MISO_LOCAL")]:
        resistor("main",ref,signal,"GND")
    def resistance(board,ref):
        val=boards[board][0][ref].findtext("value")
        return float(val[:-1])*1000 if val.endswith("k") else float(val.rstrip("R"))
    # 1% initial plus 100 ppm/K through a 100 K excursion, conservatively 2%.
    factor=1.02
    fault_low=20e-6*resistance("main","R141")*factor
    rlow=1/(1/(resistance("main","R141")/factor)+1/(resistance("wheel","R89")/factor))
    rup=resistance("wheel","R88")*factor
    parallel=1/(1/rlow+1/rup)
    fault_high=3.1*rlow/(rlow+rup)-50e-6*parallel
    check(fault_low<.8,"Unplugged fault is not a guaranteed CMOS low")
    check(fault_high>2.2,"Added fault pulldown violates DRV startup threshold")
    bias_results={"fault_unplugged_max_V":fault_low,"fault_connected_min_V":fault_high,
                  "fault_total_sink_leakage_screen_A":50e-6}
    for local,source in [("R144","R76"),("R145","R74")]:
        resistor("main",source,"+3V3", "CS_DRV8316" if local=="R144" else "CS_ADC2")
        low=20e-6*resistance("wheel",local)*factor
        rd=resistance("wheel",local)/factor; ru=resistance("main",source)*factor
        high=3.0*rd/(ru+rd)-20e-6/(1/ru+1/rd)
        check(low<.8 and high>2.0,f"{local}: disconnected-low/connected-high CS bias failed")
        bias_results[local]={"unplugged_max_V":low,"main_reset_min_V":high}
    act_low=50e-6*resistance("wheel","R84")*factor
    check(act_low<.6,"Unplugged ACT_DRIVE_EN may wake driver")
    bias_results["enable_unplugged_max_V"]=act_low
    for ref in ("R137","R138","R139","R140"):
        check(20e-6*resistance("wheel",ref)*factor<.8,f"{ref}: input low not established")
    for ref in ("R142","R143"):
        check(20e-6*resistance("main",ref)*factor<.8,f"{ref}: disconnected MISO input low not established")
    # Read the U22 gate topology, then evaluate RUN and each phase for all binary
    # commands and connected/disconnected harness states. This is settled DC,
    # not cable bounce or power-ramp simulation.
    cases=0
    wp=boards["wheel"][1]
    gatepins=[(1,2,3),(4,5,6),(9,10,8),(12,13,11)]
    for connected,enable,run,a,b,c in itertools.product((False,True),repeat=6):
        state={"ACT_DRIVE_EN":enable if connected else False,
               "WHEEL_RUN_REQ":run if connected else False,
               "WHEEL_PWM_A":a if connected else False,
               "WHEEL_PWM_B":b if connected else False,
               "WHEEL_PWM_C":c if connected else False,"GND":False,"+3V3":True}
        for pa,pb,py in gatepins:
            ia,ib,oy=(wp.get(("U22",str(p))) for p in (pa,pb,py))
            if ia not in state or ib not in state:
                check(False,"Unknown U22 gate input")
                break
            state[oy]=state[ia] and state[ib]
        permitted=connected and enable and run
        check(state.get("WHEEL_RUN_EN")==permitted,"RUN truth table failure")
        for output,pwm in [("DRV_INHA",a),("DRV_INHB",b),("DRV_INHC",c)]:
            check(state.get(output)==(permitted and pwm),"PWM truth table failure")
        cases+=1
    local_power=review_local_power(boards,check)
    # U13's nominal limit is shared by the actuator branch. It is not a
    # guaranteed maximum, or a dedicated wheel-feed protective limit.
    nominal_limit=3334*(1/resistance("main","R42")+1/resistance("main","R43"))
    wire_rating=plan["signal_harness"]["candidate_cable"]["catalog_current_per_conductor_A_at_25C"]
    return_fault={"candidate_cable":plan["signal_harness"]["candidate_cable"]["mpn"],
                  "nominal_U13_branch_limit_A":nominal_limit,
                  "ideal_equal_sharing_15_contacts_A":nominal_limit/15,
                  "single_remaining_ground_contact_A_before_protection":nominal_limit,
                  "candidate_conductor_rating_A_at_25C":wire_rating,
                  "single_contact_screen_exceeds_rating":None if wire_rating is None else nominal_limit>wire_rating,
                  "accepted":False,
                  "required_for_prototype":disconnect_required,
                  "review_status":"Open" if disconnect_required else "Outside prototype scope by user decision; not validated",
                  "scope":"Nominal DC illustration only; no current-sharing, derating, fault-energy or interruption guarantee"}
    # Datasheet screening only: two LVC125A paths, each up to 6 ns at
    # 3.3 V +/-0.3 V, -40..125C, plus ADS7038 SCLK-to-SDO up to 16 ns.
    # Does not include cable, ESP32 input/setup delay, or phase adjustments.
    timing={"external_path_max_ns_before_cable":28,
            "unshifted_20MHz_half_cycle_ns":25,
            "unshifted_20MHz_margin_before_cable_ns":-3,
            "ideal_four_frame_burst_at_10MHz_us":4*(18/10+.7),
            "frequency_sweep":[{
                "SCLK_MHz":mhz,
                "unshifted_half_cycle_margin_before_cable_and_MCU_ns":500/mhz-28,
                "four_frames_with_four_0_7us_gaps_us":4*(18/mhz+.7),
                "remaining_in_12us_quiet_window_before_software_us":12-4*(18/mhz+.7)
            } for mhz in (1,5,10,20)],
            "assumptions":"16ns ADC plus 6ns forward and 6ns return buffer at datasheet loads; actual load, input delay and setup/hold unqualified",
            "status":"20 MHz target unaccepted; validate sampling phase and loaded cable"}
    open_gates=["Fully connected harness current sharing, voltage drop and conductor/connector heating",
                "Soldered-wire product, numbered continuity, ground conductors and fixture strain relief",
                "Connected-system power-ramp/output-clamp measurement; SN74LVC125A has no guaranteed Ioff",
                "SPI3/ADC2 timing including ESP32 input delay and cable loading",
                "Wheel-local effective capacitance/ESR, inrush and braking transient qualification",
                "PCB placement/routing, mechanical fit and assembly-panel DFM"]
    if disconnect_required:
        open_gates.append("FFC power-return-open and partial-insertion fault survival")
    return {"status":"Static schematic migration and DC checks only",
            "prototype_scope":plan["prototype_scope"],
            "netlist_sha256":{label:hashlib.sha256(path.read_bytes()).hexdigest()
                              for label,path in [("baseline",baseline),("main",main_path),("wheel",wheel_path)]},
            "component_counts":{b:len(c) for b,(c,p) in boards.items()},
            "preserved_baseline_pin_checks":checks,"harness_contacts_checked":32,
            "shutdown_truth_table_cases":cases,"bias_screen":bias_results,
            "wheel_rail":local_power,
            "spi3_screen":timing,"power_return_fault_screen":return_fault,
            "open_review_gates":open_gates,"errors":errors}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--wheel",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--require-reviewed",action="store_true")
    a=p.parse_args()
    report=verify(a.baseline,a.main,a.wheel)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return int(bool(report["errors"] or (a.require_reviewed and report["open_review_gates"])))


if __name__=="__main__":raise SystemExit(main())
