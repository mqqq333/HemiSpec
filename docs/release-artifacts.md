# Release artifacts

HemiSpec v0.1.0 is a public beta distributed through the GitHub Release and the source repository. The `hemispec-toolkit` project is **not currently public on PyPI**, so current installation instructions must not use `pip install hemispec-toolkit` as if it were available from PyPI.

## Current public v0.1.0 artifacts

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

For model-enabled development or GUI use, a source checkout is recommended:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[gui,model,classifier]
```

The hemisphere classifier is an optional downstream validation step. Installing the `classifier` extra does not make classifier execution mandatory.

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

The source repository contains code, documentation, tests, synthetic examples, and approved reusable model bundles tracked through Git LFS. Atlas payloads, real neuroimaging data, generated outputs, and additional custom model bundles must remain outside the public source tree unless their provenance, license, redistribution approval, checksums, and compatible versions are documented.

The lightweight Windows CLI/GUI artifacts do not embed PyTorch, atlas payloads, real MRI inputs, or generated outputs. Model-enabled workflows require a suitable Python/PyTorch environment and approved model assets from a Git-LFS checkout, the user cache, or an offline asset bundle.

## Post-release verification

The v0.1.0 artifacts were downloaded and checked after publication on June 29, 2026. The checksums matched, the Windows CLI displayed `--help`, and the downloaded wheel completed the public-safe synthetic quickstart. See [v0.1.0 release verification](developer/release-verification-v0.1.0.md).

## Related pages

- [Installation](installation.md)
- [Data and models](data-and-models.md)
- [External asset bundles](reference/asset-bundle.md)
- [Roadmap](developer/roadmap.md)
