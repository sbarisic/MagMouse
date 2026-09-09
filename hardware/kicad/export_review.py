# SPDX-License-Identifier: GPL-3.0-or-later
"""Export review artifacts from the editable KiCad project (Python standard library)."""

import argparse
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kicad-cli', help='Path to KiCad 10 kicad-cli executable')
    parser.add_argument('--schematic', type=Path,
                        default=Path(__file__).resolve().parent / 'MagMouse.kicad_sch')
    parser.add_argument('--output', type=Path, help='Separate review directory for this board')
    args = parser.parse_args()
    cli = args.kicad_cli or shutil.which('kicad-cli')
    if not cli:
        for base in [Path(os.environ.get('LOCALAPPDATA', '.')) / 'Programs',
                     Path(os.environ.get('ProgramFiles', '.'))]:
            candidate = base / 'KiCad/10.0/bin/kicad-cli.exe'
            if candidate.is_file():
                cli = str(candidate)
                break
    if not cli:
        parser.error('KiCad CLI not found; supply --kicad-cli PATH')

    sch = args.schematic.resolve()
    project = Path(__file__).resolve().parent
    default_name = 'kicad-review' if sch == project / 'MagMouse.kicad_sch' else sch.stem.lower() + '-review'
    out = args.output.resolve() if args.output else project.parents[1] / 'build' / default_name
    out.mkdir(parents=True, exist_ok=True)
    commands = [
        ['sch', 'export', 'svg', '-o', str(out / 'sheets'), str(sch)],
        ['sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(out / 'netlist.xml'), str(sch)],
        ['sch', 'erc', '--format', 'json', '-o', str(out / 'erc.json'), str(sch)],
    ]
    for command in commands:
        subprocess.run([cli, *command], check=True)

    netlist = ET.parse(out / 'netlist.xml').getroot()
    grouped = {}
    missing = []
    count = sourced = 0
    for comp in netlist.findall('./components/comp'):
        props = {p.get('name'): p.get('value', '') for p in comp.findall('property')}
        if 'exclude_from_bom' in props or 'dnp' in props:
            continue
        fields = {f.get('name'): f.text or '' for f in comp.findall('./fields/field')}
        ref = comp.get('ref')
        value = comp.findtext('value', '')
        fp = comp.findtext('footprint', '')
        lcsc, mpn = fields.get('LCSC', ''), fields.get('MPN', '')
        status = fields.get('Sourcing Status', '')
        key = (value, fp, lcsc, mpn, status)
        grouped.setdefault(key, []).append(ref)
        count += 1
        sourced += bool(lcsc)
        gaps = [name for name, data in [('Footprint', fp), ('LCSC', lcsc), ('MPN', mpn)] if not data]
        if gaps:
            missing.append({'reference': ref, 'missing': gaps})
    with (out / 'DRAFT-bom.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.writer(stream)
        writer.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #', 'MPN', 'Sourcing Status', 'Quantity'])
        for (value, fp, lcsc, mpn, status), refs in grouped.items():
            writer.writerow([value, ','.join(refs), fp, lcsc, mpn, status, len(refs)])
    erc = json.loads((out / 'erc.json').read_text(encoding='utf-8'))
    violations = [v for s in erc['sheets'] for v in s.get('violations', [])]
    summary = {
        'status': 'REVIEW ONLY - NOT FABRICATION APPROVAL',
        'kicad_version': erc.get('kicad_version'),
        'bom_components': count, 'components_with_lcsc': sourced,
        'incomplete_components': missing,
        'erc_errors': sum(v['severity'] == 'error' for v in violations),
        'erc_warnings': sum(v['severity'] == 'warning' for v in violations),
    }
    (out / 'review-status.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f'Review exports: {out}')
    print(f'{count} BOM components; {sourced} with LCSC numbers; {len(missing)} with incomplete fields.')
    print(f"ERC: {summary['erc_errors']} errors, {summary['erc_warnings']} warnings.")
    return 2 if missing or violations else 0


if __name__ == '__main__':
    raise SystemExit(main())
