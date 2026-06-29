# TRT and classifier tasks

This note documents runtime tasks without publishing manuscript-specific result
values.

## TRT reliability

`hemispec trt` estimates test-retest reliability from paired ANS/RNS maps. The
command writes similarity matrices, within-subject summaries, summary plots, and
`validation_summary.csv`.

```bash
hemispec trt   --maps-dir "/path/to/workflow/intermediate/combined_maps"   --out-dir "/path/to/workflow/validation/trt"   --kinds ANS,RNS   --hemis L,R
```

Before public release, use only approved/synthetic examples in this document.
Do not publish private cohort sizes, exact p-values, or manuscript-only summary
statistics here.

## Hemisphere-classifier validation

`hemispec hemi-classify` loads saved sklearn/joblib classifier artifacts and
applies them to ROI-level ANS/RNS features. Training is not a product feature.

```bash
hemispec hemi-classify   --maps-dir "/path/to/workflow/voxel_maps"   --roi-csv "/path/to/workflow/tables/roi_features_bilateral.csv"   --classifier-model-dir "/path/to/classifier_bundle"   --out-dir "/path/to/workflow/validation/hemi_classify"
```

Supported runtime modes:

```text
single
paired_residual
```

Publish model performance only through an approved model card or manuscript-safe
release note. The model card should include training/validation provenance,
feature transforms, software versions, checksums, and citation boundaries.
