# Compute specificity maps

ANS/RNS are defined in [ANS and RNS metrics](../methods/ans-rns-metrics.md) and originate from Wang et al. (2024).

This tutorial covers ANS/RNS computation after reconstruction.

## Install

Use a current source checkout. Enable Git LFS before cloning so the checkout is also ready for model-enabled workflows:

```bash
git lfs install
git clone https://github.com/mqqq333/HemiSpec.git
cd HemiSpec
git lfs pull
python -m pip install -e "."
git rev-parse HEAD
```

Record the printed commit hash with the analysis. Archived versions remain available on the [GitHub Releases page](https://github.com/mqqq333/HemiSpec/releases), but this tutorial targets current `main`.

For a complete packaged smoke test, run `hemispec quickstart --out-dir hemispec_quickstart_run_001`; it generates toy paired inputs and runs this compute path. Use a new output directory for each run.

## Required paired inputs

Each subject needs an actual target gray-matter map and a reconstructed counterpart in the same shape, affine, and orientation.

## Current command

```bash
hemispec compute \
  --actual-glob "derivatives/*_GM_masked.nii.gz" \
  --predicted-glob "outputs/recon/*_PRED_LR_full.nii.gz" \
  --out-dir outputs/specificity_run_001 \
  --save-subject-maps
```

This writes group-level ANS/RNS maps and, with `--save-subject-maps`, subject-level maps for validation and ROI extraction.

## ROI export

ROI feature export is available through `compute` options. Supply an approved local atlas on the map grid; see [Data and models](../data-and-models.md). Replace the example path with your atlas path:

```bash
hemispec compute \
  --actual-glob "derivatives/*_GM_masked.nii.gz" \
  --predicted-glob "outputs/recon/*_PRED_LR_full.nii.gz" \
  --out-dir outputs/specificity_roi_run_001 \
  --roi-atlas /approved/path/atlas.nii.gz \
  --roi-out-csv outputs/specificity_roi_run_001/roi_features.csv
```

There is not yet a standalone `roi` command.

## Outputs

- Subject-level ANS maps.
- Subject-level RNS maps.
- Optional ROI-level feature tables.
- Group-level voxelwise summaries when enabled.

## Checks before computation

`compute` checks shape and affine agreement among the paired files and excludes non-finite voxels from its valid mask. These checks do not establish canonical MNI alignment, correct hemisphere labeling, or anatomical quality. Before computation, verify voxel size, orientation, full template affine, registration, segmentation, and mask quality as described in [Input and preprocessing](../input-preprocessing.md).
