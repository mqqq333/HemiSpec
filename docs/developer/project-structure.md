# Project Structure

HemiSpec Toolkit is organized as a deployable Python package plus local-only research assets. The public repository should make the runtime contract clear without committing private MRI data, trained weights, or generated outputs.

```text
.
├── src/hemispec/                         # importable package: API, CLI, GUI, workflows
│   └── resources/preprocess/             # small packaged preprocessing helper script
├── tests/                                # synthetic/unit regression tests
├── examples/                             # public-safe examples and IO contracts
│   ├── synthetic_quickstart/             # generated toy NIfTI example
│   └── input_sample/                     # local/approved input placeholder only
├── docs/                                 # developer, architecture, deployment, and method notes
├── scripts/                              # release and local launcher helpers; no core runtime logic
│   └── research/                         # local research utilities, not public runtime API
├── assets/                               # local runtime assets; payloads ignored, manifests tracked
│   ├── atlases/glasser/                  # local Glasser atlas + label table, not tracked
│   └── models/                           # local DGN/classifier bundles, not tracked
├── data/                                 # local validation data, not tracked
├── outputs/                              # generated outputs, not tracked
├── reference/                            # papers/reference materials/training references, not tracked
├── pyproject.toml                        # package metadata and tool configuration
├── MANIFEST.in                           # source distribution inclusion/exclusion policy
├── CONTRIBUTING.md                       # engineering and validation rules
└── CHANGELOG.md                          # release history
```

## Public source vs local assets

Tracked public source should include:

- `src/hemispec/` package code and small package-owned resources.
- Tests based on synthetic/tiny generated fixtures.
- README, docs, examples, release scripts, and manifest templates.
- Asset README files that describe expected local placement.

Ignored local/private material includes:

- real subject-level MRI/NIfTI files;
- DGN checkpoints and classifier bundles;
- atlas payload files unless redistribution is explicitly approved;
- generated outputs, cache folders, and compiled release folders.

## Runtime asset discovery

Model and atlas discovery is centralized in `hemispec.paths` and follows this order:

1. Explicit CLI/API/GUI override, if supplied.
2. Environment variables such as `HEMISPEC_DGN_MODEL_ROOT`.
3. Local project assets under `assets/` when present.
4. Legacy root folders such as `outputs_bi_stable_L/R`, for compatibility only.

The PyPI package remains lightweight and does not include large DGN checkpoints, classifier bundles, atlas payloads, or subject-level examples. Compiled app distributions can ship approved external assets beside the application folder with a manifest and checksums.
