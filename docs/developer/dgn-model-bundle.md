# DGN Model Bundle Notes

This document records the trained DGN assets that HemiSpec should deploy for
inference. Model training is not part of HemiSpec v1.

## Scope

`train_code/` is reference material only. Use it to understand:

- the `Generator` architecture,
- the PyTorch checkpoint format,
- the corrected hemisphere crop convention,
- how generated hemisphere patches are pasted back for inspection.

Do not expose training as a user-facing feature in v1, and do not require users
to run `train_code/train.py`.

## Current Local Assets

Reference-only training code:

```text
train_code/
  datasets.py
  models.py
  train.py
```

These files are not imported by the public API, CLI, or GUI. They document the
origin of the deployed runtime architecture and crop conventions.

Trained model output folders:

```text
outputs_bi_stable_L/
  ckpts/
    best_netG_L.pth
    netG_L.pth
  metrics.csv

outputs_bi_stable_R/
  ckpts/
    best_netG_R.pth
    netG_R.pth
  metrics.csv
  recon/
```

The inference adapter should load Generator checkpoints, not Discriminator
checkpoints.

## Direction Mapping

Use this owner-confirmed mapping in API, CLI, GUI, and documentation:

```text
outputs_bi_stable_L = R_to_L = right hemisphere -> generated left hemisphere
outputs_bi_stable_R = L_to_R = left hemisphere  -> generated right hemisphere
```

The current copied checkpoint folders use target-side names:

```text
assets/models/dgn/outputs_bi_stable_L/ckpts/best_netG_L.pth
assets/models/dgn/outputs_bi_stable_R/ckpts/best_netG_R.pth
```

Future checkpoint exports may use explicit direction names:

```text
assets/models/dgn/outputs_bi_stable_L/ckpts/best_netG_R2L.pth
assets/models/dgn/outputs_bi_stable_R/ckpts/best_netG_L2R.pth
```

`discover_local_dgn_bundles()` supports both conventions and prefers explicit
direction names when both exist.

## Runtime Contract

The package-owned inference adapter should:

1. Load a full preprocessed `*_GM_masked.nii.gz` NIfTI.
2. Crop the source hemisphere.
3. Run the matching trained `Generator` checkpoint.
4. Paste the generated patch into the target hemisphere location.
5. Save a reconstructed full-volume GM map with the original affine/header.

For a bilateral reconstructed map, run both directions and paste both generated
hemispheres into one output volume.

## Checkpoint Format

Generator checkpoints are PyTorch files with this shape:

```python
{
    "epoch": <int>,
    "state_dict": <Generator state dict>,
}
```

The reference `Generator` expects a single-channel 3D hemisphere patch and
returns a single-channel generated hemisphere patch. The patch shape is:

```text
55 x 119 x 87
```

## Crops

Use the corrected anatomical convention:

```text
anatomical right: z 5:60,   y 15:134, x 15:102
anatomical left:  z 60:115, y 15:134, x 15:102
```

The runtime adapter owns these constants in package code rather than importing
`train_code` directly.

## Thresholds

The reference dataset code masks low-valued voxels before inference with:

```text
img > 0.05
```

ANS/RNS computation later uses:

```text
GM >= 0.15
```

Keep these thresholds separate in parameter names and documentation.

## Output Naming

The final reconstructed output filename convention still needs to be chosen.
Recommended v1 convention:

```text
<subject>_DGN_bilateral_full.nii.gz
```

For compatibility with old scripts, keep support for:

```text
*_PRED_LR_full.nii.gz
```
