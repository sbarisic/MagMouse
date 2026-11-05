# SPDX-License-Identifier: GPL-3.0-or-later
"""Export and read a KiCad XML netlist."""
from pathlib import Path
import subprocess, sys
import xml.etree.ElementTree as ET
CLI=Path(sys.executable).with_name("kicad-cli.exe")

def export(path,out):
    subprocess.run([str(CLI),'sch','export','netlist','--format','kicadxml','-o',str(out),str(path)],check=True)
    tree=ET.parse(out).getroot()
    comps={c.get('ref'):c for c in tree.findall('./components/comp')}
    pins={(n.get('ref'),n.get('pin')):net.get('name') for net in tree.findall('./nets/net') for n in net.findall('node')}
    return comps,pins
