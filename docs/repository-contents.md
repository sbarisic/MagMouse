# Repository content policy

The 2026-11-05 cleanup removes superseded design copies from the current
checkout. Previous revisions remain in Git; history has not been rewritten.

| Content | Policy |
|---|---|
| Active Lower, Upper, Wheel and Encoder projects | Keep editable sources |
| Current panel, manufacturing files, 3D exports, quotes and reviews | Keep |
| Shared symbols, footprints and reusable CAD helpers | Keep in `hardware/common` |
| Combined Main schematic migration reference | Keep for partition checks |
| Original monolithic, modular four-layer and oversized two-layer designs | Retrieve from Git history |
| Old bench panel, fixtures, galleries and September quote exports | Retrieve from Git history |
| Exact submitted CAM archive and receipt | Keep unchanged under `hardware/bench/submissions` |
| Brake simulation | Keep code, frozen historical netlists, compact results and model provenance |
| Build dependencies, waveforms, downloaded vendor models and caches | Keep local and ignored |

See [previous revisions](history/README.md) for the pre-cleanup commit. The
historical brake study does not qualify the current design. Its netlists were
relocated without changes; the historical source labels in its results are
intentional provenance.

Use narrow ignore rules. Do not blanket-ignore CAD exports, ZIPs, JSON, CSV,
SVG or logs: some are required deliverables and evidence. Removing a revision
requires checking consumers, library paths, documentation and source hashes.
