# Release artifacts

HemiSpec will be published as software artifacts, not only as a GitHub source repository. The public website should explain and link to those artifacts; it is not the final user-facing product by itself.

## Planned public artifacts

```text
hemispec-toolkit-<version>-py3-none-any.whl      Python/PyPI package
hemispec_toolkit-<version>.tar.gz                source distribution
hemispec.exe                                     Windows CLI executable
HemiSpec-GUI-Windows-<version>.zip               compiled GUI folder distribution
HemiSpec-Assets-<version>.zip                    optional external asset bundle
```

The same public Python API powers the CLI, GUI, and compiled app so that examples and validation behavior remain reproducible.

ANS/RNS metric usage should keep citation boundaries clear: the original ANS/RNS and cross-hemispheric DGN framework comes from Wang et al. 2024, *Patterns*; HemiSpec packages and extends that workflow for the current software release.

## Build commands

Build the lightweight package and, unless skipped, compiled Windows artifacts with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -Python "py -3.12"
```

Useful switches:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -Python "py -3.12" -SkipExe
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -Python "py -3.12" -SkipGuiSmoke
```

`-SkipGuiSmoke` should only be used in a headless environment where GUI launch checks are impossible.

## Release acceptance gates

A release is not considered public-ready until all relevant artifacts are built and checked together:

- `python -m build --wheel --sdist` creates lightweight `hemispec-toolkit` artifacts.
- `pip install dist/*.whl` exposes `hemispec` and `hemispec-gui` entry points.
- `hemispec --help` and documented subcommands run in a clean environment.
- `hemispec-gui` starts the compact standard-workflow GUI.
- The Windows app is built as a folder distribution and includes only approved runtime files.
- Any DGN model, atlas, classifier, or example data bundle has a manifest, checksums, license/provenance notes, and a compatibility version.
- Public artifacts and docs pass leak checks for private paths, keys, subject data, model payloads, and unpublished result claims.

## Source versus assets

The source repository should contain code, documentation, tests, examples, and asset manifests. Large DGN weights, classifier bundles, atlas NIfTI files, and non-public neuroimaging derivatives should be released separately with checksums, licenses, and model cards.

## Desktop release variants

- **Lightweight app:** compact GUI plus CLI/API utilities without bundling private model/data assets.
- **Model-enabled app:** compact GUI plus approved DGN/model/atlas/classifier assets and PyTorch runtime, packaged as a larger folder distribution or paired with an external asset bundle.

Both variants should use the public `hemispec` package internally.
