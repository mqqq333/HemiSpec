# Release artifacts

HemiSpec is published as software artifacts, not only as a GitHub source repository. The v0.1.0 first public beta is available at [https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0).

## v0.1.0 public artifacts

```text
hemispec_toolkit-0.1.0-py3-none-any.whl          Python wheel
hemispec_toolkit-0.1.0.tar.gz                    source distribution
HemiSpec-CLI-v0.1.0-win64.exe                    Windows CLI executable
HemiSpec-GUI-v0.1.0-win64.zip                    compiled GUI folder distribution
HemiSpec-v0.1.0-SHA256SUMS.txt                   checksums
HemiSpec-v0.1.0-RELEASE_ARTIFACTS.txt            verification and artifact manifest
HemiSpec-Assets-<version>.zip                    optional offline/custom asset bundle for non-default assets
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
- Any additional/offline DGN model, atlas, classifier, or example data bundle has a manifest, checksums, license/provenance notes, and a compatibility version.
- Public artifacts and docs pass leak checks for private paths, keys, subject data, model payloads, and unpublished result claims.

## Source versus assets

The source repository contains code, documentation, tests, examples, and the approved reusable model bundles under Git LFS. Atlas NIfTI files, non-public neuroimaging derivatives, and any additional/custom model bundles should be released separately with checksums, licenses, and model cards unless explicitly approved for the repository.

## Desktop release variants

- **Lightweight app:** compact GUI plus CLI/API utilities; released models are resolved from Git LFS, cache download, or user-configured paths.
- **Model-enabled app:** compact GUI plus approved model/atlas assets and PyTorch runtime, packaged as a larger folder distribution or paired with an offline asset bundle.

Both variants should use the public `hemispec` package internally.


## Post-release verification

The v0.1.0 release was re-downloaded from GitHub on 2026-06-29. SHA256 checksums matched, the downloaded Windows CLI printed `--help`, and the downloaded wheel ran the public-safe synthetic quickstart in a fresh local verification workspace. See [v0.1.0 release verification](developer/release-verification-v0.1.0.md).

## Related pages

- [v0.1.0 release verification](developer/release-verification-v0.1.0.md)
- [External asset bundles](reference/asset-bundle.md)
- [Roadmap](developer/roadmap.md)
