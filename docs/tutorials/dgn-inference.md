# DGN inference

This tutorial shows how to apply released HemiSpec DGN model bundles to preprocessed gray-matter maps.

## Install

For model-enabled PyPI installs, include the model extra and optionally pre-download released checkpoints:

```bash
python -m pip install "hemispec-toolkit[model]"
hemispec models --install
```

For source development, clone with Git LFS and use `python -m pip install -e .[model]`.

## Inputs

- Preprocessed `*_GM_masked.nii.gz` files.
- A HemiSpec model bundle containing weights, model direction, preprocessing assumptions, and version metadata.

## Outputs

- Reconstructed hemisphere maps.
- Source and target hemisphere records.
- Run manifest with model version, command, parameters, and output paths.

## Current status

Released default model bundles are available through Git LFS source checkouts or first-run PyPI cache download. Do not publish additional trained weights until their release policy, provenance, checksums, and license notes are approved.