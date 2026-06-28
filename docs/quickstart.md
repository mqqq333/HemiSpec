# Quick start

This page shows the current HemiSpec workflow. Public branding, CLI examples, and the Python API use HemiSpec naming consistently.

The CLI shape in this page was checked against the current migration toolkit interface on 2026-06-28. The public package name is `hemispec-toolkit`; public package upload and real-data asset releases are still pending.

!!! note "Command naming"
    Use `hemispec` for the command-line interface and `hemispec-gui` for the graphical interface.

!!! warning "Real-data assets are not bundled yet"
    The homepage does not ship public model weights, real atlas files, or real sample data yet. The synthetic compute demo below is generated locally and is safe to publish; real-data commands still use placeholders such as `<model-root>` and `<atlas-path>` until approved release assets are added.


## Public-safe synthetic compute demo

For a first CLI smoke test that does not require private MRI data, model weights,
or atlas assets, use the HemiSpec Toolkit synthetic quickstart. It creates toy
NIfTI files, mock reconstruction outputs, and a toy atlas, then runs
`hemispec compute` with subject maps and ROI export:

```powershell
cd <hemispec-toolkit-checkout>
python -m pip install -e .
powershell -ExecutionPolicy Bypass -File examples\synthetic_quickstart\run_synthetic_quickstart.ps1 -Python python
```

The generated maps are not anatomical data and should only be used to verify the
public command/file contract.

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

## 2. Inspect available local model bundles

```bash
hemispec models --root <model-root>
```

Model weights are not yet part of this homepage repository. See [Data and models](data-and-models.md) before publishing or distributing trained weights.

## 3. Run one-direction DGN inference

```bash
hemispec infer \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --direction L_to_R \
  --model-root <model-root> \
  --out-dir outputs/recon_L_to_R
```

Use `--direction R_to_L` for the opposite reconstruction direction.

## 4. Compute ANS/RNS maps

```bash
hemispec compute \
  --actual-glob "derivatives/*_GM_masked.nii.gz" \
  --predicted-glob "outputs/recon_L_to_R/*_PRED_LR_full.nii.gz" \
  --out-dir outputs/specificity_L_to_R \
  --save-subject-maps
```

ROI export is currently part of `compute`, `run`, and `workflow` via `--roi-atlas` and `--roi-out-csv`; it is not a separate public `roi` subcommand yet.

For the lower-level `compute` command, pass `--save-subject-maps` when you need per-subject maps for downstream validation. The higher-level `run` command writes subject-level maps by default and uses `--no-subject-maps` to disable them.

## 5. Run inference and compute together

```bash
hemispec run \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --direction L_to_R \
  --model-root <model-root> \
  --recon-dir outputs/recon_L_to_R \
  --metrics-dir outputs/specificity_L_to_R
```

The `run` command writes subject-level maps by default; use `--no-subject-maps` only when you do not need downstream validation or ROI extraction.

## 6. Run the bilateral workflow

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --model-root <model-root> \
  --out-dir outputs/hemispec_workflow

# Optional ROI table with a custom atlas:
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --model-root <model-root> \
  --out-dir outputs/hemispec_workflow \
  --roi-atlas atlas/custom_atlas.nii.gz \
  --roi-label-table atlas/custom_labels.xlsx
```

The workflow command is the closest current entry point to the planned HemiSpec Toolkit experience: bilateral DGN inference and voxel-wise/subject-level ANS/RNS maps as the primary output. ROI tables are optional atlas-derived outputs, hemisphere-classifier validation is opt-in with `--run-classifier`, and TRT reliability remains optional.

## 7. Validate maps

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
- Public real-data preprocessing assets, model bundles, atlas assets, and approved real sample data. A synthetic compute demo exists for CLI smoke testing.
- A fully public handedness reproduction workflow.
