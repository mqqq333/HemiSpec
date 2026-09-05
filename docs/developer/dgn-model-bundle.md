# DGN model bundles

Current HemiSpec `main` deploys trained generator checkpoints for inference. Record the exact source commit with `git rev-parse HEAD`. Model training is reference-only and is not a public workflow requirement.

ANS/RNS and the cross-hemispheric DGN framework originate from Wang et al. (2024); see [Citation](../citation.md).

## Current asset layout

```text
assets/models/dgn/
├── outputs_bi_stable_L/
│   └── ckpts/
│       └── best_netG_L.pth       # R_to_L target-left bundle
└── outputs_bi_stable_R/
    └── ckpts/
        └── best_netG_R.pth       # L_to_R target-right bundle
```

Explicit direction filenames such as `best_netG_R2L.pth` and `best_netG_L2R.pth` are also supported and preferred when both naming styles exist.

The public bundle should contain only approved runtime assets. Subject-level reconstructions or training metrics must not be included.

## Direction mapping

```text
outputs_bi_stable_L = R_to_L = source right -> generated left
outputs_bi_stable_R = L_to_R = source left  -> generated right
```

`discover_local_dgn_bundles()` implements this mapping for the API, CLI, and GUI.

## Runtime contract

For one direction, the inference adapter:

1. loads a preprocessed `*_GM_masked.nii.gz` volume;
2. applies the low-value inference mask;
3. crops the source hemisphere;
4. loads the matching generator checkpoint;
5. predicts the target-hemisphere patch;
6. pastes the prediction into the original whole-volume grid;
7. saves a reconstructed NIfTI with the source affine/header.

The bilateral workflow runs both directions and combines target-side results.

## Checkpoint format

Supported generator checkpoints may contain a direct state dictionary or a wrapper containing `state_dict`. The runtime loader normalizes supported formats before loading the generator architecture.

The expected single-channel patch shape is:

```text
55 × 119 × 87
```

## Crops

```text
anatomical right: z 5:60,   y 15:134, x 15:102
anatomical left:  z 60:115, y 15:134, x 15:102
```

These constants are owned by package runtime code.

## Thresholds

```text
DGN input cleanup: values > 0.05
ANS/RNS valid GM:  values >= 0.15
```

The thresholds serve different stages and must remain separately named and reported.

## Output naming

Direction-specific reconstructed full volumes use:

```text
<subject>_PRED_LR_full.nii.gz
```

The bilateral workflow then writes final hemisphere-specific metric maps under `voxel_maps/`.
