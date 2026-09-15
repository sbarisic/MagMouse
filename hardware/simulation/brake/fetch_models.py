# SPDX-License-Identifier: GPL-3.0-or-later
"""Fetch TI models for local use, checking the exact model revisions used in the study."""
import argparse
import hashlib
import io
from pathlib import Path
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
MODELS = {
    'lm4040.lib': {
        'url': 'https://www.ti.com/lit/zip/snom526',
        'member': 'LM4040_NA2P5_TRANS.lib',
        'sha256': '8e1e252008162dd3ef6039b3169260d4f82e9b798876e015dbc1088d6d3eaaec',
    },
    'tlv1811.lib': {
        'url': 'https://www.ti.com/lit/zip/snom762',
        'member': 'tlv1811.lib',
        'sha256': '8a273cb9af327982356c4cd0071dd9a5183cd84967ed16a1f7c2c9b8db1124e8',
    },
}


def validate(data, model):
    if hashlib.sha256(data).hexdigest() != model['sha256']:
        raise ValueError('Model hash differs from the reviewed version; review it before updating the expected hash.')


def fetch(output, check_only=False):
    for name, model in MODELS.items():
        path = output / name
        if path.exists():
            validate(path.read_bytes(), model)
        elif check_only:
            raise FileNotFoundError(f'{path}: run fetch_models.py without --check')
        else:
            with urllib.request.urlopen(model['url'], timeout=60) as response:
                archive = response.read()
            with zipfile.ZipFile(io.BytesIO(archive)) as z:
                matches = [n for n in z.namelist() if n.rsplit('/', 1)[-1].lower() == model['member'].lower()]
                if len(matches) != 1:
                    raise ValueError(f'Expected exactly one {model["member"]} in {model["url"]}')
                data = z.read(matches[0])
            validate(data, model)
            output.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        print(f'{name}: reviewed SHA-256 verified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Verify existing local models without network access')
    parser.add_argument('--output', type=Path, default=HERE / 'models')
    args = parser.parse_args()
    fetch(args.output, args.check)
