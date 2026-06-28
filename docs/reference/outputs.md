# Outputs

HemiSpec outputs should be predictable enough for downstream statistics, machine learning, and manuscript reporting.

## Current output groups

The current toolkit writes outputs under user-selected directories. A bilateral workflow should produce reconstruction outputs, ANS/RNS maps, ROI tables, classifier summaries, and optional TRT validation summaries.

A recommended public layout is:

```text
outputs/
  recon_L_to_R/            one-direction reconstructed maps
  recon_R_to_L/            one-direction reconstructed maps
  specificity_L_to_R/      one-direction ANS/RNS maps
  specificity_R_to_L/      one-direction ANS/RNS maps
  hemispec_workflow/       bilateral workflow outputs
    subject_maps/          merged bilateral subject-level ANS/RNS maps
    subject_hemi_maps/     hemisphere-split subject-level ANS/RNS maps
  trt_validation/          test-retest reliability outputs
  structural_specificity/   structural specificity validation outputs
```

## Required metadata roadmap

Each run should eventually record:

- HemiSpec version.
- Model bundle version.
- Input paths or dataset identifiers.
- Main parameters.
- Output paths.
- Warnings and validation failures.

This full manifest contract is planned; it should not be described as complete until implemented.
