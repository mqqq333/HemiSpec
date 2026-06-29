# Deployment

This project can be deployed in four practical forms: PyPI package, CLI wrapper, GUI/EXE build, and model-enabled compiled app.

## 1. Python package

Recommended for analysis servers and clusters.

```bash
cd <hemispec-toolkit-checkout>
python -m pip install -e .
hemispec --help
```

For a fixed install:

```bash
python -m pip install .
```

For trained DGN inference:

```bash
python -m pip install .[model]
```

For local DGN inference and ROI export, use a PyTorch/CUDA-capable environment:

```text
<torch-env-python>
<torch-version>, CUDA available if using GPU
```

Use it without installing the package during development:

```powershell
$env:PYTHONPATH='src'
<torch-env-python> -m hemispec models --root .
```

For GUI-based PyTorch/CUDA DGN inference, set `HEMISPEC_D2L_PYTHON` and use:

```bat
set HEMISPEC_D2L_PYTHON=<torch-env-python>
scripts\hemispec_gui_d2l.cmd
```

`openpyxl` is a runtime dependency because the default/local Glasser label mapping
can be an `.xlsx` file.

## 2. CMD wrapper

After the package is installed, Windows users can run:

```bat
scripts\hemispec.cmd compute --help
```

The wrapper simply calls:

```bat
python -m hemispec %*
```

## 3. EXE / compiled GUI build

Install PyInstaller and build:

```powershell
cd <hemispec-toolkit-checkout>
python -m pip install -e .[dev]
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

The command-line executable should appear under:

```text
dist/hemispec.exe
```

The graphical executable should appear under:

```text
dist/hemispec_gui/hemispec_gui.exe
```

Important: `hemispec_gui.exe` is an onedir build. Keep the whole
`dist/hemispec_gui/` folder together; do not move only the `.exe`.

For a cleaner and smaller EXE, build in a minimal virtual environment rather
than a large analysis environment that contains unrelated packages such as
Torch, VTK, or full neuroimaging toolchains.

Example clean Windows build:

```powershell
python -m venv .venv-build
.\.venv-build\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv-build\Scripts\python.exe -m pip install -e .[dev] --no-build-isolation
.\.venv-build\Scripts\python.exe -m PyInstaller --clean --onedir --windowed --name hemispec_gui scripts\hemispec_gui_entry.py
```

The GUI executable appears under:

```text
dist/hemispec_gui/hemispec_gui.exe
```

The EXE is convenient for users without command-line Python experience, but the
Python package is easier to update and debug on clusters.

The current lightweight GUI EXE does not bundle PyTorch. It can open the compact standard-workflow GUI, but model-enabled DGN inference requires a PyTorch environment plus released DGN assets from Git LFS, the first-run cache download, an explicit model root, or a separate model-enabled/Torch bundle.

## 4. Model-enabled deployment

The current Python package/CLI includes trained DGN inference entry points and first-run download of the released model defaults. The current GUI intentionally exposes only the standard ANS/RNS workflow with optional ROI, classifier, and TRT branches; lower-level inference, compute, specificity, and classifier commands remain available through CLI/API. Rebuild the GUI EXE after source changes before treating `dist/` as a release artifact.

The model-enabled release should include or load:

```text
1. package-owned DGN runtime code
2. trained model checkpoint/weights
3. preprocessing/cropping rules
4. inference command and compact GUI standard workflow
5. reconstructed GM output naming convention
6. ANS/RNS compute and validation pipeline
```

Expected local model assets are organized as:

```text
reference/training_code/   reference only: architecture/crops/checkpoint format
outputs_bi_stable_L/       R_to_L model, right -> generated left
outputs_bi_stable_R/       L_to_R model, left -> generated right
```

The training scripts are not part of deployment. They should not be imported by
runtime code, exposed as commands, or required for GUI users.

See `docs/dgn_model_bundle.md` before changing the inference adapter.

Build a fully offline model-enabled app as a separate folder distribution, because
PyTorch/CUDA/model dependencies can make the bundle much larger. The lightweight app can instead use the released model cache/download path.

Recommended folder layout:

```text
HemiSpec_Model_App/
  hemispec_gui.exe
  _internal/
  models/
  configs/
  examples/
  docs/
```

See `docs/local_model_deployment_zh.md`.

## Cluster usage

Use the Python package form on Linux clusters. Example SLURM body:

```bash
module load python
cd <remote-hemispec-toolkit>
python -m pip install -e .
hemispec compute \
  --actual-glob "<preprocessed-gm-dir>/*.nii.gz" \
  --predicted-glob "<reconstruction-dir>/*_PRED_LR_full.nii.gz" \
  --out-dir "<hemispec-results>/ANS_RNS_thr0p15" \
  --gm-thresh 0.15 \
  --save-subject-maps
```

Model-enabled CLI example:

```bash
hemispec models
hemispec infer \
  --direction L_to_R \
  --input-glob "<preprocessed-gm-dir>/*_GM_masked.nii.gz" \
  --out-dir "<hemispec-results>/recon_L_to_R" \
  --device cuda
```

End-to-end DGN inference plus ANS/RNS compute:

```bash
hemispec run \
  --direction L_to_R \
  --input-glob "<preprocessed-gm-dir>/*_GM_masked.nii.gz" \
  --recon-dir "<hemispec-results>/recon_L_to_R" \
  --metrics-dir "<hemispec-results>/ANS_RNS_thr0p15" \
  --device cuda
```



