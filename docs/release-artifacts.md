# Release artifacts

HemiSpec will be published as software artifacts, not only as a GitHub source
repository. The public website should explain and link to those artifacts; it is
not the final user-facing product by itself.

## Planned public artifacts

```text
hemispec-toolkit  PyPI package
hemispec          command-line interface
hemispec-gui      GUI entry point
HemiSpec app      compiled Windows folder distribution
```

The same public Python API should power the CLI, GUI, and compiled app so that
examples and validation behavior remain reproducible.

ANS/RNS metric usage should keep citation boundaries clear: the original
ANS/RNS and cross-hemispheric DGN framework comes from Wang et al. 2024,
*Patterns*; HemiSpec packages and extends that workflow for the current
software release.

## Release acceptance gates

A release is not considered public-ready until all relevant artifacts are built
and checked together:

- `python -m build --wheel` creates a lightweight `hemispec-toolkit` wheel.
- `pip install dist/*.whl` exposes `hemispec` and `hemispec-gui` entry points.
- `hemispec --help` and the documented subcommands run in a clean environment.
- The Windows app is built as a folder distribution and includes only approved
  runtime files.
- Any model, atlas, or example data bundle has a manifest, checksums, license or
  provenance notes, and a compatibility version.
- Public artifacts and docs pass leak checks for private paths, keys, subject
  data, and unpublished result claims.

## Source versus assets

The source repository should contain code, documentation, tests, examples, and
asset manifests. Large DGN weights, classifier bundles, atlas NIfTI files, and
non-public neuroimaging derivatives should be released separately with checksums,
licenses, and model cards.

## Desktop release variants

- **Lightweight app:** GUI plus non-Torch workflows for inspection, ANS/RNS
  computation, ROI export, and validation.
- **Model-enabled app:** GUI plus approved DGN/model/atlas assets and PyTorch
  runtime, packaged as a larger folder distribution.

Both variants should use the public `hemispec` package internally.
