# Deployment

HemiSpec can be deployed as an installable Python package, a command wrapper, a Windows CLI/GUI build, or a model-enabled Python application. The current public v0.1.0 package artifacts are distributed through GitHub Releases; the PyPI project is not public yet.

## 1. Python package

Recommended for analysis servers, clusters, and model-enabled use:

```bash
cd <hemispec-checkout>
python -m pip install -e .[model]
hemispec --help
```

Add GUI or optional classifier dependencies only when needed:

```bash
python -m pip install -e .[gui,model]
python -m pip install -e .[gui,model,classifier]
```

The classifier remains an optional downstream validation branch.

A downloaded v0.1.0 wheel can be installed directly:

```bash
python -m pip install ./hemispec_toolkit-0.1.0-py3-none-any.whl
```

## 2. Windows command wrapper

After package installation, Windows users can run:

```bat
scripts\hemispec.cmd compute --help
```

The wrapper delegates to `python -m hemispec %*` and must not contain separate workflow logic.

## 3. Windows CLI and GUI builds

Install development and GUI dependencies, then build:

```powershell
cd <hemispec-checkout>
python -m pip install -e .[dev,gui]
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

Expected local outputs:

```text
dist/hemispec.exe
dist/hemispec_gui/hemispec_gui.exe
```

`hemispec_gui.exe` is an onedir build. Keep the complete `dist/hemispec_gui/` folder together rather than moving only the executable.

For a clean build environment:

```powershell
python -m venv .venv-build
.\.venv-build\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv-build\Scripts\python.exe -m pip install -e .[dev,gui] --no-build-isolation
.\.venv-build\Scripts\python.exe -m PyInstaller --clean --onedir --windowed --name hemispec_gui scripts\hemispec_gui_entry.py
```

The lightweight GUI build does not embed PyTorch, atlas payloads, real MRI data, or generated outputs.

## 4. Model-enabled deployment

A model-enabled installation requires:

1. package-owned DGN runtime code;
2. approved generator checkpoints for `L_to_R` and `R_to_L`;
3. the preprocessing/crop contract;
4. a suitable PyTorch environment;
5. the reconstruction output naming contract;
6. ANS/RNS computation and optional validation settings.

Expected model assets follow the layout documented in [DGN model bundles](dgn-model-bundle.md). They may be resolved from a Git-LFS source checkout, the per-user cache, an explicit model root, or an approved offline asset bundle.

```bash
hemispec models
hemispec infer \
  --direction L_to_R \
  --input-glob "<preprocessed-gm-dir>/*_GM_masked.nii.gz" \
  --out-dir "<hemispec-results>/recon_L_to_R" \
  --device cuda
```

The standard bilateral workflow exposes ROI export, classifier validation, and TRT validation as optional flags; none of them is required to generate voxel-wise ANS/RNS maps.

## Cluster usage

Use the Python package on Linux clusters:

```bash
module load python
cd <remote-hemispec-checkout>
python -m pip install -e .[model]
hemispec workflow \
  --input-glob "<preprocessed-gm-dir>/*_GM_masked.nii.gz" \
  --out-dir "<hemispec-results>/bilateral" \
  --device cuda
```

For a single direction followed by metric computation:

```bash
hemispec run \
  --direction L_to_R \
  --input-glob "<preprocessed-gm-dir>/*_GM_masked.nii.gz" \
  --recon-dir "<hemispec-results>/recon_L_to_R" \
  --metrics-dir "<hemispec-results>/ANS_RNS_thr0p15" \
  --device cuda
```

See [Data and models](../data-and-models.md) and [Release artifacts](../release-artifacts.md) for public/private asset boundaries.
