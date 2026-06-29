# Model bundles

This directory contains the public model bundles needed to run HemiSpec without retraining.
Large binary weights are tracked with Git LFS.

## DGN checkpoints

```text
assets/models/dgn/outputs_bi_stable_L/ckpts/best_netG_L.pth
assets/models/dgn/outputs_bi_stable_R/ckpts/best_netG_R.pth
```

These are the two generator checkpoints used by the bilateral workflow. Training
intermediates, discriminator checkpoints, and reconstruction previews are not shipped.

## Hemisphere classifier bundles

```text
assets/models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models/
assets/models/hemisphere_classifier/OUT_noICBM_train_ICBM_external_saved_models_paired_residual/
```

Each metric folder contains the runnable `*.joblib` classifier bundle and
`feature_names.csv`. Archive copies and training/prediction dumps are intentionally
excluded.
