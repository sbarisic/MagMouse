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

# Explicit delta for the integrated motor encoder revision. Earlier snapshots
# remain immutable; validators apply these changes rather than rebasing history.
REMOVED_COMPONENTS = {
    'Lower': {f'TP{i}' for i in (1,*range(4,11),*range(16,34),*range(40,44))},
    'Upper': {f'TP{i}' for i in (2,3,*range(11,16))}, 'Wheel': set(),
}
LOWER_ADDITIONS = {'U42': ('TLV75533PDBVR','Package_TO_SOT_SMD:SOT-23-5',
    {'1':'ENC_5V','2':'GND','3':'ENC_5V','4':'unconnected-(U42-NC-Pad4)','5':'ENC_3V3'})}
LOWER_ADDITIONS['C105'] = ('100nF/50V','Capacitor_SMD:C_1206_3216Metric',{'1':'ENC_3V3','2':'GND'})
VALUE_CHANGES['Lower'].update({'C55':'1uF/50V','C64':'1uF/50V','J6':'GB1806 AS5048A encoder wires'})
PIN_CHANGES['Lower'] = {('U28','1'):'RGB_5V',('U28','6'):'ENC_5V',('C63','1'):'RGB_5V',
    ('R125','2'):'ENC_5V',('J6','1'):'ENC_5V',('C55','1'):'ENC_5V',
    ('U3','39'):'unconnected-(U3-TXD0-Pad39)',('U3','40'):'unconnected-(U3-RXD0-Pad40)'}

def expected_net(name, ref, pin, original):
    return PIN_CHANGES.get(name,{}).get((ref,pin),original.replace('CS_MA735','CS_ENCODER'))

def additions(name):
    return LOWER_ADDITIONS if name=='Lower' else NEW_COMPONENTS if name=='Wheel' else {}
