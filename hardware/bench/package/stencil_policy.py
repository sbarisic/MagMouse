"""Single source of truth for the selected Rev-A stencil geometry review."""
from dataclasses import dataclass


@dataclass(frozen=True)
class StencilPolicy:
    thickness_mm: float = 0.10
    minimum_area_ratio: float = 0.66
    polygon_error_mm: float = 0.001
    overlap_tolerance_mm2: float = 0.000001
    transform_tolerance_mm: float = 0.000002
    label: str = '0.10 mm — selected for Rev-A prototype'


POLICY = StencilPolicy()
# J1's USB-C footprint names both contacts of four physically shared lands.
# These exact coincident same-net definitions produce one opening per land.
USB_SHARED_LANDS = {frozenset(pair) for pair in
                    [('A1', 'B12'), ('A4', 'B9'), ('A9', 'B4'), ('A12', 'B1')]}


def exclude_non_reflow(board, wanted):
    """Remove all paste from non-reflow references, including wire lands."""
    import pcbnew as p
    removed = set()
    for f in board.GetFootprints():
        if f.GetReference() in wanted:
            continue
        for pad in f.Pads():
            layers = pad.GetLayerSet()
            for layer in (p.F_Paste, p.B_Paste):
                if pad.IsOnLayer(layer):
                    layers.RemoveLayer(layer)
                    removed.add(f.GetReference())
            pad.SetLayerSet(layers)
    return sorted(removed)


def physical_openings(footprint, policy=POLICY):
    """Union only the reviewed duplicate/compound aperture definitions."""
    import pcbnew as p
    from review_details import pad_polygon
    from shapely.ops import unary_union
    pads = [(q, pad_polygon(q, p.F_Paste)) for q in footprint.Pads() if q.IsOnLayer(p.F_Paste)]
    parents = list(range(len(pads)))
    def root(i):
        while parents[i] != i:
            i = parents[i]
        return i
    ref = footprint.GetReference()
    for i, (q, geom) in enumerate(pads):
        for j in range(i + 1, len(pads)):
            r, other = pads[j]
            overlap = geom.intersection(other).area
            if overlap <= policy.overlap_tolerance_mm2:
                continue
            shared_usb = (ref in ('J1', 'M_J1')
                          and frozenset((q.GetNumber(), r.GetNumber())) in USB_SHARED_LANDS
                          and q.GetNetname() == r.GetNetname() and geom.equals(other))
            sizes = {tuple(sorted(round(p.ToMM(v), 4) for v in (pad.GetSize().x, pad.GetSize().y))) for pad in (q, r)}
            compound_efuse = (ref in ('U12', 'U13', 'M_U12', 'M_U13')
                              and q.GetNumber() == r.GetNumber() == ''
                              and sizes == {(0.275, 0.6), (0.225, 0.65)}
                              and abs(overlap - 0.060481) <= policy.overlap_tolerance_mm2)
            assert shared_usb or compound_efuse, (ref, q.GetNumber(), r.GetNumber(), 'overlapping apertures')
            parents[root(j)] = root(i)
    groups = {}
    for i, item in enumerate(pads):
        groups.setdefault(root(i), []).append(item)
    return [(group[0][0], unary_union([geom for _, geom in group]),
             '/'.join(sorted({q.GetNumber() for q, _ in group})), len(group)) for group in groups.values()]


def verify_geometry(board, wanted, policy=POLICY):
    """Reject missing deposits, excluded paste, overlaps and poor release."""
    import pcbnew as p
    from review_details import pad_polygon
    from shapely.ops import unary_union
    from shapely.strtree import STRtree
    apertures = []
    found = set()
    for f in board.GetFootprints():
        ref = f.GetReference()
        local = []
        for pad in f.Pads():
            assert not pad.IsOnLayer(p.B_Paste), (ref, 'unexpected bottom paste')
        for pad, geom, numbers, primitive_count in physical_openings(f, policy):
            assert ref in wanted, (ref, 'paste on excluded reference')
            assert geom.is_valid and geom.area > 0, (ref, 'invalid aperture')
            ratio = geom.area / (geom.length * policy.thickness_mm)
            assert ratio >= policy.minimum_area_ratio, (ref, pad.GetNumber(), 'release ratio', ratio)
            local.append(geom)
            apertures.append((ref, numbers, geom, ratio))
            found.add(ref)
        if ref in wanted:
            assert local, (ref, 'missing all deposits')
            union = unary_union(local)
            # Plated anchors are hand soldered. Every SMT copper land must
            # still receive paste, including exposed pads with separate windows.
            for pad in f.Pads():
                if pad.GetAttribute() == p.PAD_ATTRIB_SMD and pad.IsOnLayer(p.F_Cu):
                    assert union.intersection(pad_polygon(pad, p.F_Cu)).area > policy.overlap_tolerance_mm2, (ref, pad.GetNumber(), 'missing land deposit')
    assert found == set(wanted), ('missing populated references', set(wanted) - found)
    geoms = [a[2] for a in apertures]
    tree = STRtree(geoms)
    for i, geom in enumerate(geoms):
        for j in tree.query(geom):
            j = int(j)
            if j > i:
                assert geom.intersection(geoms[j]).area <= policy.overlap_tolerance_mm2, (apertures[i][:2], apertures[j][:2], 'overlapping apertures')
    return min(a[3] for a in apertures)


def verify_transforms(actual, expected, offsets, policy=POLICY):
    """Compare complete aperture shapes against independent unit exports."""
    from collections import defaultdict
    from shapely import wkt
    from shapely.affinity import translate
    groups = defaultdict(list)
    for row in actual:
        groups[row['Reference'], row['Pad']].append(wkt.loads(row['Polygon_wkt']))
    for row in expected:
        name = row['Board']
        key = (name[0] + '_' + row['Reference'], row['Pad'])
        target = translate(wkt.loads(row['Polygon_wkt']), *offsets[name])
        choices = groups[key]
        index = next((i for i, geom in enumerate(choices)
                      if geom.hausdorff_distance(target) <= policy.transform_tolerance_mm
                      and geom.symmetric_difference(target).area <= policy.overlap_tolerance_mm2), None)
        assert index is not None, (key, 'panel/unit paste transformation mismatch')
        choices.pop(index)
    assert not any(groups.values()), 'Unexpected panel deposits'
