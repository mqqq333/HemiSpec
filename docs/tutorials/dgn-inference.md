# DGN inference

This tutorial will show how to apply trained HemiSpec DGN model bundles to preprocessed gray-matter maps.

## Inputs

- Preprocessed `*_GM_masked.nii.gz` files.
- A HemiSpec model bundle containing weights, model direction, preprocessing assumptions, and version metadata.

## Outputs

- Reconstructed hemisphere maps.
- Source and target hemisphere records.
- Run manifest with model version, command, parameters, and output paths.

## Current status

Model bundle packaging is still being finalized. Do not publish trained weights until the release policy is decided.