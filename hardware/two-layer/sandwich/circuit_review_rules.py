# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicitly reviewed differences from the immutable migration snapshots."""

VALUE_CHANGES = {
    'Lower': {r: '74LVC125APW,118' for r in ('U25','U29','U37')},
    'Upper': {'R36':'10k','R37':'10k','R38':'10k','R39':'11k'},
    'Wheel': {r: '74LVC125APW,118' for r in ('U24','U26')},
    'Encoder': {},
}
PIN_CHANGES = {'Wheel': {('U22','3'): 'WHEEL_RUN_REQUESTED'}}
NEW_COMPONENTS = {
    'U40': ('TPS3808G01DBVR','Package_TO_SOT_SMD:SOT-23-6',
        {'1':'WHEEL_VM_OK','2':'GND','3':'ACT_DRIVE_EN','4':'unconnected-(U40-CT-Pad4)',
         '5':'WHEEL_VM_SENSE','6':'+3V3'}),
    'U41': ('SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5',
        {'1':'WHEEL_RUN_REQUESTED','2':'WHEEL_VM_OK','3':'GND','4':'WHEEL_RUN_EN','5':'+3V3'}),
    'R147': ('105k','Resistor_SMD:R_1206_3216Metric',{'1':'ACT_5V','2':'WHEEL_VM_SENSE'}),
    'R148': ('10k','Resistor_SMD:R_1206_3216Metric',{'1':'WHEEL_VM_SENSE','2':'GND'}),
    'R149': ('10k','Resistor_SMD:R_1206_3216Metric',{'1':'+3V3','2':'WHEEL_VM_OK'}),
    'R150': ('100k','Resistor_SMD:R_1206_3216Metric',{'1':'WHEEL_RUN_EN','2':'GND'}),
    'C102': ('1nF/50V','Capacitor_SMD:C_1206_3216Metric',{'1':'WHEEL_VM_SENSE','2':'GND'}),
    'C103': ('100nF/50V','Capacitor_SMD:C_1206_3216Metric',{'1':'+3V3','2':'GND'}),
    'C104': ('100nF/50V','Capacitor_SMD:C_1206_3216Metric',{'1':'+3V3','2':'GND'}),
}
