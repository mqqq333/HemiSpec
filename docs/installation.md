# Installation

HemiSpec is package-first, but the PyPI project is **not public yet**. The current v0.1.0 public beta is distributed through the GitHub Release and the source repository.

## Recommended: source checkout for model-enabled use

Use a source checkout when running DGN inference, the GUI, or classifier validation. Git LFS retrieves the released model bundles tracked under `assets/models/`:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[gui,model,classifier]
hemispec models --install --with-classifier  # optional cache pre-download
hemispec-gui
```

PyTorch must be installed in the same Python/conda environment used to launch HemiSpec. Configure the appropriate CPU or CUDA PyTorch build before a long model run.

## Install the v0.1.0 release wheel

Download `hemispec_toolkit-0.1.0-py3-none-any.whl` from the GitHub Release. For the base CLI and synthetic quickstart:

```bash
python -m pip install ./hemispec_toolkit-0.1.0-py3-none-any.whl
hemispec --help
hemispec quickstart --out-dir hemispec_quickstart
```

To request optional dependencies from the local wheel:

```bash
python -m pip install "./hemispec_toolkit-0.1.0-py3-none-any.whl[gui,model,classifier]"
```

If a local pip version does not accept extras on a wheel path, install the wheel first and then install the required optional packages explicitly.

## Development install

```bash
python -m pip install -e .[dev,gui]
python -m pytest
python -m ruff check src tests
python -m mkdocs build --strict
```

The distribution name in package metadata is `hemispec-toolkit`; the import path and CLI command are `hemispec`. A future PyPI publication should use the same distribution name, but documentation must not describe it as available until the project is actually public.

## Neuroimaging prerequisites

The model-enabled workflow starts from preprocessed GM maps, not raw T1 images. The repository study script `process_single_subject.sh` and the package variant depend on FSL tools including BET, FAST, FLIRT, and `fslmaths`; they convert one T1-weighted NIfTI into an MNI152 1.5 mm masked GM map named `*_GM_masked.nii.gz`.

Read [Input and preprocessing](input-preprocessing.md) before processing real data. That page specifies the script arguments, `121 × 145 × 121` released-model grid, `0.15` GM threshold, quality-control checks, and citations.

## GUI and compiled fallback artifacts

The recommended GUI path is `hemispec-gui` from a source or local-wheel environment containing PyTorch. The GUI exposes the GM input glob, output workspace, optional ROI atlas/label table, optional classifier validation, optional TRT reliability, run controls, logs, and an equivalent CLI command.

GitHub Release v0.1.0 also archives Windows fallback artifacts. Keep an onedir GUI distribution together; do not copy only its executable out of the folder.

## Model runtime

HemiSpec discovers model assets from explicit paths, environment variables, a Git-LFS checkout under `assets/models/`, or the per-user model cache. Wheels and lightweight executables do not embed PyTorch or the 300 MB+ model bundles. Missing released model assets can be downloaded from the GitHub Release into the cache when automatic download is enabled. See [Data and models](data-and-models.md).
