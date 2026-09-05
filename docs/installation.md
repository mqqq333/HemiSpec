# Installation

The supported public setup documented here targets the current `main` source tree. The package metadata still reports version `0.1.0`, but `main` contains functionality that is not present in the older `v0.1.0` tag or its archived packages. The `hemispec-toolkit` project is not currently public on PyPI.

## Recommended source install

Git LFS is required to retrieve the model files tracked under `assets/models/`:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e ".[gui,model,classifier]"
git rev-parse HEAD
```

Record the output of `git rev-parse HEAD` with each analysis. A branch name and the package version alone do not identify the source revision reproducibly.

PyTorch must be installed in the same Python or conda environment used to launch HemiSpec. Configure the appropriate CPU or CUDA PyTorch build before a model run.

The checked-out DGN and classifier assets are used directly from `assets/models/`. For classifier validation, use these local classifier assets or provide an explicit approved local classifier directory; do not rely on a cache pre-download as part of the recommended setup.

## Archived v0.1.0 release

The GitHub [`v0.1.0` release](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0) archives the original wheel, source distribution, and Windows artifacts. It is a historical release, not a package of current `main` features. In particular, the `v0.1.0` tag does not contain the current synthetic quickstart or model-cache downloader modules.

After downloading the archived wheel, its base CLI can be inspected with:

```bash
python -m pip install ./hemispec_toolkit-0.1.0-py3-none-any.whl
hemispec --help
```

Do not use the archived wheel as the installation path for current quickstart, model discovery, or model download documentation. See [Release artifacts](release-artifacts.md) for the exact archive contents.

## Development install

From a current source checkout:

```bash
python -m pip install -e ".[dev,gui]"
python -m pytest
python -m ruff check src tests
python -m mkdocs build --strict
```

The distribution name is `hemispec-toolkit`; the import path and CLI command are `hemispec`. Documentation should not present a PyPI install command until the project is actually public there.

## Neuroimaging prerequisites

The model-enabled workflow starts from preprocessed GM maps, not raw T1 images. The repository scripts depend on FSL tools including BET, FAST, FLIRT, and `fslmaths` to produce MNI152 1.5 mm `*_GM_masked.nii.gz` inputs.

Read [Input and preprocessing](input-preprocessing.md) before processing real data.

## GUI and model runtime

Launch `hemispec-gui` from the source environment containing PyTorch. HemiSpec discovers assets from explicit paths, environment variables, the Git-LFS checkout under `assets/models/`, or the per-user cache. Wheels and lightweight Windows artifacts do not embed PyTorch or the 300 MB+ DGN checkpoints. See [Data and models](data-and-models.md) for the current asset boundary.
