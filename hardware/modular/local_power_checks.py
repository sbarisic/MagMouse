"""Wheel-local power inventory and conditional arithmetic, never bench acceptance."""
import math


def capacitance_uF(value):
    value = value.split('/')[0]
    for suffix, scale in [('uF', 1), ('nF', .001), ('pF', .000001)]:
        if value.endswith(suffix):
            return float(value[:-len(suffix)]) * scale
    raise ValueError(f'Unparsed capacitance: {value}')


def rail_caps(components, pins):
    return [{'ref': ref, 'nominal_uF': capacitance_uF(c.findtext('value'))}
            for ref, c in components.items() if ref.startswith('C') and
            {pins.get((ref, '1')), pins.get((ref, '2'))} == {'ACT_5V', 'GND'}]


def review(boards, check):
    comps, pins = boards['wheel']
    expected = {
        'C90': ('100uF/16V', '16SVPC100M', 'C136275', 'Capacitor_SMD:CP_Elec_6.3x5.9'),
        'D6': ('SMBJ6.0A', 'SMBJ6.0A', 'C83270', 'Diode_SMD:D_SMB'),
        'R146': ('4.7k', '0603WAF4701T5E', 'C23162', 'Resistor_SMD:R_0603_1608Metric'),
    }
    credited_bulk_uF = 0
    for ref, spec in expected.items():
        c = comps.get(ref)
        if c is None:
            check(False, f'{ref}: missing wheel-local power component')
            continue
        fields = {f.get('name'): f.text for f in c.findall('./fields/field')}
        actual = (c.findtext('value'), fields.get('MPN'), fields.get('LCSC'), c.findtext('footprint'))
        identity_ok = actual == spec
        check(identity_ok, f'{ref}: local power part identity/value/footprint changed; recalculate')
        polarity_ok = pins.get((ref, '1')) == 'ACT_5V' and pins.get((ref, '2')) == 'GND'
        check(polarity_ok, f'{ref}: local rail connection/polarity wrong')
        if ref == 'C90' and identity_ok and polarity_ok:
            credited_bulk_uF = capacitance_uF(c.findtext('value'))

    caps = rail_caps(comps, pins)
    nominal = sum(c['nominal_uF'] for c in caps)
    connected = nominal + sum(c['nominal_uF'] for c in rail_caps(*boards['main']))
    # Panasonic: +/-20% initial at 120Hz/20C, +/-20% change after endurance.
    # Not a guarantee at operating temperature or at transient frequencies.
    initial_floor = credited_bulk_uF * .8
    endurance_screen = initial_floor * .8
    check(endurance_screen >= 47, 'Wheel-local bulk selection has insufficient screened capacitance')
    # Values below remain acceptance assumptions. Do not promote nominal C,
    # 100kHz/20C catalog ESR or this lumped model to actual hardware limits.
    target_cap, target_esr, response, current = 47e-6, .100, 10e-6, .4
    # Existing brake network's conservative rounded upper threshold. Its part
    # identities and every original pin remain guarded against the baseline.
    brake_on_ceiling = 6.175
    dv_cap = current * response / target_cap
    dv_esr = current * target_esr
    peak = brake_on_ceiling + dv_cap + dv_esr
    check(peak < 6.5, 'Conditional brake response has no voltage margin')
    # TPS25947 nominal application equation SR[V/ms] = 2000 / CdVdt[pF].
    # Main U13/C26 topology is guarded by the baseline migration check.
    ramp_cap = boards['main'][0]['C26']
    slew = 2000 / (capacitance_uF(ramp_cap.findtext('value')) * 1e6)
    bleed = 4700
    return {
        'capacitors': caps, 'nominal_uF': round(nominal, 3),
        'required_effective_uF': 47, 'meets_effective_requirement': False,
        'bulk_initial_tolerance_floor_uF': initial_floor,
        'bulk_initial_and_endurance_screen_uF': endurance_screen,
        'mlcc_credit_in_effective_screen_uF': 0,
        'status': 'Local parts added; effective C, ESR, inrush and transient qualification pending',
        'connected_system_nominal_uF': round(connected, 3),
        'nominal_slew_V_per_ms': slew,
        'nominal_capacitor_only_inrush_mA': connected * slew,
        'nominal_wheel_stored_energy_at_6_5V_mJ': .5 * nominal * 1e-3 * 6.5**2,
        'bleed_nominal_6_5_to_0_5V_s_no_generation': bleed * nominal * 1e-6 * math.log(13),
        'bleed_dissipation_at_6_5V_mW': 6.5**2 / bleed * 1000,
        'conditional_transient': {
            'minimum_measured_capacitance_uF': target_cap * 1e6,
            'maximum_effective_series_resistance_ohm': target_esr,
            'maximum_returned_bus_current_A': current,
            'maximum_running_brake_response_us': response * 1e6,
            'brake_on_upper_screen_V': brake_on_ceiling,
            'capacitive_rise_V': dv_cap, 'resistive_step_V': dv_esr,
            'peak_before_unmodeled_inductance_V': peak,
            'remaining_margin_to_6_5V_V': 6.5 - peak,
            'cold_start_200us_from_2_4V_screen_V': 2.4 + current * 200e-6 / target_cap + dv_esr,
            'accepted': False,
        },
        'secondary_tvs': {'ref': 'D6', 'standoff_V': 6, 'specified_pulse_clamp_V': 10.3,
                          'enforces_6_5V_limit': False},
    }
