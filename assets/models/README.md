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

Each metric folder contains the runnable `*_model_bundle.joblib`, the trained
`*_final_pipeline.joblib`, and `feature_names.csv`. Public runtime bundles retain
only the trained pipeline and runtime configuration. Cohort identifiers, sample
counts, evaluation metrics, training reports, and private provenance paths are
intentionally excluded.
