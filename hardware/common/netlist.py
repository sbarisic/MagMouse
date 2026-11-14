# SPDX-License-Identifier: GPL-3.0-or-later
"""Export and read a KiCad XML netlist."""
from pathlib import Path
import subprocess, sys, uuid
import xml.etree.ElementTree as ET
CLI=Path(sys.executable).with_name("kicad-cli.exe")

def export(path,out):
    out=Path(out)
    temporary=out.with_name(out.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        subprocess.run([str(CLI),'sch','export','netlist','--format','kicadxml','-o',str(temporary),str(path)],check=True)
        tree=ET.parse(temporary).getroot()
        # Windows readers may memory-map the previous export. Replacing the
        # complete file avoids truncating that mapping and preserves a valid
        # previous netlist if KiCad fails before producing the new one.
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    comps={c.get('ref'):c for c in tree.findall('./components/comp')}
    pins={(n.get('ref'),n.get('pin')):net.get('name') for net in tree.findall('./nets/net') for n in net.findall('node')}
    return comps,pins
