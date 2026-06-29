# Model bundles

HemiSpec includes reusable released model parameters under `assets/models/` via Git LFS, and wheel/PyPI installs can download the same files into a per-user cache. Clone with Git LFS enabled for source checkouts; otherwise model files may be downloaded as small pointer files.

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
```

## Bundled DGN checkpoints

```text
assets/models/dgn/
  outputs_bi_stable_L/ckpts/best_netG_L.pth
  outputs_bi_stable_R/ckpts/best_netG_R.pth
```

These are the bilateral generator checkpoints used by `hemispec workflow` and the GUI. Training intermediates, discriminator checkpoints, and reconstruction previews are not shipped.

## Bundled classifier models

```text
assets/models/hemisphere_classifier/
  OUT_noICBM_train_ICBM_external_saved_models/
  OUT_noICBM_train_ICBM_external_saved_models_paired_residual/
```

Each metric folder contains runnable `*.joblib` bundles plus `feature_names.csv`. The default GUI/API classifier mode uses `OUT_noICBM_train_ICBM_external_saved_models`; `paired_residual` can be selected through CLI/API configuration.

## Discovery order

HemiSpec resolves model paths in this order:

1. explicit CLI/API/GUI path when provided;
2. environment variables such as `HEMISPEC_DGN_MODEL_ROOT` and `HEMISPEC_CLASSIFIER_MODEL_DIR`;
3. bundled source-checkout paths under `assets/models/`;
4. the per-user cache (`HEMISPEC_MODEL_CACHE`, or the OS-specific HemiSpec cache).

If the released defaults are missing from a wheel/PyPI install, model-enabled commands download them from GitHub on first use. To prefetch explicitly:

```bash
hemispec models --install --with-classifier
```

## Distribution notes

Model binaries are tracked with Git LFS. Keep raw MRI data, generated outputs, and private manuscript-only artifacts out of the repository. Additional model bundles should include provenance, compatible HemiSpec version, preprocessing assumptions, checksums, license, and citation notes.
