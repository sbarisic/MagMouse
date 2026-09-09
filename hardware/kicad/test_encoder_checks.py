# SPDX-License-Identifier: GPL-3.0-or-later
"""Reject reversed wiring, supply bypasses and mistakes in the assembly split."""
import copy
import json
from pathlib import Path
import unittest
from verify_encoder import ROOT, read_netlist, verify


class EncoderChecks(unittest.TestCase):
    def setUp(self):
        self.main = read_netlist(ROOT/'build/kicad-review/netlist.xml')
        self.encoder = read_netlist(ROOT/'build/encoder-review/netlist.xml')
        self.harness = json.loads((ROOT/'hardware/encoder/harness.json').read_text(encoding='utf-8'))

    def report(self):
        return verify(self.main,self.encoder,self.harness)['errors']

    def test_current_pair_passes(self):
        self.assertEqual(self.report(), [])

    def test_reversed_harness_fails(self):
        for wire in self.harness['connections']:
            wire['encoder_pin'] = 9-wire['encoder_pin']
        self.assertTrue(any('Harness must' in e for e in self.report()))

    def test_missing_ground_conductor_fails(self):
        self.harness['connections'].pop(3)
        self.assertTrue(any('all three grounds' in e for e in self.report()))

    def test_unswitched_encoder_supply_fails(self):
        self.main[1]['J6','1'] = '+3V3'
        self.assertTrue(any('J6.1' in e for e in self.report()))

    def test_clock_buffer_bypass_fails(self):
        self.main[1]['J6','3'] = 'SPI_SCLK'
        self.assertTrue(any('J6.3' in e for e in self.report()))

    def test_swapped_daughterboard_spi_pins_fail(self):
        self.encoder[1]['J7','3'],self.encoder[1]['J7','8'] = self.encoder[1]['J7','8'],self.encoder[1]['J7','3']
        self.assertTrue(any('J7.3' in e for e in self.report()))

    def test_duplicate_sensor_in_main_bom_fails(self):
        self.main[0]['U27'] = copy.deepcopy(self.encoder[0]['U27'])
        self.assertTrue(any('both board BOMs' in e for e in self.report()))

    def test_missing_local_bypass_fails(self):
        del self.encoder[0]['C62']
        self.assertTrue(any('only J7, U27 and C62' in e for e in self.report()))


if __name__ == '__main__':
    unittest.main()
