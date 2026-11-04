"""Check exported board solids and viewer meshes. Requires build123d and trimesh.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib
import json
from pathlib import Path

from build123d import import_step
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / '3d'
DIMENSIONS = {'Lower': (70, 100), 'Upper': (70, 100), 'Wheel': (70, 67),
              'Encoder': (14, 18), 'Panel': (238, 114)}


def main():
    manifest = json.loads((OUT / 'manifest.json').read_text())
    result = {}
    for name, dimensions in DIMENSIONS.items():
        entry = manifest[name]
        assert hashlib.sha256((ROOT / entry['source']).read_bytes()).hexdigest() == entry['source_sha256']
        board = import_step(OUT / (name + '-bare.step'))
        solids = list(board.solids())
        assert len(solids) == 1 and board.is_valid and board.volume > 0, name
        size = board.bounding_box().size
        actual = [size.X, size.Y, size.Z]
        # These two-layer exports use 35 um copper and 10 um mask per side.
        # KiCad's bare-board export contains the dielectric substrate only.
        expected = [*dimensions, entry['exported_substrate_expected_mm']]
        assert all(abs(a - b) < .002 for a, b in zip(actual, expected)), (name, actual, expected)
        # Probe the actual STEP solid, so a valid bounding box cannot conceal
        # a missing optical aperture or uncut encoder corner.
        bounds=board.bounding_box();z=(bounds.min.Z+bounds.max.Z)/2
        opening_check=None
        if name in ('Lower','Panel'):
            ox,oy=(0,0) if name=='Lower' else (7,7)
            assert not solids[0].is_inside((35.5+ox,-52.31-oy,z))
            assert solids[0].is_inside((35.5+ox,-40-oy,z))
            opening_check=True
        if name=='Encoder':
            assert not solids[0].is_inside((50.5,-50.5,z))
            assert not solids[0].is_inside((63.5,-50.5,z))
            assert solids[0].is_inside((57,-64.5,z))
        scene = trimesh.load(OUT / (name + '.glb'), force='scene')
        assert scene.geometry and scene.bounds is not None
        assert all(mesh.vertices.size and mesh.faces.size for mesh in scene.geometry.values())
        result[name] = {'bare_step_valid': True, 'substrate_solids': 1,
                        'substrate_bounds_mm': actual, 'substrate_volume_mm3': board.volume,
                        'glb_meshes': len(scene.geometry), 'glb_bounds_m': scene.bounds.tolist(),
                        'source_hash_matches': True,
                        'optical_aperture_open_in_step':opening_check,
                        'encoder_corner_cuts_verified':True if name=='Encoder' else None}
        print(name, 'valid solid', [round(x, 4) for x in actual], 'GLB meshes', len(scene.geometry), flush=True)
    (OUT / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
