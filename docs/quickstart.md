# Quick start

This page shows the current HemiSpec workflow using the recommended PyPI-first path. Public branding, CLI examples, and the Python API use HemiSpec naming consistently.

The CLI shape in this page was checked against the current toolkit interface on 2026-06-29. The public package name is `hemispec-toolkit`; the import path and command remain `hemispec`.

!!! note "Command naming"
    Use `hemispec` for the command-line interface and `hemispec-gui` for the graphical interface.

!!! note "Released model assets"
    The source repository includes reusable DGN checkpoints and hemisphere-classifier bundles through Git LFS. Wheel/PyPI installs keep those large binaries outside the wheel, then auto-download the released assets into the user cache on the first model run. No retraining is required.

## Public-safe synthetic compute demo

For a first CLI smoke test that does not require private MRI data, model weights, atlas assets, or a source checkout, install HemiSpec from PyPI and run the built-in synthetic quickstart:

```bash
python -m pip install hemispec-toolkit
hemispec --help
hemispec quickstart --out-dir hemispec_quickstart
```

For editable source development, replace the PyPI install with `python -m pip install -e .`; source-tree wrapper scripts remain under `examples/synthetic_quickstart/`.

The generated maps are not anatomical data and should only be used to verify the public command/file contract.

## Model-enabled install from PyPI

Install the released package from PyPI with model runtime extras in the environment that has the desired PyTorch build, then optionally pre-download the released model assets:

```bash
python -m pip install "hemispec-toolkit[gui,model,classifier]"
hemispec models --install --with-classifier
hemispec-gui
```

If you skip `hemispec models --install`, the first `hemispec workflow`, `hemispec infer`, `hemispec run`, or GUI model run downloads the released DGN checkpoints automatically.

For a Git-LFS source checkout, install from the repository:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[gui,model,classifier]
python scripts/hemispec_gui_entry.py
```

The GUI setup card should show DGN model and classifier bundle as found after Git LFS checkout or after model cache download. PyTorch availability depends on the Python/conda environment used to launch the GUI.

Troubleshooting: if classifier validation reports `No module named 'numpy._core'`, update to the latest HemiSpec checkout. The runtime includes a compatibility shim for classifier bundles saved with NumPy 2.x so older conda environments can still load them.

## 1. Prepare gray-matter maps

Run the preprocessing workflow on T1-weighted MRI data to produce masked gray-matter maps. The toolkit packages the reference preprocessing script under `src/hemispec/resources/preprocess/`; real preprocessing still depends on local FSL installation and validated site-specific assumptions:

```bash
bash src/hemispec/resources/preprocess/process_single_subject_GM_v2_reorient.sh \
  input_T1.nii.gz \
  derivatives/sub-001
```

Expected output:

```text
derivatives/sub-001_GM_masked.nii.gz
```

## 2. Run the standard GUI workflow

Start the package-installed launcher from the same environment that has PyTorch installed:

```bash
python -m pip install "hemispec-toolkit[gui,model,classifier]"
hemispec-gui
```

For a Git-LFS source checkout, use `python scripts/hemispec_gui_entry.py` instead.

The GUI is intentionally a thin standard-workflow interface. Its setup status card reports whether DGN models, Glasser atlas files, classifier bundles, and PyTorch are found before a long run. Normal users choose:

1. **Input GM maps**: a glob such as `derivatives/*_GM_masked.nii.gz`.
2. **Output workspace**: where final voxel_maps/, tables/, and optional validation/ outputs are written. Reconstructions are removed by default unless intermediate outputs are kept.
3. **Optional ROI table**: atlas NIfTI and label table, defaulting to configured local Glasser assets when available.
4. **Optional validation**: hemisphere-classifier validation and TRT reliability.
5. **Run HemiSpec**: the GUI shows the equivalent `hemispec workflow` command for reproducibility.

The primary output is four voxel-wise maps per subject: ANS.L, ANS.R, RNS.L, and RNS.R under voxel_maps/. ROI tables are optional downstream features. Classifier validation requires ROI table export.

## 3. Inspect bundled model bundles

```bash
hemispec models
```

This lists both DGN directions when the Git-LFS checkout or user cache contains the released checkpoints. To pre-download from a wheel/PyPI install, run `hemispec models --install --with-classifier`. See [Data and models](data-and-models.md) before publishing or distributing additional trained weights.

## 4. Run the bilateral workflow from CLI

The GUI maps to the same public CLI/API path inside the PyPI-installed environment:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow
```

Optional ROI table with a custom atlas:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --roi-atlas atlas/custom_atlas.nii.gz \
  --roi-label-table atlas/custom_labels.xlsx
```

Skip ROI table export when only voxel-wise maps are needed:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow \
  --no-roi-table
```

The workflow command runs bilateral DGN inference and writes voxel-wise/subject-level ANS/RNS maps as the primary output. ROI tables are optional atlas-derived outputs; hemisphere-classifier validation is opt-in with `--run-classifier`; TRT reliability is opt-in with `--run-trt`.

## 5. Lower-level CLI commands

One-direction DGN inference:

```bash
hemispec infer \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --direction L_to_R \
  --out-dir outputs/recon_L_to_R
```

Compute ANS/RNS from existing actual and reconstructed maps:

```bash
hemispec compute \
  --actual-glob "derivatives/*_GM_masked.nii.gz" \
  --predicted-glob "outputs/recon_L_to_R/*_PRED_LR_full.nii.gz" \
  --out-dir outputs/specificity_L_to_R \
  --save-subject-maps
```

Run inference and compute together for one direction:

```bash
hemispec run \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --direction L_to_R \
  --recon-dir outputs/recon_L_to_R \
  --metrics-dir outputs/specificity_L_to_R
```

## 6. Validate maps

For the standard workflow, prefer enabling validation during the workflow run so results are written to predictable folders:

```bash
hemispec workflow   --input-glob "derivatives/*_GM_masked.nii.gz"   --out-dir outputs/hemispec_workflow   --run-classifier   --run-trt
```

This writes classifier outputs under `outputs/hemispec_workflow/validation/hemi_classify/` and TRT outputs under `outputs/hemispec_workflow/validation/trt/`.

If you want to run standalone validation commands later on workflow-generated merged maps, keep intermediates:

```bash
hemispec workflow   --input-glob "derivatives/*_GM_masked.nii.gz"   --out-dir outputs/hemispec_workflow   --keep-intermediate

hemispec trt   --maps-dir outputs/hemispec_workflow/intermediate/combined_maps   --out-dir outputs/trt_validation
```

## What is not ready yet

- A standalone `report` command.
- A standalone `roi` command.
- Public real-data preprocessing assets and approved real sample data.
- Public redistribution decision for any atlas payloads not already cleared.
- A fully public behavioral-phenotype reproduction workflow.
