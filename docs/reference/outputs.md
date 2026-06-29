# Outputs

HemiSpec outputs should be predictable enough for downstream statistics, machine learning, and manuscript reporting.

## Standard workflow layout

`hemispec workflow` and the GUI write a compact user-facing layout. The default final outputs are four voxel maps per subject plus optional tables and validation reports:

```text
<out-dir>/
  voxel_maps/
    <subject>_ANS.L.nii.gz
    <subject>_ANS.R.nii.gz
    <subject>_RNS.L.nii.gz
    <subject>_RNS.R.nii.gz
  tables/
    subject_metric_summary.csv
    roi_features_bilateral.csv          # when ROI export is enabled and an atlas is available
    roi_features_bilateral_wide.csv     # when ROI export is enabled and an atlas is available
  validation/
    hemi_classify/                      # only when --run-classifier is enabled
    trt/                                # only when --run-trt is enabled
```

DGN reconstructions and one-direction metrics are intermediate implementation details. They are removed by default because the stitched actual/reconstructed recon maps are redundant for most users. To debug or run standalone validation on the merged bilateral maps, use `--keep-intermediate` in CLI or the matching GUI checkbox:

```text
<out-dir>/
  intermediate/
    recon/
      L_to_R/
      R_to_L/
    direction_metrics/
      L_to_R/
      R_to_L/
    combined_maps/
      <subject>_ANS.nii.gz
      <subject>_RNS.nii.gz
```

Lower-level commands keep their own historical contracts. For example, `hemispec compute --save-subject-maps` still writes `subject_maps/<subject>_ANS.nii.gz` and `subject_maps/<subject>_RNS.nii.gz` under its chosen output directory.

## Required metadata roadmap

Each run should eventually record:

- HemiSpec version.
- Model bundle version.
- Input paths or dataset identifiers.
- Main parameters.
- Output paths.
- Warnings and validation failures.

This full manifest contract is planned; it should not be described as complete until implemented.
