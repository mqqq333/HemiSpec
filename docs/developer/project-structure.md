# Project structure

HemiSpec is organized as an installable Python package plus explicitly approved runtime assets. The public repository documents the complete software and file contracts without publishing private MRI data, generated study outputs, or assets whose redistribution has not been approved.

```text
.
|-- src/hemispec/                         # Python API, CLI, GUI, and workflows
|   `-- resources/preprocess/             # packaged preprocessing helper
|-- tests/                                # synthetic/unit regression tests
|-- examples/
|   |-- synthetic_quickstart/             # public-safe generated NIfTI example
|   `-- input_sample/                     # local, git-ignored MRI input area; README only is public
|-- docs/                                 # user, method, reference, and developer documentation
|-- scripts/                              # release and local launcher helpers
|   `-- research/                         # local research utilities, not public runtime API
|-- assets/
|   |-- atlases/glasser/                  # public README/manifest; atlas payload stays local until approved
|   `-- models/                           # approved DGN/classifier bundles tracked with Git LFS
|-- data/                                 # local validation data, not tracked
|-- outputs/                              # generated outputs, not tracked
|-- reference/                            # local papers/training references, not tracked
|-- pyproject.toml                        # package metadata and tool configuration
|-- MANIFEST.in                           # source-distribution inclusion/exclusion policy
|-- CONTRIBUTING.md                       # engineering and validation rules
`-- CHANGELOG.md                          # release history
```

## Public source and local-only material

Tracked public source may include:

- package code and small package-owned resources under `src/hemispec/`;
- tests and examples based on synthetic or tiny generated fixtures;
- README, documentation, release scripts, and manifest templates;
- asset README files that define expected local placement and provenance fields;
- approved reusable DGN and classifier bundles under `assets/models/` through Git LFS.

Keep the following local and ignored unless explicit release approval and redistribution rights are documented:

- real subject-level MRI/NIfTI files, including files placed in `examples/input_sample/`;
- generated reconstructions, ANS/RNS maps, ROI tables, and validation results;
- unapproved model checkpoints or classifier bundles;
- atlas NIfTI files and label tables;
- private paths, subject identifiers, credentials, and unpublished result summaries.

The public runnable example is `examples/synthetic_quickstart/`; `examples/input_sample/` is only a local input location and must not be treated as redistributable example data.

## Runtime asset discovery

Model and atlas discovery is centralized in `hemispec.paths` and follows this order:

1. explicit CLI/API/GUI override;
2. environment variables such as `HEMISPEC_DGN_MODEL_ROOT`;
3. local project assets under `assets/`, when present;
4. the per-user cache populated by model download;
5. legacy root folders such as `outputs_bi_stable_L/R`, for compatibility only.

The release wheel remains lightweight: it contains package code and small resources, not large model checkpoints, atlas payloads, or subject-level examples. Model-enabled runs obtain approved DGN/classifier assets from a Git-LFS source checkout, the per-user cache, or an explicitly configured offline asset bundle.
