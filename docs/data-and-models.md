# Data and models

HemiSpec works with neuroimaging data and trained model weights, so the public repository uses conservative data boundaries.

## Do not commit

- Raw T1-weighted MRI data.
- Subject-level derivatives that are not cleared for public redistribution.
- Large `.nii.gz`, `.pth`, `.pt`, `.ckpt`, `.joblib`, `.pkl`, or `.xlsx` payloads unless they are explicitly approved release artifacts and intentionally tracked.
- Manuscript-only figures or tables before public release approval.
- Private workstation paths, server paths, keys, tokens, or local-only coordination notes.

## Repository policy

The source repository should contain code, documentation, tests, synthetic examples, and manifests. Large runtime payloads should remain external:

```text
assets/
  atlases/              # local-only payloads, ignored by git
  models/               # local-only DGN/classifier bundles, ignored by git
```

The package and default PyInstaller specs do not bundle repository-level `assets/`.

## Expected local asset layout

A model-enabled local checkout or release bundle can use this layout:

```text
HemiSpec-Assets/
  ASSET_MANIFEST.yml
  SHA256SUMS.txt
  LICENSES/
  models/
    dgn/
      <R_to_L-bundle>/ckpts/<checkpoint>.pth
      <L_to_R-bundle>/ckpts/<checkpoint>.pth
    hemisphere_classifier/
      <classifier-bundle-dir>/
  atlases/
    glasser/
      <atlas-nifti>.nii.gz
      <atlas-label-table>.xlsx
```

Supported environment variables:

```text
HEMISPEC_ASSET_ROOT
HEMISPEC_DGN_MODEL_ROOT
HEMISPEC_CLASSIFIER_MODEL_DIR
HEMISPEC_GLASSER_ATLAS
HEMISPEC_GLASSER_LABEL_TABLE
```

The GUI and CLI resolve explicit paths first, then environment variables, then local repository/distribution conventions. See [External asset bundles](reference/asset-bundle.md) for the manifest/checksum/license contract.

## External release channels

Prefer GitHub Releases, Zenodo, OSF, or institutional storage for model weights and compiled-app asset bundles. Every released asset bundle should include:

- version and date,
- source/provenance,
- license and citation requirements,
- expected local path or environment variable,
- checksums,
- preprocessing assumptions,
- compatible `hemispec-toolkit` version.

## Method and model attribution

If a release distributes or documents ANS/RNS-capable models or workflows, keep the method boundary explicit: the original ANS/RNS metrics and cross-hemispheric DGN framework come from Wang et al. 2024, *Patterns*. HemiSpec packages and extends that workflow for the current software and handedness application.
