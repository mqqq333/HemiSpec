# Compute specificity maps

This tutorial covers ANS/RNS computation after reconstruction.

## Required paired inputs

Each subject needs an actual target gray-matter map and a reconstructed counterpart in the same shape, affine, and orientation.

## Current command

```bash
hemispec compute \
  --actual-glob "derivatives/*_GM_masked.nii.gz" \
  --predicted-glob "outputs/recon/*_PRED_LR_full.nii.gz" \
  --out-dir outputs/specificity \
  --save-subject-maps
```

This writes group-level ANS/RNS maps and, with `--save-subject-maps`, subject-level maps for validation and ROI extraction.

## ROI export

ROI feature export is available through `compute` options. The atlas path is a placeholder until the public HemiSpec atlas assets are added or an external atlas installation is documented:

```bash
hemispec compute \
  --actual-glob "derivatives/*_GM_masked.nii.gz" \
  --predicted-glob "outputs/recon/*_PRED_LR_full.nii.gz" \
  --out-dir outputs/specificity \
  --roi-atlas <atlas-path> \
  --roi-out-csv outputs/roi_features.csv
```

There is not yet a standalone `roi` command.

## Outputs

- Subject-level ANS maps.
- Subject-level RNS maps.
- Optional ROI-level feature tables.
- Group-level voxelwise summaries when enabled.

## Checks before computation

HemiSpec should validate shape, affine, finite values, hemisphere labels, and valid masks before writing outputs.