# Release artifacts

HemiSpec should be released as aligned software artifacts, not just as a source
folder.

## Public package

- PyPI distribution name: `hemispec-toolkit`
- Import path: `hemispec`
- Console command: `hemispec`
- GUI command: `hemispec-gui`

The PyPI package should remain lightweight and should not include private MRI
data, unpublished result tables, or large model/atlas binaries unless those files
have an explicit public license and release decision.

Documentation for any ANS/RNS-capable release must preserve method attribution:
ANS/RNS and the original cross-hemispheric DGN framework come from Wang et al.
2024, *Patterns*; HemiSpec packages and extends the workflow rather than
claiming to originate those metrics.

## Compiled software

The user-facing desktop release should be a compiled/folder distribution built
from the same public API used by the CLI and PyPI package.

Recommended Windows layouts:

```text
HemiSpec-Desktop/
  hemispec_gui.exe
  _internal/
  docs/
  examples/
  ASSET_MANIFEST.md

HemiSpec-Model-App/
  hemispec_gui.exe
  _internal/
  models/
  atlases/
  configs/
  docs/
  ASSET_MANIFEST.md
```

Use a lightweight GUI build for inspection and non-Torch workflows. Build a
separate model-enabled app when PyTorch/CUDA and approved DGN weights should be
included or colocated.


## Release acceptance gates

A HemiSpec release should be treated as a software release, not a source-code
snapshot. Before publishing, verify these artifacts from a clean environment:

```text
PyPI/wheel       dist/hemispec_toolkit-*.whl installs import path hemispec
CLI             hemispec --help and documented subcommands pass
GUI entry       hemispec-gui starts the workbench
Windows app     dist/hemispec_gui/hemispec_gui.exe works as a complete folder
Asset bundle    optional, approved, manifest + checksum + license/provenance
```

The default PyInstaller specs intentionally do not bundle local `assets/` or
PyTorch/TorchVision/Torchaudio. Model-enabled releases should use a separate
model-enabled build path and should add or colocate only an approved asset
bundle with `ASSET_MANIFEST.md`.

Build the lightweight wheel and, unless skipped, the compiled CLI/GUI artifacts with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1
```

Use `-SkipExe` when you only want the PyPI wheel validation path. Use
`-SkipGuiSmoke` only in a headless environment where GUI launch checks are not
possible.

## Asset policy

Large assets should be distributed through an explicit artifact channel such as
GitHub Releases, Zenodo/OSF, or institutional storage. Each released asset bundle
needs:

- version and date,
- source/provenance,
- license and citation requirements,
- expected local path or environment variable,
- checksum,
- preprocessing assumptions,
- compatibility with the `hemispec-toolkit` version.

Supported environment variables include:

```text
HEMISPEC_ASSET_ROOT
HEMISPEC_DGN_MODEL_ROOT
HEMISPEC_CLASSIFIER_MODEL_DIR
HEMISPEC_GLASSER_ATLAS
HEMISPEC_GLASSER_LABEL_TABLE
```
