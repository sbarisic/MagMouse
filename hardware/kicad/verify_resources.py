# SPDX-License-Identifier: GPL-3.0-or-later
"""Check the GPIO allocation against the exported schematic and S3 resources.

Run export_review.py first. No firmware execution or analog timing is simulated.
Capability baseline: ESP32-S3-MINI-1 datasheet v1.7 and ESP-IDF v5.5.1
components/soc/esp32s3/include/soc/soc_caps.h. See docs/interfaces.md.
"""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path(__file__).resolve().parent

# Manufacturer module pad numbers, not bare-SoC or development-board pin numbers.
MODULE_PADS = {**{g: g + 4 for g in range(22)}, 26: 26,
               33: 28, 34: 29, 35: 31, 36: 32, 37: 33, 38: 34,
               39: 35, 40: 36, 41: 37, 42: 38, 43: 39, 44: 40,
               45: 41, 46: 44, 47: 27, 48: 30}
CS_CAPACITY = {'SPI2': 6, 'SPI3': 3}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allocation', type=Path, default=PROJECT / 'gpio-allocation.json')
    parser.add_argument('--netlist', type=Path, default=ROOT / 'build/kicad-review/netlist.xml')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/kicad-review/resource-checks.json')
    args = parser.parse_args()
    spec = json.loads(args.allocation.read_text(encoding='utf-8'))
    xml = ET.parse(args.netlist).getroot()
    components = {c.get('ref'): c for c in xml.findall('./components/comp')}
    nets = {n.get('name'): {(p.get('ref'), p.get('pin')) for p in n.findall('node')}
            for n in xml.findall('./nets/net')}
    pin_net = {p: name for name, pins in nets.items() for p in pins}
    rows = spec['gpio']
    by_gpio = {r['gpio']: r for r in rows}
    by_net = {r['net']: r for r in rows}
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    check(spec['module'] == 'ESP32-S3-MINI-1-N8', 'Allocation is only valid for the N8 module')
    check(components['U3'].findtext('value') == spec['module'], 'Schematic MCU differs from allocation')
    check(len(rows) == len(by_gpio) == len(by_net) == 39, 'Duplicate or missing GPIO/net allocation')
    check(set(by_gpio) == set(MODULE_PADS), 'Allocation must cover exactly the exposed module GPIOs')
    for row in rows:
        gpio, pad, name = row['gpio'], row['module_pad'], row['net']
        check(MODULE_PADS.get(gpio) == pad, f'GPIO{gpio}: incorrect module pad {pad}')
        check(pin_net.get(('U3', str(pad))) == name, f'GPIO{gpio}: schematic net mismatch for {name}')
        if 'testpoint' in row:
            check(pin_net.get((row['testpoint'], '1')) == name, f'{name}: reservation pad missing')
        if 'bias' in row:
            bias = row['bias']
            ref = bias['ref']
            expected = {name, '+3V3' if bias['direction'] == 'up' else 'GND'}
            check({pin_net.get((ref, '1')), pin_net.get((ref, '2'))} == expected,
                  f'{name}: bias resistor wiring mismatch')
            value = components.get(ref)
            check(value is not None and value.findtext('value') == '10k' and bias['ohms'] == 10000,
                  f'{name}: expected a fitted 10k bias')
            if value is not None:
                check(value.find('./property[@name="dnp"]') is None, f'{name}: required bias is DNP')

    for gpio, name in {0: 'BOOT', 19: 'MCU_USB_DM', 20: 'MCU_USB_DP',
                       43: 'UART_TX', 44: 'UART_RX'}.items():
        check(by_gpio.get(gpio, {}).get('net') == name, f'Recovery/USB GPIO{gpio} moved')
    for gpio in (3, 45, 46):
        check(by_gpio.get(gpio, {}).get('bias', {}).get('direction') == 'down',
              f'GPIO{gpio}: explicit boot-low bias required')
    check(by_gpio.get(46, {}).get('direction') == 'reserved', 'GPIO46 must remain a boot-low spare')
    check(by_net.get('ACT_HEARTBEAT', {}).get('peripheral') == 'software',
          'Heartbeat must not be generated autonomously by PWM/RMT')

    buses = {b['host']: b for b in spec['spi']}
    check(set(buses) == set(CS_CAPACITY), 'Only SPI2 and SPI3 are available to this allocation')
    cs_names = []
    for host, bus in buses.items():
        check(len(bus['devices']) <= CS_CAPACITY.get(host, 0), f'{host}: hardware CS capacity exceeded')
        for field, direction in [('sclk', 'output'), ('mosi', 'output'), ('miso', 'input')]:
            row = by_net.get(bus[field], {})
            check(row.get('peripheral') == host and row.get('direction') == direction,
                  f'{host}: invalid {field} allocation')
        for device in bus['devices']:
            cs_names.append(device['cs'])
            row = by_net.get(device['cs'], {})
            check(row.get('peripheral') == host and row.get('direction') == 'output',
                  f'{device["name"]}: wrong CS host/direction')
    check(len(set(cs_names)) == len(cs_names) == 6, 'Six independent chip selects are required')
    check([d['name'] for d in buses.get('SPI3', {}).get('devices', [])] == ['ADS7038_2'],
          'Wheel ADC SPI3 must not share its bus')
    check({d['name'] for d in buses.get('SPI2', {}).get('devices', [])} ==
          {'ADS7038_1', 'PAW3950', 'ICM42688P', 'MA735', 'DRV8316R'}, 'SPI2 device inventory mismatch')

    wheel, buttons = spec['pwm']['wheel'], spec['pwm']['buttons']
    check(wheel['group'] == 0 and buttons['group'] == 1, 'Wheel and buttons require separate MCPWM groups')
    for name, pwm, signals in [('wheel', wheel, 3), ('buttons', buttons, 6)]:
        check(pwm['timer'] in range(3) and sorted(pwm['operators']) == [0, 1, 2],
              f'{name}: invalid MCPWM timer/operator resources')
        check(len(pwm['nets']) == len(set(pwm['nets'])) == signals, f'{name}: incorrect PWM output count')
        for net in pwm['nets']:
            row = by_net.get(net, {})
            check(row.get('peripheral') == f'MCPWM{pwm["group"]}' and row.get('direction') == 'output',
                  f'{net}: incorrect PWM group/direction')
    check(wheel['generators'] == ['A', 'A', 'A'], 'Wheel requires one generator per operator')
    check(buttons['generators'] == ['A', 'B'], 'Each button requires two independent generators')
    check(spec['rgb']['tx_channels'] == 1 and by_net.get(spec['rgb']['net'], {}).get('peripheral') == 'RMT',
          'RGB requires one RMT TX channel; four are available')
    check(wheel['fault_net'] == 'DRV_FAULT_N' and by_net['DRV_FAULT_N']['direction'] == 'input',
          'Wheel fault input missing')
    check(all(len(ch) == 8 for ch in spec['adc_channels'].values()), 'Each ADS7038 has eight multiplexed channels')
    check(spec['adc_channels']['ADS7038_2'][:3] == ['WHEEL_I_A', 'WHEEL_I_B', 'WHEEL_I_C'],
          'Wheel phase channels differ from selected architecture')

    # A wire-time lower bound and an unmeasured acceptance budget, NOT proof that
    # the ESP-IDF driver can achieve the target or that low-side currents are valid.
    timing = spec['wheel_timing_targets']
    low_us = (timing['frame_bits'] + timing['cs_setup_clocks'] + timing['cs_hold_clocks']) / timing['sclk_hz'] * 1e6
    frame_us = low_us + timing['cs_high_ns'] / 1000
    frames = timing['frames_per_triplet_including_pipeline_flush']
    check(frames >= 4, 'Three fresh pipelined conversions require a final result read')
    check(timing['cs_high_ns'] >= 600 and frame_us >= 1, 'ADC conversion/cycle timing is too short')
    check(timing['frame_bits'] == 16 and timing['sclk_hz'] <= 20000000, 'Unreviewed wheel SPI frame/clock')
    check(timing['burst_budget_us'] >= frames * frame_us, 'Burst target below physical wire-time bound')
    required_window = timing['burst_budget_us'] + timing['launch_jitter_budget_us'] + timing['settling_guard_budget_us']
    check(required_window <= timing['common_low_side_window_us'], 'Sampling budget exceeds common low-side window')
    check(timing['pwm_hz'] % timing['control_hz'] == 0, 'Control updates must divide the PWM carrier in this plan')
    report = {'module_gpio_count': len(rows), 'allocated_gpio_count': sum(r['direction'] != 'reserved' for r in rows),
              'reserved_gpio': [r['gpio'] for r in rows if r['direction'] == 'reserved'],
              'spi_devices': {h: len(b['devices']) for h, b in buses.items()},
              'mcpwm_outputs': {'group0_wheel': len(wheel['nets']), 'group1_buttons': len(buttons['nets'])},
              'wheel_wire_time_lower_bound_us': round(frames * frame_us, 3),
              'wheel_window_budget_us': required_window,
              'timing_acceptance': 'OPEN: SPI software overhead, ISR jitter, CSA/ADC settling and valid low-side windows must be measured',
              'consumer_circuits': 'Wheel/ADC2/MA735 and brake connected; optical/IMU/RGB remain interface reservations',
              'errors': errors}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
