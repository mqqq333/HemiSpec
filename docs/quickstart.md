# Quick start

This page shows the current HemiSpec workflow. Public branding, CLI examples, and the Python API use HemiSpec naming consistently.

The CLI shape in this page was checked against the current migration toolkit interface on 2026-06-29. The public package name is `hemispec-toolkit`; public package upload and real-data asset releases are still pending.

!!! note "Command naming"
    Use `hemispec` for the command-line interface and `hemispec-gui` for the graphical interface.

!!! warning "Real-data assets are not bundled yet"
    The source repository and public website do not ship public DGN weights, real atlas payloads, classifier bundles, or real subject data. Real-data commands use placeholders such as `<model-root>` and `<atlas-path>` until approved release assets are added.

## Public-safe synthetic compute demo

For a first CLI smoke test that does not require private MRI data, model weights, or atlas assets, use the HemiSpec Toolkit synthetic quickstart. It creates toy NIfTI files, mock reconstruction outputs, and a toy atlas, then runs `hemispec compute` with subject maps and ROI export:

```powershell
cd <hemispec-toolkit-checkout>
python -m pip install -e .
powershell -ExecutionPolicy Bypass -File examples\synthetic_quickstart\run_synthetic_quickstart.ps1 -Python python
```

The generated maps are not anatomical data and should only be used to verify the public command/file contract.

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

Install the GUI extra and start the launcher:

```bash
python -m pip install -e .[gui]
hemispec-gui
```

The GUI is intentionally a thin standard-workflow interface. Normal users choose:

1. **Input GM maps**: a glob such as `derivatives/*_GM_masked.nii.gz`.
2. **Output workspace**: where reconstructions, ANS/RNS maps, tables, and logs are written.
3. **Optional ROI table**: atlas NIfTI and label table, defaulting to configured local Glasser assets when available.
4. **Optional validation**: hemisphere-classifier validation and TRT reliability.
5. **Run HemiSpec**: the GUI shows the equivalent `hemispec workflow` command for reproducibility.

Voxel-wise and subject-level ANS/RNS maps are the primary output. ROI tables are optional downstream features. Classifier validation requires ROI table export.

## 3. Inspect available local model bundles

```bash
hemispec models --root <model-root>
```

Model weights are not part of the source repository. See [Data and models](data-and-models.md) before publishing or distributing trained weights.

## 4. Run the bilateral workflow from CLI

The GUI maps to the same public CLI/API path:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --model-root <model-root> \
  --out-dir outputs/hemispec_workflow
```

Optional ROI table with a custom atlas:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --model-root <model-root> \
  --out-dir outputs/hemispec_workflow \
  --roi-atlas atlas/custom_atlas.nii.gz \
  --roi-label-table atlas/custom_labels.xlsx
```

Skip ROI table export when only voxel-wise maps are needed:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --model-root <model-root> \
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
  --model-root <model-root> \
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
  --model-root <model-root> \
  --recon-dir outputs/recon_L_to_R \
  --metrics-dir outputs/specificity_L_to_R
```

## 6. Validate maps

```bash
hemispec trt \
  --maps-dir outputs/hemispec_workflow/subject_maps \
  --out-dir outputs/trt_validation

hemispec specificity \
  --maps-dir outputs/hemispec_workflow/subject_maps \
  --out-dir outputs/structural_specificity
```

## What is not ready yet

- A standalone `report` command.
- A standalone `roi` command.
- Public real-data preprocessing assets, DGN model bundles, atlas payloads, classifier bundles, and approved real sample data.
- A fully public handedness reproduction workflow.
