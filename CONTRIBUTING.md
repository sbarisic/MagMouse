# Contributing to MagMouse

Read the [architecture](docs/architecture.md) and [roadmap](docs/roadmap.md)
before proposing a design change. Preserve `ideas.md` as the original notes;
record decisions and their rationale in the maintained documents.

- Identify whether values are targets, datasheet limits, calculations, or measurements.
- Link manufacturer documentation and record its revision when validating a part.
- Commit editable schematic/CAD source alongside release exports.
- Describe the changed behavior or circuit, validation, and unresolved issues.
- Do not commit credentials, local environments, build output, or vendor material
  whose redistribution rights have not been established.
- Use the license for the relevant directory. Add SPDX identifiers to new source
  files where comments are supported, and preserve third-party notices.

CAD verification, panel/fixture generation and simulation tools are documented
in their hardware and mechanical directories. See the
[repository content policy](docs/repository-contents.md) before adding generated
files. For documentation changes, verify local links and run `git diff --check`
on the edited text files. When adding the first firmware or host application,
document reproducible build and test commands and add corresponding CI.
