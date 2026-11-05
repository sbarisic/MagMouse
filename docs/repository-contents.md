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

## Local build cleanup, 2026-11-05

Removed 16,935 ignored scratch files (2,415 MiB), reducing the local workspace
from about 3.04 GiB to 695 MiB, excluding the root `.git` directory. These were
old routing attempts, repeated PCB snapshots, panel staging, obsolete helper
scripts, logs, old router downloads and unused Python dependency copies.

Retained local inputs and tools:

- `build/two-layer/python` and `build/simulation-python`: CAD and simulation dependencies.
- `build/sandwich/java25` and `freerouting-2.5.0.jar`: current router runtime.
- `build/sandwich/1206/original` and `baseline.json`: passive-package comparison inputs.
- `build/sandwich/assembly-spacing/original` and `baseline.json`: spacing and component identity checks.
- `build/sandwich/cost-reduction/*-before.kicad_pcb`, matching projects and `conversion.json`: via migration snapshots and guards.
- `build/revision-cleanup` and `build/local-cleanup`: cleanup manifests and verification evidence.
- Historical simulation waveforms, decks and vendor models: retained for result review without a new simulation run.

The `build/quote-cost/node_modules` junction was not traversed or deleted; its
target is excluded from these sizes. No tracked CAD, manufacturing output or
supplier record changed during the scratch cleanup. Retained files were checked
against pre-cleanup hashes. CAD helper imports, nine router geometry tests,
assembly spacing/outline/net/via checks, model hashes and simulation inventory
passed. Routing export now creates its output directory when it is missing;
this was checked with a new scratch directory.
