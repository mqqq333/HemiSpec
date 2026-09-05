# Deployment

HemiSpec can be deployed as an installable Python package, a command wrapper, a Windows CLI/GUI build, or a model-enabled Python application. This page targets current `main`; archived versions are available on the [GitHub Releases page](https://github.com/mqqq333/HemiSpec/releases), and the PyPI project is not public.

## 1. Python package

Recommended for analysis servers, clusters, and model-enabled use:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e ".[model]"
git rev-parse HEAD
hemispec --help
```

Record the printed commit hash with deployment metadata.

Add GUI or optional classifier dependencies only when needed:

```bash
python -m pip install -e ".[gui,model]"
python -m pip install -e ".[gui,model,classifier]"
```

The classifier remains an optional downstream validation branch.

## 2. Windows command wrapper

After package installation, Windows users can run:

```bat
scripts\hemispec.cmd compute --help
```

The wrapper delegates to `python -m hemispec %*` and must not contain separate workflow logic.

## 3. Windows CLI and GUI builds

Install development and GUI dependencies, then build:

```powershell
cd "C:\path\to\HemiSpec"
python -m pip install -e ".[dev,gui]"
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
.\.venv-build\Scripts\python.exe -m pip install -e ".[dev,gui]" --no-build-isolation
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

Expected model assets follow the layout documented in [DGN model bundles](dgn-model-bundle.md). DGN checkpoints may be resolved from the Git LFS source checkout, the per-user cache populated from `main` Git LFS media, an explicit model root, or an approved offline bundle. Classifier assets should come from the local Git LFS checkout or an explicit local directory because the current classifier cache download is incomplete; see [Data and models](../data-and-models.md#current-cache-download-boundary).

```bash
hemispec models
hemispec infer \
  --direction L_to_R \
  --input-glob "<preprocessed-gm-dir>/*_GM_masked.nii.gz" \
  --out-dir "<hemispec-results>/recon_L_to_R" \
  --device cuda
```

The standard bilateral workflow exposes ROI export, classifier validation, and TRT validation as optional flags; none is required to generate voxel-wise ANS/RNS maps. The released classifier requires the compatible Glasser 1.5 mm labels `1..180` left / `1001..1180` right; a custom atlas is ROI-only. TRT requires at least two subjects with two scans each and matching `--trt-file-regex`, `--trt-session-a`, and `--trt-session-b` values. Use `--keep-intermediate` when later standalone validation needs `intermediate/combined_maps/`; direction-specific maps use a different suffix contract.

## Cluster usage

Use the Python package on Linux clusters:

```bash
module load python
cd /path/to/HemiSpec
python -m pip install -e ".[model]"
hemispec workflow \
  --input-glob "<preprocessed-gm-dir>/*_GM_masked.nii.gz" \
  --out-dir "<new-hemispec-results>/bilateral_run_001" \
  --device cuda
```

For a single direction followed by metric computation:

```bash
hemispec run \
  --direction L_to_R \
  --input-glob "<preprocessed-gm-dir>/*_GM_masked.nii.gz" \
  --recon-dir "<new-hemispec-results>/recon_L_to_R_run_001" \
  --metrics-dir "<new-hemispec-results>/ANS_RNS_thr0p15_run_001" \
  --device cuda
```

See [Data and models](../data-and-models.md) and [Release artifacts](../release-artifacts.md) for public/private asset boundaries.
