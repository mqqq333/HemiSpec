# Release artifacts

This page separates the archived `v0.1.0` GitHub Release from the current `main` source tree. Both currently report package version `0.1.0`, but they do not have the same feature set. The `hemispec-toolkit` project is **not currently public on PyPI**.

## Archived v0.1.0 artifacts

The v0.1.0 GitHub Release provides:

```text
hemispec_toolkit-0.1.0-py3-none-any.whl          Python wheel
hemispec_toolkit-0.1.0.tar.gz                    source distribution
HemiSpec-CLI-v0.1.0-win64.exe                    Windows CLI executable
HemiSpec-GUI-v0.1.0-win64.zip                    Windows GUI folder distribution
HemiSpec-v0.1.0-SHA256SUMS.txt                   checksums
HemiSpec-v0.1.0-RELEASE_ARTIFACTS.txt            release manifest
```

Download the required artifact from the [v0.1.0 GitHub Release](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0). To install the downloaded wheel:

```bash
python -m pip install ./hemispec_toolkit-0.1.0-py3-none-any.whl
hemispec --help
```

The archived `v0.1.0` tag does not contain the current synthetic quickstart or `model_assets` downloader. Use a current source checkout for current documentation and model-enabled workflows:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e ".[gui,model,classifier]"
git rev-parse HEAD
```

Record the commit hash with each analysis because the package version alone does not distinguish the current source from the archived tag. Use the classifier assets in the Git-LFS checkout or an explicitly configured local directory.

## Scientific attribution

The cross-hemispheric DGN framework and both specificity measures originate from Wang et al. (2024): **ANS** is **absolute neuroanatomical specificity**, and **RNS** is **relative neuroanatomical specificity**. Cite the original paper separately from the software release; see [Citation](citation.md).

## Build commands

Maintainers can build package and Windows artifacts with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -Python "py -3.12"
```

Useful variants:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -Python "py -3.12" -SkipExe
powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -Python "py -3.12" -SkipGuiSmoke
```

Use `-SkipGuiSmoke` only in a headless environment where the GUI launch check cannot run.

## Release acceptance checks

Before publishing a release:

- build the wheel and source distribution with `python -m build --wheel --sdist`;
- validate package metadata with `python -m twine check dist/hemispec_toolkit-*.whl dist/hemispec_toolkit-*.tar.gz`;
- install the built wheel locally and run `hemispec quickstart --out-dir <tmpdir>`;
- check `hemispec --help`, `hemispec-gui`, and the documented subcommands in a clean environment;
- verify checksums and the release manifest;
- confirm that no private paths, credentials, subject data, unapproved model/atlas payloads, or unpublished result claims are included.

Uploading to PyPI is a separate future release action. Documentation should describe PyPI installation only after the project is publicly available there.

## Source and asset boundary

The current source repository contains code, documentation, tests, synthetic examples, and approved reusable model bundles tracked through Git LFS. These current-source features must not be attributed to the archived `v0.1.0` packages. Atlas payloads, real neuroimaging data, generated outputs, and additional custom model bundles must remain outside the public source tree unless their provenance, license, redistribution approval, checksums, and compatible versions are documented.

The lightweight Windows CLI/GUI artifacts do not embed PyTorch, atlas payloads, real MRI inputs, or generated outputs. Model-enabled workflows require a suitable Python/PyTorch environment and approved model assets from a Git-LFS checkout, the user cache, or an offline asset bundle.

## Post-release verification

The v0.1.0 artifacts were downloaded and checked after publication on June 29, 2026. The recorded checksums matched, the Windows CLI displayed `--help`, and the wheel was imported from a clean environment. There is no retained evidence that the downloaded wheel ran the later synthetic quickstart. See [v0.1.0 release verification](developer/release-verification-v0.1.0.md).

## Related pages

- [Installation](installation.md)
- [Data and models](data-and-models.md)
- [External asset bundles](reference/asset-bundle.md)
- [Roadmap](developer/roadmap.md)
