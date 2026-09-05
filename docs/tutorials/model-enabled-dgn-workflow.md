# Model-enabled DGN workflow

The PyPI project is not public. This page targets a current source checkout from `main`; archived versions are available on the [GitHub Releases page](https://github.com/mqqq333/HemiSpec/releases).

This page documents the current model-enabled workflow using the reusable parameters tracked with Git LFS under `assets/models/`. Real MRI inputs and generated outputs are not distributed.

## Status

- **Synthetic compute-only demo:** available without model assets; see [Quick start](../quickstart.md).
- **Model-enabled source checkout:** available when cloned with Git LFS and run from a PyTorch environment.
- **DGN cache download:** current `main` can download missing DGN checkpoints from the repository's Git LFS media; the complete classifier bundle must come from a local Git LFS checkout or another approved local directory.

## Setup

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e ".[gui,model,classifier]"
git rev-parse HEAD
```

Record the printed commit hash with the analysis. On Windows, run these commands from the conda environment that contains the desired PyTorch/CUDA build.

## Bundled model layout

```text
assets/models/dgn/
  outputs_bi_stable_L/ckpts/best_netG_L.pth
  outputs_bi_stable_R/ckpts/best_netG_R.pth
assets/models/hemisphere_classifier/
  OUT_noICBM_train_ICBM_external_saved_models/
  OUT_noICBM_train_ICBM_external_saved_models_paired_residual/
```

HemiSpec discovers this source-checkout layout automatically. `HEMISPEC_DGN_MODEL_ROOT` and `HEMISPEC_CLASSIFIER_MODEL_DIR` can select other approved local assets. Current `main` can populate the DGN cache with `hemispec models --install`; do not use `--with-classifier` as an installation recipe because required `feature_names.csv` media URLs currently return HTTP 404. See [Data and models](../data-and-models.md#current-cache-download-boundary).

## GUI path

Start the GUI with:

```bash
hemispec-gui
python scripts/hemispec_gui_entry.py  # equivalent source-checkout entry
```

The setup status card reports:

- DGN model: found / missing;
- Glasser atlas: found / missing;
- classifier bundle: found / missing;
- PyTorch: available / missing.

Choose either a folder containing `*_GM_masked.nii.gz` files or a glob such as `derivatives/*_GM_masked.nii.gz`, choose an output workspace, and click **Run HemiSpec**. The log prints per-file inference, compute, and merge progress; **Stop** requests cancellation after the current file.

ROI table export is optional. Any atlas on the input grid may be used for ROI-only export. The released classifier specifically requires its compatible Glasser 1.5 mm atlas and label table, with labels `1..180` on the left and `1001..1180` on the right. Uncheck **Export ROI table** when you only need voxel-wise/subject-level ANS/RNS maps.

## CLI path

First confirm that HemiSpec discovers both DGN directions:

```bash
hemispec models
```

Then run the standard bilateral workflow on approved preprocessed gray-matter maps:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_workflow_run_001
```

Classifier validation requires the compatible Glasser assets; do not substitute a custom atlas:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_classifier_run_001 \
  --roi-atlas "$HEMISPEC_GLASSER_ATLAS" \
  --roi-label-table "$HEMISPEC_GLASSER_LABEL_TABLE" \
  --classifier-model-dir "assets/models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models" \
  --run-classifier
```

TRT requires at least two subjects with two scans each. For example, prepare `sub-001_run-01_GM_masked.nii.gz`, `sub-001_run-02_GM_masked.nii.gz`, and the corresponding pair for `sub-002`; then make the filename parser and session values explicit:

```bash
hemispec workflow \
  --input-glob "derivatives/sub-*_run-*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_trt_run_001 \
  --run-trt \
  --trt-file-regex "(?P<subject>sub-[0-9]+)_(?P<session>run-[0-9]+)" \
  --trt-session-a run-01 \
  --trt-session-b run-02 \
  --keep-intermediate
```

The TRT regex is applied to merged names such as `sub-001_run-01_ANS.nii.gz`, after `_GM_masked` has been removed. Use `--keep-intermediate` when `intermediate/combined_maps/` will later be passed to standalone validation; direction-specific maps use a different suffix contract. Every example uses a fresh output directory because workflow output directories are not intended to be reused.

## Release boundary

The repository model bundles let users run inference without retraining. They do not include raw MRI data, generated outputs, or private manuscript-only analysis tables. Additional public assets should include provenance, checksums, compatible HemiSpec version, preprocessing assumptions, and license/citation notes; see [External asset bundles](../reference/asset-bundle.md).
