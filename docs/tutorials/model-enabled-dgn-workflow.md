# Model-enabled DGN workflow

This page documents the current model-enabled workflow for running HemiSpec with the reusable released model parameters. The DGN checkpoints and hemisphere-classifier bundles are tracked with Git LFS under `assets/models/`; wheel/PyPI installs can download the same files into the user cache. Real MRI inputs and generated outputs are not distributed.

## Status

- **Synthetic compute-only demo:** available without model assets; see [Quick start](../quickstart.md).
- **Model-enabled source checkout:** available when cloned with Git LFS and run from a PyTorch environment.
- **Wheel/PyPI / lightweight desktop installs:** model-enabled through first-run download of the released checkpoints into the user cache; PyTorch is still required in the active environment.

## Setup

PyPI install:

```bash
python -m pip install "hemispec-toolkit[gui,model,classifier]"
hemispec models --install --with-classifier  # optional pre-download
```

Source checkout:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e .[gui,model,classifier]
```

On Windows, run those commands from the conda environment that contains the desired PyTorch/CUDA build.

## Bundled model layout

```text
assets/models/dgn/
  outputs_bi_stable_L/ckpts/best_netG_L.pth
  outputs_bi_stable_R/ckpts/best_netG_R.pth
assets/models/hemisphere_classifier/
  OUT_noICBM_train_ICBM_external_saved_models/
  OUT_noICBM_train_ICBM_external_saved_models_paired_residual/
```

HemiSpec discovers this layout automatically. Wheel/PyPI installs use the same layout in the user model cache after automatic download. You only need `HEMISPEC_DGN_MODEL_ROOT` or `HEMISPEC_CLASSIFIER_MODEL_DIR` when you want to override the released defaults.

## GUI path

Start the GUI with:

```bash
hemispec-gui                 # PyPI install
python scripts/hemispec_gui_entry.py  # source checkout
```

The setup status card reports:

- DGN model: found / missing;
- Glasser atlas: found / missing;
- classifier bundle: found / missing;
- PyTorch: available / missing.

Choose either a folder containing `*_GM_masked.nii.gz` files or a glob such as `derivatives/*_GM_masked.nii.gz`, choose an output workspace, and click **Run HemiSpec**. The log prints per-file inference, compute, and merge progress; **Stop** requests cancellation after the current file.

ROI table export is optional. The ROI atlas and label table paths are reference files for ROI summaries and classifier validation; uncheck **Export ROI table** when you only need voxel-wise/subject-level ANS/RNS maps.

## CLI path

First confirm that HemiSpec discovers both DGN directions:

```bash
hemispec models
```

Then run the standard bilateral workflow on approved preprocessed gray-matter maps:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_full_demo
```

With optional ROI table, classifier validation, and TRT reliability:

```bash
hemispec workflow \
  --input-glob "derivatives/*_GM_masked.nii.gz" \
  --out-dir outputs/hemispec_full_demo \
  --roi-atlas "$HEMISPEC_GLASSER_ATLAS" \
  --roi-label-table "$HEMISPEC_GLASSER_LABEL_TABLE" \
  --run-classifier \
  --run-trt
```

Classifier/TRT outputs from tiny smoke-test datasets should be treated as connectivity checks, not model-performance evidence.

## Release boundary

The repository model bundles let users run inference without retraining. They do not include raw MRI data, generated outputs, or private manuscript-only analysis tables. Additional public assets should include provenance, checksums, compatible HemiSpec version, preprocessing assumptions, and license/citation notes; see [External asset bundles](../reference/asset-bundle.md).
