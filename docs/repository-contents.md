# Repository content policy

The September 15, 2026 audit covered all 921 previously tracked paths and the new brake-simulation files. No previously tracked file was identified as a cache, executable, credential file or accidental temporary output requiring removal. Existing generated deliverables are deliberate project records, not blanket candidates for deletion.

| Content | Decision | Reason |
|---|---|---|
| Schematics, boards, local libraries, editable mechanical CAD and scripts | Keep | Maintained design and reproducible toolchain |
| Documentation, licenses, BOMs, purchasing and interface records | Keep | Design decisions, sourcing and assembly requirements |
| Historical monolithic design, partition studies and dated quote packages | Keep | Reference geometry, regression inputs and cost provenance; not current fabrication releases |
| Current panel/package, validation logs and JSON, stencil, Gerbers/drills | Keep | Reviewable manufacturing deliverables with source/hash evidence |
| Copper/router galleries, fixture STEP/STL/drawings and archive copies | Keep | Requested visual review and printable/manufacturing handoff; copies belong to self-contained packages |
| Previously submitted CAM archive and receipt | Keep unchanged | Exact supplier submission record |
| Brake simulation code, model URLs/hashes, compact results, plots and failed-model log | Add | Reproducibility and review evidence |
| Brake waveform arrays, per-run decks and routine logs | Ignore, retain locally | Approximately 100 MB of reproducible detailed run output |
| Downloaded TI models and decks containing their text | Ignore, retain locally | Redistribution rights not established; fetch exact reviewed models from TI |
| Local scratch directories, Python caches/environments and build dependencies | Ignore | Machine-specific or disposable work |

Use narrow ignore rules. Do not globally ignore `.log`, `.json`, `.csv`, `.svg`, `.zip`, Gerber files or CAD exports: several are required evidence or deliverables here. `.gitignore` does not remove tracked files; any future removal must also check documentation links, generators, tests and package hashes.

The simulation README documents how to download and verify models and regenerate omitted artifacts. Simulation hash inventories include those local artifacts as provenance; their absence from a fresh checkout is intentional. Hash-covered evidence is preserved byte-for-byte through `.gitattributes`.

This audit did not regenerate boards, rerun electrical simulations, delete local outputs, rewrite Git history or alter the immutable CAM submission.
